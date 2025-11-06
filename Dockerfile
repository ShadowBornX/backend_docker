# Imagen base con Python 3.10 slim
FROM python:3.10-slim

# -----------------------
# 🔧 Configuración básica
# -----------------------
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# -----------------------
# 📦 Dependencias del sistema
# -----------------------
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libglib2.0-0 \
    libgl1 \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# -----------------------
# 🧠 Instalar dependencias de Python
# -----------------------
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# -----------------------
# 📁 Copiar el proyecto
# -----------------------
COPY . .

# -----------------------
# ⚙️ Variables de entorno por defecto
# -----------------------
ENV PORT=8001

# -----------------------
# 🚪 Exponer el puerto
# -----------------------
EXPOSE 8001

# -----------------------
# 🚀 Comando de ejecución
# -----------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
