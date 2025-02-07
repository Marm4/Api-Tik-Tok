FROM python:3.10-slim

# 1. Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Configurar el entorno
WORKDIR /app
COPY . .

# 3. Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# 4. Especificar el comando de inicio
CMD ["python", "app.py"]