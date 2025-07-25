#!/usr/bin/env python3
"""
Script para probar el procesamiento de factura con el sistema de IA
"""
import requests
import json
from pathlib import Path

# Configuración
API_URL = "http://localhost:8000/process"
PDF_PATH = r"c:\Users\pinnc\Downloads\1-20250724150851.pdf"

def test_invoice_processing():
    """Prueba el procesamiento de la factura"""
    
    print("🧾 Probando Sistema de Procesamiento de Facturas con IA")
    print("=" * 60)
    
    # Verificar que el archivo existe
    pdf_file = Path(PDF_PATH)
    if not pdf_file.exists():
        print(f"❌ Error: No se encontró el archivo {PDF_PATH}")
        return
    
    print(f"📄 Archivo encontrado: {pdf_file.name}")
    print(f"📊 Tamaño: {pdf_file.stat().st_size / 1024:.1f} KB")
    print()
    
    try:
        # Enviar factura al API
        print("🚀 Enviando factura al servidor...")
        with open(pdf_file, 'rb') as f:
            files = {'file': (pdf_file.name, f, 'application/pdf')}
            response = requests.post(API_URL, files=files, timeout=60)
        
        print(f"📡 Respuesta del servidor: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ ¡Factura procesada exitosamente!")
            print()
            print("📋 RESULTADOS:")
            print("-" * 40)
            print(f"🆔 ID de factura: {result.get('invoice_id', 'N/A')}")
            print(f"📁 Archivo: {result.get('filename', 'N/A')}")
            print(f"📏 Tamaño: {result.get('file_size', 0)} bytes")
            print(f"📝 Texto extraído: {result.get('text_extracted', 0)} caracteres")
            print()
            print("🤖 RESPUESTA DE LA IA:")
            print("-" * 40)
            ai_response = result.get('ai_response', '')
            print(ai_response)
            print()
            
            # Guardar resultado completo
            output_file = "resultado_factura.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Resultado completo guardado en: {output_file}")
            
        else:
            print(f"❌ Error del servidor: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"📄 Detalle: {error_detail.get('detail', 'Error desconocido')}")
            except:
                print(f"📄 Respuesta: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al servidor")
        print("💡 Asegúrate de que el servidor esté ejecutándose en http://localhost:8000")
    except requests.exceptions.Timeout:
        print("❌ Error: Timeout - El procesamiento tomó demasiado tiempo")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")

if __name__ == "__main__":
    test_invoice_processing()
