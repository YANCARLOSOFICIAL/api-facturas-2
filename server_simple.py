#!/usr/bin/env python3
"""
Servidor simple de procesamiento de facturas
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from fastapi import FastAPI, File, UploadFile, HTTPException
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

# Configuración
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

print("🚀 Iniciando servidor de procesamiento de facturas...")

app = FastAPI(title="Sistema de Procesamiento de Facturas con IA")

@app.get("/")
async def root():
    return {
        "message": "🧾 Sistema de Procesamiento de Facturas con IA",
        "status": "funcionando",
        "version": "1.0.0",
        "endpoints": {
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
        # Extraer texto con pdfplumber
        text = ""
        with pdfplumber.open(temp_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        if not text or len(text.strip()) < 20:
            raise HTTPException(status_code=400, detail="No se pudo extraer texto del PDF")
        
        # Procesar con OpenAI (versión simplificada para prueba)
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Usar modelo más económico para pruebas
            messages=[{
                "role": "user", 
                "content": f"Extrae el tipo de documento, número, fecha y proveedor de esta factura en formato JSON: {text[:1000]}..."
            }],
            max_tokens=500,
            temperature=0.1
        )
        
        ai_response = response.choices[0].message.content
        
        return {
            "invoice_id": str(uuid.uuid4()),
            "filename": file.filename,
            "file_size": file.size,
            "text_extracted": len(text),
            "ai_response": ai_response,
            "status": "✅ Procesado exitosamente"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass

if __name__ == "__main__":
    print("🎯 Servidor listo en http://localhost:8000")
    print("📖 Documentación en http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
