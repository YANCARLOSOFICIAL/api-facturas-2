from openai import OpenAI
import json
import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.schemas.invoice import InvoiceResponse, SupplierInfo, InvoiceItem, TaxInfo, InvoiceTotals
import uuid
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class AIExtractor:
    """Clase para extraer información de facturas usando GPT-4o"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    def create_extraction_prompt(self, text: str) -> str:
        """
        Crea el prompt para extraer información de la factura
        """
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
        return prompt
    
    async def extract_invoice_data(self, text: str) -> InvoiceResponse:
        """
        Extrae datos de la factura usando GPT-4o
        """
        try:
            # Crear prompt
            prompt = self.create_extraction_prompt(text)
            
            # Llamada a OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
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
            
            # Obtener contenido de la respuesta
            content = response.choices[0].message.content.strip()
            logger.info(f"Respuesta de OpenAI: {content[:200]}...")
            
            # Limpiar la respuesta (remover texto que no sea JSON)
            json_content = self._extract_json_from_response(content)
            
            # Parsear JSON
            extracted_data = json.loads(json_content)
            
            # Crear ID único para la factura
            invoice_id = str(uuid.uuid4())
            
            # Convertir a objeto InvoiceResponse
            invoice_response = self._convert_to_invoice_response(extracted_data, invoice_id, text)
            
            # Calcular score de confianza
            confidence_score = self._calculate_confidence_score(extracted_data, text)
            invoice_response.confidence_score = confidence_score
            
            logger.info(f"Factura procesada exitosamente: {invoice_id}")
            return invoice_response
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON de OpenAI: {str(e)}")
            logger.error(f"Contenido recibido: {content}")
            raise Exception(f"Error interpretando respuesta de IA: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error en extracción con IA: {str(e)}")
            raise Exception(f"Error procesando factura con IA: {str(e)}")
    
    def _extract_json_from_response(self, content: str) -> str:
        """
        Extrae el JSON válido de la respuesta de OpenAI
        """
        # Buscar JSON entre llaves
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json_match.group()
        
        # Si no se encuentra JSON entre llaves, intentar limpiar
        lines = content.split('\n')
        json_lines = []
        in_json = False
        
        for line in lines:
            if line.strip().startswith('{'):
                in_json = True
            if in_json:
                json_lines.append(line)
            if line.strip().endswith('}') and in_json:
                break
        
        if json_lines:
            return '\n'.join(json_lines)
        
        # Como último recurso, devolver el contenido completo
        return content
    
    def _convert_to_invoice_response(self, data: Dict[str, Any], invoice_id: str, raw_text: str) -> InvoiceResponse:
        """
        Convierte los datos extraídos a InvoiceResponse
        """
        # Convertir supplier
        supplier = None
        if data.get('supplier'):
            supplier = SupplierInfo(**data['supplier'])
        
        # Convertir items
        items = []
        if data.get('items'):
            for item_data in data['items']:
                # Validar y convertir valores numéricos
                item_data = self._validate_numeric_fields(item_data, ['quantity', 'unit_price', 'discount_percentage', 'subtotal'])
                items.append(InvoiceItem(**item_data))
        
        # Convertir taxes
        taxes = None
        if data.get('taxes'):
            tax_data = self._validate_numeric_fields(data['taxes'], [
                'ica_percentage', 'ica_amount', 'fuente_percentage', 'fuente_amount', 
                'iva_percentage', 'iva_amount'
            ])
            taxes = TaxInfo(**tax_data)
        
        # Convertir totals
        totals = None
        if data.get('totals'):
            total_data = self._validate_numeric_fields(data['totals'], [
                'subtotal', 'discount_total', 'tax_total', 'retention_total', 'total'
            ])
            totals = InvoiceTotals(**total_data)
        
        # Crear respuesta
        invoice_response = InvoiceResponse(
            invoice_id=invoice_id,
            document_type=data.get('document_type'),
            series=data.get('series'),
            number=data.get('number'),
            issue_date=data.get('issue_date'),
            due_date=data.get('due_date'),
            supplier=supplier,
            currency=data.get('currency', 'COP'),
            items=items,
            taxes=taxes,
            totals=totals,
            raw_text=raw_text[:1000] if raw_text else None  # Limitar texto crudo
        )
        
        return invoice_response
    
    def _validate_numeric_fields(self, data: Dict[str, Any], numeric_fields: list) -> Dict[str, Any]:
        """
        Valida y convierte campos numéricos
        """
        for field in numeric_fields:
            if field in data and data[field] is not None:
                try:
                    # Convertir a float si es string
                    if isinstance(data[field], str):
                        # Remover comas y espacios
                        cleaned = data[field].replace(',', '').replace(' ', '')
                        data[field] = float(cleaned) if cleaned else 0.0
                    else:
                        data[field] = float(data[field])
                except (ValueError, TypeError):
                    logger.warning(f"No se pudo convertir {field}: {data[field]} a número")
                    data[field] = 0.0
        
        return data
    
    def _calculate_confidence_score(self, data: Dict[str, Any], text: str) -> float:
        """
        Calcula un score de confianza basado en la información extraída
        """
        score = 0.0
        max_score = 10.0
        
        # Verificar campos obligatorios
        if data.get('document_type'):
            score += 1.0
        if data.get('number'):
            score += 1.5
        if data.get('issue_date'):
            score += 1.0
        if data.get('supplier', {}).get('name'):
            score += 1.5
        if data.get('totals', {}).get('total'):
            score += 2.0
        if data.get('items') and len(data['items']) > 0:
            score += 2.0
        if data.get('currency'):
            score += 0.5
        if data.get('taxes'):
            score += 0.5
        
        # Normalizar a 0-1
        confidence = min(score / max_score, 1.0)
        
        logger.info(f"Score de confianza calculado: {confidence:.2f}")
        return round(confidence, 2)
