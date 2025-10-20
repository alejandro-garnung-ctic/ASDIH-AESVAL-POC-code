FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY src/ ./src/
COPY config/ ./config/
COPY assets/ ./assets/
COPY start.sh /app/start.sh

# Permisos para el script Linux
RUN chmod +x /app/start.sh

# Exponer puerto
EXPOSE 8502

# Healthcheck (usa el endpoint raíz de Streamlit)
HEALTHCHECK --interval=30s --timeout=30s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8502 || exit 1

# Comando por defecto (usa el script Linux)
CMD ["/app/start.sh"]