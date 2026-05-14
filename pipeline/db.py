import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@db:3306/red_social_db"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

"""
Se crea la función init_db para inicializar la base de datos, creando las tablas necesarias si no existen.
"""
def init_db():
    query = """
    CREATE TABLE IF NOT EXISTS notificaciones(
        id INT AUTO_INCREMENT PRIMARY KEY,
        evento_id VARCHAR(100) NOT NULL UNIQUE,
        usuario_origen VARCHAR(100) NOT NULL,
        usuario_destino VARCHAR(100) NOT NULL,
        tipo_evento VARCHAR(50) NOT NULL,
        mensaje TEXT NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'pendiente',
        latencia_ms FLOAT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );"""
    
    error_query = """
    CREATE TABLE IF NOT EXISTS errores(
        id INT AUTO_INCREMENT PRIMARY KEY,
        evento_id VARCHAR(100) NOT NULL,
        mensaje_error TEXT NOT NULL,
        raw_event JSON,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );"""
    try:
        with engine.begin() as connection:
            connection.execute(text(query))
            connection.execute(text(error_query))
            print("Tablas 'notificaciones' y 'errores' creadas o ya existen.")
    except SQLAlchemyError as e:
        print(f"Error al inicializar la base de datos: {e}")
        
"""
    Función para insertar notificación en la base de datos.
"""
def insert_notification(evento_id, usuario_origen, usuario_destino, tipo_evento, mensaje, latencia_ms):
    query = """
    INSERT INTO notificaciones (
        evento_id, 
        usuario_origen, 
        usuario_destino, 
        tipo_evento, 
        mensaje, 
        latencia_ms
    )
    VALUES (
        :evento_id, 
        :usuario_origen, 
        :usuario_destino, 
        :tipo_evento, 
        :mensaje, 
        :latencia_ms
    );
    """
    try:
        with engine.begin() as connection:
            connection.execute(text(query), {
                "evento_id": evento_id,
                "usuario_origen": usuario_origen,
                "usuario_destino": usuario_destino,
                "tipo_evento": tipo_evento,
                "mensaje": mensaje,
                "latencia_ms": latencia_ms
            })
            print(f"Notificación insertada: {evento_id}")
    except SQLAlchemyError as e:
        print(f"Error al insertar notificación: {e}")
        raise

"""
    Función para insertar error en la base de datos.
"""
def insert_error(evento_id, mensaje_error, raw_event):
    query = """
    INSERT INTO errores (evento_id, mensaje_error, raw_event)
        VALUES (:evento_id, :mensaje_error, :raw_event);
    """
    try:
        with engine.begin() as connection:
            connection.execute(text(query), {
                "evento_id": evento_id,
                "mensaje_error": mensaje_error,
                "raw_event": raw_event
            })
            print(f"Error insertado para evento: {evento_id}")
    except SQLAlchemyError as e:
        print(f"Error al insertar error: {e}")
        
def get_notificaciones():
    query = "SELECT * FROM notificaciones ORDER BY timestamp DESC;"
    try:
        with engine.begin() as connection:
            result = connection.execute(text(query))
            return [dict(row._mapping) for row in result]
    except SQLAlchemyError as e:
        print(f"Error al obtener notificaciones: {e}")
        return []