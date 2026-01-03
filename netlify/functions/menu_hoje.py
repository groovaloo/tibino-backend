from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/menu-hoje")
def menu():
    return {"prato": "Arroz de tamboril", "preco": "18€"}

handler = Mangum(app)