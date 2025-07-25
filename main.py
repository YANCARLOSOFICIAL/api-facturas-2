from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from pathlib import Path

from app.api.v1.endpoints import invoices
from app.core.config import settings

# Crear instancia de FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para procesamiento de facturas con IA",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(
    invoices.router,
    prefix=f"{settings.API_V1_STR}/invoices",
    tags=["invoices"]
)

@app.get("/")
async def root():
    return {
        "message": "Invoice Processing API with AI",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
