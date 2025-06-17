import os
import uuid
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from telethon import TelegramClient, events
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager

load_dotenv("config.env")

# 🔁 V1 CONFIG
API_ID_V1 = int(os.getenv("API_ID"))
API_HASH_V1 = os.getenv("API_HASH")
SESSION_NAME_V1 = os.getenv("SESSION_NAME_V1")
GROUP_ID_V1 = int(os.getenv("GROUP_ID"))

client_v1 = TelegramClient(SESSION_NAME_V1, API_ID_V1, API_HASH_V1)

comandos_v1 = {
    "cpf": "cpf1",
    "cnpj": "cnpj",
    "nome": "nome",
    "email": "email",
    "placa": "placa",
    "telefone": "telefone"
}

pending_requests_v1 = {}
responses_v1 = {}

@asynccontextmanager
async def lifespan_v1(app):
    await client_v1.start()
    print("✅ [V1] Bot iniciado.")

    @client_v1.on(events.NewMessage(chats=GROUP_ID_V1))
    async def handler(event):
        if event.out:
            return
        for req_id in list(pending_requests_v1):
            if req_id not in responses_v1:
                responses_v1[req_id] = event.text
                print(f"📨 [V1] Resposta recebida para ID {req_id}: {event.text}")

    asyncio.create_task(client_v1.run_until_disconnected())
    yield

appv1 = FastAPI(lifespan=lifespan_v1)

@appv1.get("/{tipo}/{dado}")
async def iniciar_consulta_v1(tipo: str, dado: str):
    if tipo not in comandos_v1:
        return JSONResponse(content={"erro": "❌ Tipo inválido."}, status_code=400)

    req_id = str(uuid.uuid4())
    pending_requests_v1[req_id] = {"tipo": tipo, "dado": dado}
    comando = comandos_v1[tipo]

    await client_v1.send_message(GROUP_ID_V1, f"/{comando} {dado}")
    print(f"📤 [V1] Enviada consulta para /{comando} {dado} com ID {req_id}")

    return {"status": "pendente", "id": req_id}

@appv1.get("/resultado/{req_id}")
async def verificar_resposta_v1(req_id: str):
    if req_id in responses_v1:
        resposta = responses_v1.pop(req_id)
        pending_requests_v1.pop(req_id, None)
        return {"resposta": resposta}
    else:
        return {"resposta": None}

# 🔁 V2 CONFIG
API_ID_V2 = int(os.getenv("API_ID"))
API_HASH_V2 = os.getenv("API_HASH")
SESSION_NAME_V2 = os.getenv("SESSION_NAME_V2")  # ✅ Correto agora!
GROUP_ID_V2 = int(os.getenv("GROUP_ID2"))

client_v2 = TelegramClient(SESSION_NAME_V2, API_ID_V2, API_HASH_V2)

comandos_v2 = {
    "cpf": "cpf",
    "cnpj": "cnpj",
    "nome": "nome",
    "email": "email",
    "placa": "placa",
    "telefone": "telefone",
    "site": "site",
    "pix": "pix",
    "cep": "cep",
    "instagram": "instagram",
    "mae": "mae",
    "pai": "pai",
    "placad": "placa2"
}

pending_requests_v2 = {}
responses_v2 = {}

@asynccontextmanager
async def lifespan_v2(app):
    await client_v2.start()
    print("✅ [V2] Bot iniciado.")

    @client_v2.on(events.NewMessage(chats=GROUP_ID_V2))
    async def handler(event):
        if event.out:
            return
        for req_id in list(pending_requests_v2):
            if req_id not in responses_v2:
                responses_v2[req_id] = event.text
                print(f"📨 [V2] Resposta recebida para ID {req_id}: {event.text}")

    asyncio.create_task(client_v2.run_until_disconnected())
    yield

appv2 = FastAPI(lifespan=lifespan_v2)

def salvar_consulta(tipo: str, dado: str, ip: str):
    registro = {
        f"Dado {tipo}": dado,
        "Horario da consulta": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "IP da consulta": ip
    }
    try:
        with open("consultas_v2.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        dados = []

    dados.append(registro)
    with open("consultas_v2.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

@appv2.get("/{tipo}/{dado}")
async def iniciar_consulta_v2(tipo: str, dado: str, request: Request):
    if tipo not in comandos_v2:
        return JSONResponse(content={"erro": "❌ Tipo inválido."}, status_code=400)

    ip = request.client.host
    salvar_consulta(tipo, dado, ip)

    req_id = str(uuid.uuid4())
    pending_requests_v2[req_id] = {"tipo": tipo, "dado": dado}
    comando = comandos_v2[tipo]

    await client_v2.send_message(GROUP_ID_V2, f"/{comando} {dado}")
    print(f"📤 [V2] Enviada consulta para /{comando} {dado} com ID {req_id}")

    return {"status": "pendente", "id": req_id}

@appv2.get("/resultado/{req_id}")
async def verificar_resposta_v2(req_id: str):
    if req_id in responses_v2:
        resposta = responses_v2.pop(req_id)
        pending_requests_v2.pop(req_id, None)

        os.makedirs("resultados_v2", exist_ok=True)
        filename = f"resposta_{req_id}.txt"
        filepath = os.path.join("resultados_v2", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(resposta)

        return FileResponse(filepath, filename=filename, media_type="text/plain")
    return JSONResponse(content={"resposta": None}, status_code=202)

# 🎯 API principal
main = FastAPI(title="Center Seven API")
main.mount("/api/v1", appv1)
main.mount("/api/v2", appv2)