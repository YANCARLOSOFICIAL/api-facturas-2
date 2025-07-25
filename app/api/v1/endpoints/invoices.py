from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import shutil
from pathlib import Path
import logging
from typing import List
import uuid

from app.core.config import settings
from app.schemas.invoice import InvoiceResponse, ProcessingStatus
from app.services.pdf_processor import PDFProcessor
from app.services.ai_extractor import AIExtractor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Crear directorio de uploads si no existe
Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)

@router.post("/process", response_model=InvoiceResponse)
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
    
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo es demasiado grande. Máximo permitido: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Generar nombre único para el archivo
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    unique_filename = f"{file_id}{file_extension}"
    file_path = Path(settings.UPLOAD_DIR) / unique_filename
    
    try:
        # Guardar archivo temporalmente
        logger.info(f"Guardando archivo: {file.filename}")
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Validar que es un PDF válido
        logger.info("Validando PDF...")
        if not PDFProcessor.validate_pdf(str(file_path)):
            raise HTTPException(
                status_code=400,
                detail="El archivo PDF está corrupto o no es válido"
            )
        
        # Extraer texto del PDF
        logger.info("Extrayendo texto del PDF...")
        pdf_processor = PDFProcessor()
        extracted_text = pdf_processor.extract_text(str(file_path))
        
        if not extracted_text or len(extracted_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="No se pudo extraer texto suficiente del PDF"
            )
        
        logger.info(f"Texto extraído: {len(extracted_text)} caracteres")
        
        # Procesar con IA
        logger.info("Procesando con IA...")
        ai_extractor = AIExtractor()
        invoice_data = await ai_extractor.extract_invoice_data(extracted_text)
        
        # Agregar información adicional
        invoice_data.processing_notes = [
            f"Archivo original: {file.filename}",
            f"Tamaño: {file.size} bytes",
            f"Texto extraído: {len(extracted_text)} caracteres"
        ]
        
        logger.info(f"Factura procesada exitosamente: {invoice_data.invoice_id}")
        return invoice_data
        
    except HTTPException:
        # Re-lanzar HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Error procesando factura: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno procesando la factura: {str(e)}"
        )
    finally:
        # Limpiar archivo temporal
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Archivo temporal eliminado: {file_path}")
        except Exception as e:
            logger.warning(f"No se pudo eliminar archivo temporal: {str(e)}")

@router.post("/process-async", response_model=ProcessingStatus)
async def process_invoice_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Procesa una factura de forma asíncrona (para archivos grandes)
    """
    # Validar archivo
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten archivos PDF"
        )
    
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo es demasiado grande. Máximo permitido: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Generar ID único para el proceso
    process_id = str(uuid.uuid4())
    
    # Guardar archivo y agregar tarea en background
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    unique_filename = f"{file_id}{file_extension}"
    file_path = Path(settings.UPLOAD_DIR) / unique_filename
    
    try:
        # Guardar archivo
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Agregar tarea de procesamiento en background
        background_tasks.add_task(
            process_invoice_background,
            str(file_path),
            process_id,
            file.filename
        )
        
        return ProcessingStatus(
            status="processing",
            message="La factura se está procesando en segundo plano",
            invoice_id=process_id
        )
        
    except Exception as e:
        logger.error(f"Error iniciando procesamiento asíncrono: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error iniciando procesamiento: {str(e)}"
        )

async def process_invoice_background(file_path: str, process_id: str, original_filename: str):
    """
    Función para procesar facturas en background
    """
    try:
        logger.info(f"Iniciando procesamiento en background: {process_id}")
        
        # Validar PDF
        if not PDFProcessor.validate_pdf(file_path):
            logger.error(f"PDF inválido: {file_path}")
            return
        
        # Extraer texto
        pdf_processor = PDFProcessor()
        extracted_text = pdf_processor.extract_text(file_path)
        
        # Procesar con IA
        ai_extractor = AIExtractor()
        invoice_data = await ai_extractor.extract_invoice_data(extracted_text)
        
        # Aquí podrías guardar en base de datos, enviar notificación, etc.
        logger.info(f"Procesamiento completado: {process_id}")
        
    except Exception as e:
        logger.error(f"Error en procesamiento background {process_id}: {str(e)}")
    finally:
        # Limpiar archivo
        try:
            Path(file_path).unlink()
        except Exception as e:
            logger.warning(f"No se pudo eliminar archivo: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Endpoint para verificar el estado del servicio
    """
    return {
        "status": "healthy",
        "service": "invoice-processing",
        "openai_configured": bool(settings.OPENAI_API_KEY)
    }
