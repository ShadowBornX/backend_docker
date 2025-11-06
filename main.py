# python_backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat_router
import uvicorn
import os

# Inicializar la aplicación FastAPI
app = FastAPI(
    title="API VRI-UNTELS",
    description=(
        "Backend oficial del Vicerrectorado de Investigación de la "
        "Universidad Nacional Tecnológica de Lima Sur (VRI-UNTELS). "
        "Proporciona servicios de información institucional, apoyo a la "
        "investigación y respuestas inteligentes mediante IA."
    ),
    version="1.0.0",
)

# Configuración de CORS
# En desarrollo puedes usar ["*"], pero en producción especifica los dominios permitidos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Para pruebas locales desde cualquier frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir los routers
app.include_router(chat_router.router, prefix="/api/v1")

@app.get("/")
async def read_root():
    return {
        "message": "Bienvenido a la API del Vicerrectorado de Investigación (VRI-UNTELS)",
        "status": "online",
        "version": "1.0.0",
        "institution": "Universidad Nacional Tecnológica de Lima Sur",
    }

# Ejecutar Uvicorn directamente si se corre con `python main.py`
if __name__ == "__main__":  
    port = int(os.environ.get("PORT", 8001))  # Puerto por defecto: 8001
    uvicorn.run("main:app", host="0.0.0.0", port=port)
