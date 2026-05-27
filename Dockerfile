# Usar una imagen base oficial de Python
FROM python:3.11-slim

# Evitar que Python genere archivos .pyc y almacene en caché
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear y establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para PostgreSQL y otros
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del proyecto
COPY . /app/

# Exponer el puerto que Django usa (generalmente 8000)
EXPOSE 8000

# Ajusta esta línea en tu Dockerfile:
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "SistemaVisitantes.wsgi:application"]