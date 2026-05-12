import os
from fastapi import FastAPI

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

print("Acá se hará la api para la red social")

@app.get("/config-check")
def check_config():
    return {"db_url_configurada": DATABASE_URL is not None}