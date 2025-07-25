# Sistema de Procesamiento de Facturas con IA

## Descripción
Sistema basado en IA para procesar facturas en formato PDF y extraer información estructurada usando GPT-4o, FastAPI y Python.

Este sistema permite la extracción de datos estructurados a partir de facturas en formato PDF, desarrollado con FastAPI, Python y OpenAI.

## Características
- Extracción automática de datos de facturas PDF
- API REST con FastAPI
- Procesamiento con GPT-4o
- Interfaz web moderna para subir facturas
- Validación de datos con Pydantic
- Autenticación JWT

## Instalación

### Opción 1: Usando entorno virtual (recomendado)

1. Clonar el repositorio
2. Crear entorno virtual:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno en `.env`:
```
OPENAI_API_KEY=tu_api_key_aqui
```

5. Iniciar el servidor:
```bash
python server_web.py
```

### Opción 2: Sin entorno virtual

1. Clonar el repositorio
2. Instalar dependencias globalmente:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno en `.env`:
```
OPENAI_API_KEY=tu_api_key_aqui
```

4. Iniciar el servidor:
```bash
python server_web.py
```

## Uso

### Interfaz Web
1. Abre el navegador y ve a:
   - [http://localhost:8001](http://localhost:8001) (con entorno virtual)
   - [http://localhost:8002](http://localhost:8002) (sin entorno virtual)

2. Sube tu factura PDF y obtén los datos estructurados.

### API REST
#### Procesar una factura
```bash
curl -X POST "http://localhost:8000/process" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@factura.pdf"
```

#### Respuesta esperada:
```json
{
  "invoice_id": "uuid",
  "document_type": "FACTURA ELECTRONICA",
  "series": "A001",
  "number": "12345",
  "issue_date": "2025-07-24",
  "due_date": "2025-08-24",
  "supplier": {
    "name": "Proveedor S.A.",
    "tax_id": "123456789",
    "address": "Calle 123"
  },
  "currency": "COP",
  "items": [
    {
      "description": "Producto 1",
      "quantity": 1,
      "unit_price": 100000,
      "subtotal": 100000
    }
  ],
  "taxes": {
    "iva": 19.0
  },
  "totals": {
    "subtotal": 100000,
    "taxes_total": 19000,
    "total": 119000
  }
}
```

## Estructura del Proyecto
```
app/
├── api/
│   ├── v1/
│   │   ├── endpoints/
│   │   └── __init__.py
│   └── __init__.py
├── core/
│   ├── config.py
│   └── __init__.py
├── schemas/
│   ├── invoice.py
│   └── __init__.py
├── services/
│   ├── pdf_processor.py
│   ├── ai_extractor.py
│   └── __init__.py
├── main.py
├── server_web.py
└── web_interface.html
```
