from fastapi import FastAPI
from contextlib import asynccontextmanager
from pipeline.db import init_db, get_notificaciones
from pipeline.notificacion_pipeline import ejecutar_pipeline
# print("Acá se hará la api para la red social")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Inicializando base de datos...")
    init_db()
    yield
    print("Cerrando aplicación...")

app = FastAPI(
    title="Motor de Notificaciones para Red Social",
    description="Pipeline DataOps para procesar likes, comentarios y seguidores.",
    version="1.0",
    lifespan=lifespan
)

# @app.post("/init-db")
# def inicializar_base_datos():
#     init_db()
#     return {"mensaje": "Base de datos inicializada correctamente"}

@app.get("/")
def home():
    return {"message": "API funcionando.",
            "pipeline": "ingesta -> validación -> transformación -> carga"}

#Añadir example value squema para la documentación de la API
@app.post(
    "/eventos",
    summary="Procesar evento de red social",
    description="Recibe un evento (like, comentario o seguidor) y procesa la notificación correspondiente."
)
def procesar_evento(evento: dict):
    init_db()
    return ejecutar_pipeline(evento)

@app.get(
    "/notificaciones",
    summary="Listar notificaciones",
    description="Devuelve todas las notificaciones procesadas.")
def listar_notificaciones():
    init_db()
    return get_notificaciones()