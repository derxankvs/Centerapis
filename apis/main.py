import os, uuid, json, asyncio
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
from telethon import TelegramClient, events
from contextlib import asynccontextmanager

load_dotenv("config.env")

# 🔐 Variáveis de ambiente
API_ID_V2 = int(os.getenv("API_ID"))
API_HASH_V2 = os.getenv("API_HASH")
SESSION_NAME_V2 = os.getenv("SESSION_NAME_V2")
GROUP_ID_V2 = int(os.getenv("GROUP_ID2"))

# 🤖 Cliente Telegram
client_v2 = TelegramClient(SESSION_NAME_V2, API_ID_V2, API_HASH_V2)

# 📦 Comandos aceitos
comandos_v2 = {
    "cpf": "cpf", "cnpj": "cnpj", "nome": "nome", "email": "email",
    "placa": "placa", "telefone": "telefone", "site": "site", "pix": "pix",
    "cep": "cep", "instagram": "instagram", "mae": "mae", "pai": "pai", "placad": "placa2"
}

# 🕓 Armazenamento de requisições pendentes e respostas
pending_requests_v2 = {}
responses_v2 = {}

# 🌐 Ciclo de vida da aplicação FastAPI
@asynccontextmanager
async def lifespan_v2(app):
    await client_v2.connect()
    if not await client_v2.is_user_authorized():
        await client_v2.start()
    print("✅ [V2] Bot iniciado e conectado.")

    @client_v2.on(events.NewMessage(chats=GROUP_ID_V2))
    async def handler(event):
        if event.out:
            return
        for req_id in list(pending_requests_v2):
            if req_id not in responses_v2:
                responses_v2[req_id] = event.text

    asyncio.create_task(client_v2.run_until_disconnected())
    yield
    await client_v2.disconnect()

# 🚀 App FastAPI
appv2 = FastAPI(title="API V2", lifespan=lifespan_v2)

# 💾 Registro de consultas
def salvar_consulta(tipo: str, dado: str, ip: str):
    registro = {
        f"Dado {tipo}": dado,
        "Horario da consulta": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "IP da consulta": ip
    }
    try:
        with open("consultas_v2.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
    except:
        dados = []
    dados.append(registro)
    with open("consultas_v2.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

# 🔍 Iniciar consulta
@appv2.get("/{tipo}/{dado}")
async def iniciar_consulta_v2(tipo: str, dado: str, request: Request):
    if tipo not in comandos_v2:
        return JSONResponse(content={"erro": "❌ Tipo inválido."}, status_code=400)
    ip = request.client.host
    salvar_consulta(tipo, dado, ip)
    req_id = str(uuid.uuid4())
    pending_requests_v2[req_id] = {"tipo": tipo, "dado": dado}
    await client_v2.send_message(GROUP_ID_V2, f"/{comandos_v2[tipo]} {dado}")
    return {"status": "pendente", "id": req_id}

# 📬 Verificar resposta
@appv2.get("/resultado/{req_id}")
async def verificar_resposta_v2(req_id: str):
    if req_id in responses_v2:
        resposta = responses_v2.pop(req_id)
        filename = f"resultados_v2/resposta_{req_id}.txt"
        os.makedirs("resultados_v2", exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(resposta)
        return FileResponse(filename, filename=os.path.basename(filename), media_type="text/plain")
    return JSONResponse(content={"resposta": None}, status_code=202)