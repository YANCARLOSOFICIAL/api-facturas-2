from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Invoice Processing API - Simple Test")

@app.get("/")
async def root():
    return {"message": "Sistema de Procesamiento de Facturas con IA funcionando!", "status": "OK"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "Servidor funcionando correctamente"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
