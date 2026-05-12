# 1. Imagen base: Usamos una versión ligera de Python
FROM python:3.11-slim

# 2. Directorio de trabajo: Donde vivirá nuestra app dentro del contenedor
WORKDIR /app

# 3. Copiamos el archivo de dependencias primero (mejor para el caché)
COPY requirements.txt .

# 4. Instalamos las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiamos el resto del código de nuestra app
COPY . .

# 6. Exponemos el puerto que usa FastAPI (por defecto suele ser 8000)
EXPOSE 8000

# 7. El comando para iniciar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]