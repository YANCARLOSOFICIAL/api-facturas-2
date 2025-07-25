import PyPDF2
import pdfplumber
from typing import Optional, Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Clase para procesar archivos PDF y extraer texto"""
    
    @staticmethod
    def extract_text_with_pdfplumber(file_path: str) -> str:
        """
        Extrae texto usando pdfplumber (mejor para tablas y estructura)
        """
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            logger.info(f"Texto extraído exitosamente con pdfplumber: {len(text)} caracteres")
            return text
            
        except Exception as e:
            logger.error(f"Error extrayendo texto con pdfplumber: {str(e)}")
            raise Exception(f"Error procesando PDF con pdfplumber: {str(e)}")
    
    @staticmethod
    def extract_text_with_pypdf2(file_path: str) -> str:
        """
        Extrae texto usando PyPDF2 (fallback)
        """
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as e:
                        logger.warning(f"Error en página {page_num}: {str(e)}")
                        continue
            
            logger.info(f"Texto extraído exitosamente con PyPDF2: {len(text)} caracteres")
            return text
            
        except Exception as e:
            logger.error(f"Error extrayendo texto con PyPDF2: {str(e)}")
            raise Exception(f"Error procesando PDF con PyPDF2: {str(e)}")
    
    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extrae texto del PDF usando múltiples métodos
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        # Intentar primero con pdfplumber
        try:
            text = PDFProcessor.extract_text_with_pdfplumber(file_path)
            if text and len(text.strip()) > 50:  # Verificar que el texto sea significativo
                return text
        except Exception as e:
            logger.warning(f"pdfplumber falló, intentando con PyPDF2: {str(e)}")
        
        # Fallback a PyPDF2
        try:
            text = PDFProcessor.extract_text_with_pypdf2(file_path)
            if text and len(text.strip()) > 10:
                return text
            else:
                raise Exception("No se pudo extraer texto significativo del PDF")
        except Exception as e:
            logger.error(f"Todos los métodos de extracción fallaron: {str(e)}")
            raise Exception(f"No se pudo extraer texto del PDF: {str(e)}")
    
    @staticmethod
    def extract_metadata(file_path: str) -> Dict[str, Any]:
        """
        Extrae metadatos del PDF
        """
        try:
            metadata = {}
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Información básica
                metadata['num_pages'] = len(pdf_reader.pages)
                
                # Metadatos del documento
                if pdf_reader.metadata:
                    for key, value in pdf_reader.metadata.items():
                        if value:
                            metadata[key.replace('/', '')] = str(value)
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Error extrayendo metadatos: {str(e)}")
            return {"num_pages": 0}
    
    @staticmethod
    def validate_pdf(file_path: str) -> bool:
        """
        Valida que el archivo sea un PDF válido
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                # Intentar acceder a la primera página
                if len(pdf_reader.pages) > 0:
                    first_page = pdf_reader.pages[0]
                    return True
                return False
        except Exception as e:
            logger.error(f"PDF inválido: {str(e)}")
            return False
