from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

class SupplierInfo(BaseModel):
    name: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class InvoiceItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    discount_percentage: float = 0.0
    subtotal: float
    tax_amount: Optional[float] = None

class TaxInfo(BaseModel):
    ica_percentage: Optional[float] = None
    ica_amount: Optional[float] = None
    fuente_percentage: Optional[float] = None
    fuente_amount: Optional[float] = None
    iva_percentage: Optional[float] = None
    iva_amount: Optional[float] = None

class InvoiceTotals(BaseModel):
    subtotal: float
    discount_total: float = 0.0
    tax_total: float = 0.0
    retention_total: float = 0.0
    total: float

class InvoiceResponse(BaseModel):
    invoice_id: str
    document_type: Optional[str] = None
    series: Optional[str] = None
    number: Optional[str] = None
    issue_date: Optional[str] = None
    due_date: Optional[str] = None
    supplier: Optional[SupplierInfo] = None
    currency: Optional[str] = "COP"
    items: List[InvoiceItem] = []
    taxes: Optional[TaxInfo] = None
    totals: Optional[InvoiceTotals] = None
    raw_text: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_notes: Optional[List[str]] = None

class ProcessingStatus(BaseModel):
    status: str  # "processing", "completed", "failed"
    message: str
    invoice_id: Optional[str] = None
    error_details: Optional[str] = None

class InvoiceCreate(BaseModel):
    filename: str
    file_size: int
    content_type: str
