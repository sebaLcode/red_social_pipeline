from fastapi import FastAPI
# print("Acá se hará la api para la red social")

app = FastAPI()

@app.get("/")
def home():
    return {"message": "API funcionando."}