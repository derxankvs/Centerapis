import os
import uuid
import asyncio
from fastapi import FastAPI
from dotenv import load_dotenv
from telethon import TelegramClient, events
from fastapi.responses import JSONResponse

load_dotenv("config.env")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME")
GROUP_ID = int(os.getenv("GROUP_ID"))

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
app = FastAPI()

comandos = {
    "cpf": "cpf1",
    "cnpj": "cnpj",
    "nome": "nome",
    "email": "email",
    "placa": "placa",
    "telefone": "telefone"
}

# Dicionários para armazenar estado
pending_requests = {}  # id: { "tipo": str, "dado": str }
responses = {}         # id: resposta do bot

@app.on_event("startup")
async def start_bot():
    await client.start()
    print("✅ Bot do Telegram iniciado!")

    @client.on(events.NewMessage(chats=GROUP_ID))
    async def handler(event):
        if event.out:
            return  # Ignora mensagens do próprio bot
        for req_id in list(pending_requests):
            if req_id not in responses:
                responses[req_id] = event.text
                print(f"📨 Resposta recebida para ID {req_id}: {event.text}")

    asyncio.create_task(client.run_until_disconnected())

@app.get("/start/{tipo}/{dado}")
async def iniciar_consulta(tipo: str, dado: str):
    if tipo not in comandos:
        return JSONResponse(content={"erro": "❌ Tipo inválido."}, status_code=400)

    req_id = str(uuid.uuid4())
    pending_requests[req_id] = {"tipo": tipo, "dado": dado}

    comando = comandos[tipo]
    await client.send_message(GROUP_ID, f"/{comando} {dado}")
    print(f"📤 Enviada consulta para /{comando} {dado} com ID {req_id}")

    return {"status": "pendente", "id": req_id}

@app.get("/resultado/{req_id}")
async def verificar_resposta(req_id: str):
    if req_id in responses:
        resposta = responses.pop(req_id)
        pending_requests.pop(req_id, None)
        return {"resposta": resposta}
    else:
        return {"resposta": None}
