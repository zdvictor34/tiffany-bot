# Usa Python 3.11 slim como base
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia solo el requirements.txt primero para aprovechar la cache de Docker
COPY requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de los archivos del proyecto al contenedor
COPY . .

# Expone el puerto si usas Flask (opcional, por ejemplo 5000)
EXPOSE 5000

# Comando para iniciar tu bot
CMD ["python", "tifani_bot.py"]

