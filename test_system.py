#!/usr/bin/env python3
"""
Script de ejemplo para probar el sistema de procesamiento de facturas
"""
import requests
import json
import sys
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def test_health():
    """Prueba el endpoint de health"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_invoice_health():
    """Prueba el health del servicio de facturas"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/invoices/health")
        print(f"✅ Invoice service health: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Invoice service health failed: {e}")
        return False

def process_sample_invoice(pdf_path: str):
    """Procesa una factura PDF de ejemplo"""
    if not Path(pdf_path).exists():
        print(f"❌ Archivo no encontrado: {pdf_path}")
        return False
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
            response = requests.post(
                f"{API_BASE_URL}/api/v1/invoices/process",
                files=files
            )
        
        print(f"📄 Procesando factura: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Factura procesada exitosamente!")
            print(f"   ID: {result.get('invoice_id')}")
            print(f"   Tipo: {result.get('document_type')}")
            print(f"   Número: {result.get('number')}")
            print(f"   Proveedor: {result.get('supplier', {}).get('name')}")
            print(f"   Total: {result.get('totals', {}).get('total')}")
            print(f"   Confianza: {result.get('confidence_score')}")
            
            # Guardar resultado completo
            with open('resultado_factura.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print("   Resultado guardado en: resultado_factura.json")
            
            return True
        else:
            print(f"❌ Error procesando factura: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Probando Sistema de Procesamiento de Facturas con IA")
    print("=" * 60)
    
    # Probar health checks
    if not test_health():
        print("❌ El servidor no está funcionando")
        return
    
    if not test_invoice_health():
        print("❌ El servicio de facturas no está funcionando")
        return
    
    # Solicitar archivo PDF
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = input("🔍 Ingresa la ruta del archivo PDF a procesar: ").strip()
    
    if pdf_path:
        process_sample_invoice(pdf_path)
    else:
        print("ℹ️  No se proporcionó archivo PDF para procesar")
    
    print("\n📚 Para más información:")
    print(f"   - API Docs: {API_BASE_URL}/docs")
    print(f"   - Health: {API_BASE_URL}/health")

if __name__ == "__main__":
    main()
