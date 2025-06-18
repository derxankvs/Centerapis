# apis/app.py

import os, uuid, asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from telethon import TelegramClient, events
from contextlib import asynccontextmanager

load_dotenv("config.env")

# 🔐 Carregando variáveis de ambiente
API_ID_V1 = int(os.getenv("API_ID"))
API_HASH_V1 = os.getenv("API_HASH")
SESSION_NAME_V1 = os.getenv("SESSION_NAME_V1")
GROUP_ID_V1 = int(os.getenv("GROUP_ID"))

# 🤖 Cliente Telegram
client_v1 = TelegramClient(SESSION_NAME_V1, API_ID_V1, API_HASH_V1)

# 📦 Comandos aceitos
comandos_v1 = {
    "cpf": "cpf1", "cnpj": "cnpj", "nome": "nome",
    "email": "email", "placa": "placa", "telefone": "telefone"
}

# 🕓 Armazenamento de requisições pendentes e respostas
pending_requests_v1 = {}
responses_v1 = {}

# 🌐 Inicialização com ciclo de vida do FastAPI
@asynccontextmanager
async def lifespan_v1(app):
    await client_v1.connect()  # ←🔧 Conecta o client antes de qualquer evento
    if not await client_v1.is_user_authorized():
        await client_v1.start()  # Faz login automático se necessário
    print("✅ [V1] Bot iniciado e conectado.")

    @client_v1.on(events.NewMessage(chats=GROUP_ID_V1))
    async def handler(event):
        if event.out:
            return
        for req_id in list(pending_requests_v1):
            if req_id not in responses_v1:
                responses_v1[req_id] = event.text

    asyncio.create_task(client_v1.run_until_disconnected())  # ← Mantém rodando
    yield
    await client_v1.disconnect()  # ← Fecha a conexão quando encerrar

# 🚀 App FastAPI
appv1 = FastAPI(title="API V1", lifespan=lifespan_v1)

# 🔍 Iniciar consulta
@appv1.get("/{tipo}/{dado}")
async def iniciar_consulta_v1(tipo: str, dado: str):
    if tipo not in comandos_v1:
        return JSONResponse(content={"erro": "❌ Tipo inválido."}, status_code=400)
    req_id = str(uuid.uuid4())
    pending_requests_v1[req_id] = {"tipo": tipo, "dado": dado}
    await client_v1.send_message(GROUP_ID_V1, f"/{comandos_v1[tipo]} {dado}")
    return {"status": "pendente", "id": req_id}

# 📬 Verificar resposta
@appv1.get("/resultado/{req_id}")
async def verificar_resposta_v1(req_id: str):
    if req_id in responses_v1:
        return {"resposta": responses_v1.pop(req_id)}
    return {"resposta": None}