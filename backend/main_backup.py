from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json

app = FastAPI(
    title="Laika System API",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ARQUIVO_JSON = "data/leituras.json"
class Leitura(BaseModel):
    zona: str
    density_of_maxima: float
    lyapunov_estimado: float
    regime_classificado: str

def carregar_dados():
    with open(ARQUIVO_JSON, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_dados(dados):
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)

@app.get("/")
def home():
    return {"mensagem": "Laika System Online"}

@app.get("/leituras")
def listar_leituras():
    return carregar_dados()

@app.get("/leituras/{id}")
def buscar_leitura(id: int):

    dados = carregar_dados()

    for leitura in dados:
        if leitura["id"] == id:
            return leitura

    raise HTTPException(
        status_code=404,
        detail="Leitura não encontrada"
    )

@app.post("/leituras")
def criar_leitura(leitura: Leitura):

    dados = carregar_dados()

    novo_id = max([item["id"] for item in dados], default=0) + 1

    nova_leitura = {
        "id": novo_id,
        **leitura.model_dump()
    }

    dados.append(nova_leitura)

    salvar_dados(dados)

    return nova_leitura

@app.put("/leituras/{id}")
def atualizar_leitura(id: int, leitura: Leitura):

    dados = carregar_dados()

    for item in dados:

        if item["id"] == id:

            item["zona"] = leitura.zona
            item["density_of_maxima"] = leitura.density_of_maxima
            item["lyapunov_estimado"] = leitura.lyapunov_estimado
            item["regime_classificado"] = leitura.regime_classificado

            salvar_dados(dados)

            return item

    raise HTTPException(
        status_code=404,
        detail="Leitura não encontrada"
    )

@app.delete("/leituras/{id}")
def deletar_leitura(id: int):

    dados = carregar_dados()

    for item in dados:

        if item["id"] == id:

            dados.remove(item)

            salvar_dados(dados)

            return {
                "mensagem": "Leitura removida com sucesso"
            }

    raise HTTPException(
        status_code=404,
        detail="Leitura não encontrada"
    )