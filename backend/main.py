from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import statistics

app = FastAPI(
    title="Laika System API",
    description="API REST para Monitoramento Preditivo de Integridade Estrutural — Algoritmo SAC-DM",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Caminhos dos JSONs ───────────────────────────────────────────────────────

ARQUIVO_LEITURAS = "data/leituras.json"
ARQUIVO_ALERTAS  = "data/alertas.json"
ARQUIVO_HABITATS = "data/habitats.json"

# ─── Modelos ──────────────────────────────────────────────────────────────────

class Leitura(BaseModel):
    zona: str
    density_of_maxima: float
    lyapunov_estimado: float
    regime_classificado: str

# ─── Helpers ─────────────────────────────────────────────────────────────────

def carregar_json(caminho: str):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_json(caminho: str, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def classificar_regime(density: float, lyapunov: float) -> str:
    """
    Lógica simplificada do algoritmo SAC-DM.
    Classifica o regime com base na Density of Maxima e no Expoente de Lyapunov.
    """
    if lyapunov > 0.7 or density > 8.0:
        return "CAOTICO"
    elif lyapunov > 0.4 or density > 5.0:
        return "TRANSICAO"
    else:
        return "ESTOCASTICO"

# ─── Raiz ────────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {
        "sistema": "Laika System API",
        "status": "online",
        "versao": "1.0",
        "endpoints": ["/leituras", "/alertas", "/habitats", "/analise/zona/{zona}"]
    }

# ─── Leituras — CRUD Completo ────────────────────────────────────────────────

@app.get("/leituras", summary="Listar todas as leituras de telemetria")
def listar_leituras():
    return carregar_json(ARQUIVO_LEITURAS)

@app.get("/leituras/{id}", summary="Buscar leitura por ID")
def buscar_leitura(id: int):
    for leitura in carregar_json(ARQUIVO_LEITURAS):
        if leitura["id"] == id:
            return leitura
    raise HTTPException(status_code=404, detail="Leitura não encontrada")

@app.post("/leituras", summary="Registrar nova leitura de sensor")
def criar_leitura(leitura: Leitura):
    dados = carregar_json(ARQUIVO_LEITURAS)
    novo_id = max((item["id"] for item in dados), default=0) + 1
    nova = {"id": novo_id, **leitura.model_dump()}
    dados.append(nova)
    salvar_json(ARQUIVO_LEITURAS, dados)
    return nova

@app.put("/leituras/{id}", summary="Atualizar leitura existente")
def atualizar_leitura(id: int, leitura: Leitura):
    dados = carregar_json(ARQUIVO_LEITURAS)
    for item in dados:
        if item["id"] == id:
            item.update(leitura.model_dump())
            salvar_json(ARQUIVO_LEITURAS, dados)
            return item
    raise HTTPException(status_code=404, detail="Leitura não encontrada")

@app.delete("/leituras/{id}", summary="Remover leitura")
def deletar_leitura(id: int):
    dados = carregar_json(ARQUIVO_LEITURAS)
    for item in dados:
        if item["id"] == id:
            dados.remove(item)
            salvar_json(ARQUIVO_LEITURAS, dados)
            return {"mensagem": f"Leitura #{id} removida com sucesso"}
    raise HTTPException(status_code=404, detail="Leitura não encontrada")

# ─── Endpoint Estrela — Análise SAC-DM por Zona ──────────────────────────────

@app.post("/analise/zona/{zona}", summary="Analisar telemetria de uma zona com algoritmo SAC-DM")
def analisar_zona(zona: str, janela: int = 10):
    """
    Endpoint principal do produto. Recebe o nome de uma zona, busca as últimas
    N leituras (janela), aplica a lógica SAC-DM simplificada e retorna:
    - regime classificado
    - métricas estatísticas (média DM, média Lyapunov, desvio padrão)
    - alerta gerado automaticamente se regime = CAOTICO
    """
    todas = carregar_json(ARQUIVO_LEITURAS)
    leituras_zona = [l for l in todas if l["zona"].upper() == zona.upper()]

    if not leituras_zona:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhuma leitura encontrada para a zona '{zona}'"
        )

    # Pega as últimas N leituras da janela
    janela_leituras = leituras_zona[-janela:]

    densities = [l["density_of_maxima"] for l in janela_leituras]
    lyapunovs = [l["lyapunov_estimado"] for l in janela_leituras]

    media_dm  = round(statistics.mean(densities), 4)
    media_lyp = round(statistics.mean(lyapunovs), 4)
    desvio_dm = round(statistics.stdev(densities), 4) if len(densities) > 1 else 0.0

    regime = classificar_regime(media_dm, media_lyp)

    # Gera alerta automático se regime CAOTICO
    alerta_gerado = None
    if regime == "CAOTICO":
        alertas = carregar_json(ARQUIVO_ALERTAS)
        novo_id_alerta = max((a["id"] for a in alertas), default=0) + 1
        novo_alerta = {
            "id": novo_id_alerta,
            "nivel": "VERMELHO",
            "descricao": f"Regime CAOTICO detectado na zona {zona}. DM média: {media_dm} Hz. Lyapunov: {media_lyp}. Inspeção imediata requerida.",
            "status": "ABERTO"
        }
        alertas.append(novo_alerta)
        salvar_json(ARQUIVO_ALERTAS, alertas)
        alerta_gerado = novo_alerta

    return {
        "zona": zona,
        "leituras_analisadas": len(janela_leituras),
        "metricas": {
            "media_density_of_maxima": media_dm,
            "desvio_padrao_dm": desvio_dm,
            "media_lyapunov": media_lyp
        },
        "regime_classificado": regime,
        "alerta_gerado": alerta_gerado
    }

# ─── Alertas ─────────────────────────────────────────────────────────────────

@app.get("/alertas", summary="Listar todos os alertas")
def listar_alertas():
    return carregar_json(ARQUIVO_ALERTAS)

@app.get("/alertas/{id}", summary="Buscar alerta por ID")
def buscar_alerta(id: int):
    for alerta in carregar_json(ARQUIVO_ALERTAS):
        if alerta["id"] == id:
            return alerta
    raise HTTPException(status_code=404, detail="Alerta não encontrado")

# ─── Habitats ────────────────────────────────────────────────────────────────

@app.get("/habitats", summary="Listar habitats monitorados")
def listar_habitats():
    return carregar_json(ARQUIVO_HABITATS)

@app.get("/habitats/{id}", summary="Buscar habitat por ID")
def buscar_habitat(id: int):
    for habitat in carregar_json(ARQUIVO_HABITATS):
        if habitat["id"] == id:
            return habitat
    raise HTTPException(status_code=404, detail="Habitat não encontrado")