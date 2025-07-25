#!/usr/bin/env python3
"""
Servidor completo con interfaz web para procesamiento de facturas
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from fastapi import FastAPI, File, UploadFile, HTTPException
    from fastapi.responses import FileResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
    print("✅ FastAPI importado correctamente")
except ImportError as e:
    print(f"❌ Error importando FastAPI: {e}")
    sys.exit(1)

try:
    import pdfplumber
    print("✅ pdfplumber importado correctamente")
except ImportError as e:
    print(f"❌ Error importando pdfplumber: {e}")
    sys.exit(1)

try:
    from openai import OpenAI
    print("✅ OpenAI importado correctamente")
except ImportError as e:
    print(f"❌ Error importando OpenAI: {e}")
    sys.exit(1)

import uvicorn
import uuid
import json
import tempfile
import logging
from pathlib import Path

# Configuración
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

print("🚀 Iniciando servidor de procesamiento de facturas...")

app = FastAPI(title="Sistema de Procesamiento de Facturas con IA")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Página principal con interfaz web"""
    try:
        with open("web_interface.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <h1>🧾 Sistema de Procesamiento de Facturas con IA</h1>
        <p>Interfaz web no encontrada. Usa <a href="/docs">/docs</a> para acceder a la API.</p>
        """

@app.get("/api", response_class=HTMLResponse)
async def api_info():
    return {
        "message": "🧾 Sistema de Procesamiento de Facturas con IA",
        "status": "funcionando",
        "version": "1.0.0",
        "endpoints": {
            "interface": "/",
            "health": "/health",
            "process": "/process",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "openai_configured": bool(OPENAI_API_KEY),
        "dependencies": {
            "fastapi": "✅",
            "pdfplumber": "✅", 
            "openai": "✅"
        }
    }

@app.post("/process")
async def process_invoice(file: UploadFile = File(...)):
    """Procesa una factura PDF y extrae datos con IA"""
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo archivos PDF permitidos")
    
    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name
    
    try:
        print(f"📄 Procesando: {file.filename}")
        
        # Extraer texto con pdfplumber
        text = ""
        with pdfplumber.open(temp_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        if not text or len(text.strip()) < 20:
            raise HTTPException(status_code=400, detail="No se pudo extraer texto del PDF")
        
        print(f"📝 Texto extraído: {len(text)} caracteres")
        
        # Procesar con OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        prompt = f"""
Analiza esta factura colombiana y extrae la información en formato JSON estructurado.

TEXTO DE LA FACTURA:
{text[:2000]}...

Extrae SOLO la información que encuentres y devuélvela en este formato JSON:

{{
    "document_type": "tipo de documento",
    "series": "serie", 
    "number": "número",
    "issue_date": "fecha emisión YYYY-MM-DD",
    "due_date": "fecha vencimiento YYYY-MM-DD",
    "supplier": {{
        "name": "nombre proveedor",
        "tax_id": "NIT",
        "address": "dirección",
        "phone": "teléfono",
        "email": "email"
    }},
    "customer": {{
        "name": "nombre cliente",
        "tax_id": "NIT cliente",
        "address": "dirección cliente"
    }},
    "currency": "moneda",
    "items": [
        {{
            "description": "producto/servicio",
            "quantity": número,
            "unit_price": precio_unitario,
            "subtotal": subtotal
        }}
    ],
    "taxes": {{
        "iva_percentage": porcentaje_iva,
        "iva_amount": valor_iva,
        "retention_amount": retenciones
    }},
    "totals": {{
        "subtotal": subtotal_total,
        "tax_total": impuestos_total, 
        "total": total_final
    }}
}}

Usa null para valores no encontrados. Devuelve SOLO el JSON.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user", 
                "content": prompt
            }],
            max_tokens=1000,
            temperature=0.1
        )
        
        ai_response = response.choices[0].message.content.strip()
        print(f"🤖 Respuesta de IA: {ai_response[:100]}...")
        
        # Intentar extraer JSON de la respuesta
        try:
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                extracted_json = json.loads(json_match.group())
                ai_response = extracted_json
        except:
            pass  # Si no se puede parsear como JSON, devolver texto original
        
        result = {
            "invoice_id": str(uuid.uuid4()),
            "filename": file.filename,
            "file_size": file.size,
            "text_extracted": len(text),
            "extracted_data": ai_response,
            "status": "✅ Procesado exitosamente"
        }
        
        print(f"✅ Procesamiento completado: {file.filename}")
        return result
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass

if __name__ == "__main__":
    print("🎯 Servidor listo en http://localhost:8001")
    print("🌐 Interfaz web en http://localhost:8001")
    print("📖 Documentación en http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)
