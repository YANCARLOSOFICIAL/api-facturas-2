from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import uuid
import json
import tempfile
from pathlib import Path
import pdfplumber
from openai import OpenAI
import logging

# Configuración
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear instancia de FastAPI
app = FastAPI(
    title="Sistema de Procesamiento de Facturas con IA",
    description="API para extraer información de facturas PDF usando GPT-4o",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def extract_text_from_pdf(file_path: str) -> str:
    """Extrae texto de un archivo PDF usando pdfplumber"""
    text = ""
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        if text and len(text.strip()) > 10:
            return text
        else:
            raise Exception("No se pudo extraer texto significativo del PDF")
            
    except Exception as e:
        logger.error(f"Error extrayendo texto: {e}")
        raise Exception(f"No se pudo extraer texto del PDF: {e}")

def extract_invoice_data_with_ai(text: str) -> dict:
    """Extrae datos de factura usando GPT-4o"""
    prompt = f"""
Analiza el siguiente texto de una factura y extrae la información en formato JSON. 
El texto puede estar en español y contener información de facturas electrónicas colombianas.

TEXTO DE LA FACTURA:
{text}

Extrae la siguiente información y devuélvela en formato JSON válido:

{{
    "document_type": "tipo de documento (ej: FACTURA ELECTRONICA, NOTA DEBITO, etc.)",
    "series": "serie de la factura",
    "number": "número de la factura",
    "issue_date": "fecha de emisión en formato YYYY-MM-DD",
    "due_date": "fecha de vencimiento en formato YYYY-MM-DD",
    "supplier": {{
        "name": "nombre del proveedor/emisor",
        "tax_id": "NIT o identificación tributaria",
        "address": "dirección",
        "phone": "teléfono",
        "email": "email"
    }},
    "currency": "moneda (COP, USD, etc.)",
    "items": [
        {{
            "description": "descripción del producto/servicio",
            "quantity": cantidad_numérica,
            "unit_price": precio_unitario_numérico,
            "discount_percentage": porcentaje_descuento_numérico,
            "subtotal": subtotal_numérico
        }}
    ],
    "taxes": {{
        "ica_percentage": porcentaje_ica_numérico,
        "ica_amount": valor_ica_numérico,
        "fuente_percentage": porcentaje_retefuente_numérico,
        "fuente_amount": valor_retefuente_numérico,
        "iva_percentage": porcentaje_iva_numérico,
        "iva_amount": valor_iva_numérico
    }},
    "totals": {{
        "subtotal": subtotal_total_numérico,
        "discount_total": descuentos_total_numérico,
        "tax_total": impuestos_total_numérico,
        "retention_total": retenciones_total_numérico,
        "total": total_final_numérico
    }}
}}

INSTRUCCIONES IMPORTANTES:
1. Devuelve SOLO el JSON válido, sin texto adicional
2. Usa null para valores no encontrados
3. Convierte todos los valores monetarios a números (sin símbolos ni comas)
4. Las fechas deben estar en formato YYYY-MM-DD
5. Si no encuentras un campo, usa null en lugar de texto vacío
6. Para arrays vacíos, usa []
7. Para porcentajes, usa el valor numérico (ej: 19.0 para 19%)

JSON:
"""
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto en procesamiento de facturas electrónicas colombianas. Extrae información de manera precisa y devuelve solo JSON válido."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content.strip()
        logger.info(f"Respuesta de OpenAI: {content[:200]}...")
        
        # Limpiar y parsear JSON
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_content = json_match.group()
        else:
            json_content = content
        
        extracted_data = json.loads(json_content)
        return extracted_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON: {e}")
        raise Exception(f"Error interpretando respuesta de IA: {e}")
    except Exception as e:
        logger.error(f"Error en extracción con IA: {e}")
        raise Exception(f"Error procesando factura con IA: {e}")

@app.get("/")
async def root():
    return {
        "message": "Sistema de Procesamiento de Facturas con IA",
        "version": "1.0.0",
        "docs": "/docs",
        "openai_configured": bool(OPENAI_API_KEY)
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "invoice-processing",
        "openai_configured": bool(OPENAI_API_KEY)
    }

@app.post("/api/v1/invoices/process")
async def process_invoice(file: UploadFile = File(...)):
    """
    Procesa una factura en formato PDF y extrae la información usando IA
    """
    # Validar archivo
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten archivos PDF"
        )
    
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo es demasiado grande. Máximo permitido: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        logger.info(f"Procesando archivo: {file.filename}")
        
        # Extraer texto del PDF
        logger.info("Extrayendo texto del PDF...")
        extracted_text = extract_text_from_pdf(temp_file_path)
        
        if not extracted_text or len(extracted_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="No se pudo extraer texto suficiente del PDF"
            )
        
        logger.info(f"Texto extraído: {len(extracted_text)} caracteres")
        
        # Procesar con IA
        logger.info("Procesando con IA...")
        invoice_data = extract_invoice_data_with_ai(extracted_text)
        
        # Crear respuesta
        response = {
            "invoice_id": str(uuid.uuid4()),
            "filename": file.filename,
            "file_size": file.size,
            "text_length": len(extracted_text),
            **invoice_data,
            "processing_notes": [
                f"Archivo procesado: {file.filename}",
                f"Tamaño: {file.size} bytes",
                f"Texto extraído: {len(extracted_text)} caracteres"
            ]
        }
        
        logger.info(f"Factura procesada exitosamente")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando factura: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno procesando la factura: {str(e)}"
        )
    finally:
        # Limpiar archivo temporal
        try:
            os.unlink(temp_file_path)
        except Exception as e:
            logger.warning(f"No se pudo eliminar archivo temporal: {e}")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
