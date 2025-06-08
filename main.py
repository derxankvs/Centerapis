import os
import asyncio
from fastapi import FastAPI
from dotenv import load_dotenv
from telethon import TelegramClient, events
from fastapi.responses import PlainTextResponse

# Carrega variáveis do .env
load_dotenv("config.env")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME")
GROUP_ID = int(os.getenv("GROUP_ID"))

# Inicia cliente Telegram
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# Inicia FastAPI
app = FastAPI()
response_holder = {}

# Mapeia os comandos válidos
comandos = {
    "cpf": "cpf1",
    "cnpj": "cnpj",
    "nome": "nome",
    "email": "email",
    "placa": "placa",
    "telefone": "telefone"
}

# Ao iniciar a API, inicia o cliente Telegram
@app.on_event("startup")
async def start_bot():
    await client.start()
    print("✅ Telegram conectado!")

    # Captura mensagens enviadas pelo bot de consulta no grupo
    @client.on(events.NewMessage(chats=GROUP_ID))
    async def handler(event):
        sender = await event.get_sender()
        if sender.bot:
            response_holder['last'] = event.text
            print("📩 Resposta recebida do bot!")

    asyncio.create_task(client.run_until_disconnected())

# Função para enviar comando e esperar resposta
async def consultar(tipo: str, dado: str):
    comando = comandos.get(tipo)
    if not comando:
        return "❌ Tipo inválido."

    mensagem = f"/{comando} {dado}"
    await client.send_message(GROUP_ID, mensagem)

    for _ in range(20):
        await asyncio.sleep(0.5)
        if 'last' in response_holder:
            return response_holder.pop('last')
    return "⏱️ Tempo esgotado sem resposta."

# Rota JSON
@app.get("/{tipo}/{dado}")
async def consulta(tipo: str, dado: str):
    if tipo not in comandos:
        return {"erro": "Tipo inválido."}

    resposta = await consultar(tipo, dado)
    return {
        "tipo": tipo,
        "entrada": dado,
        "resposta": resposta
    }

# Rota TXT (modo texto plano)
@app.get("/txt/{tipo}/{dado}", response_class=PlainTextResponse)
async def consulta_txt(tipo: str, dado: str):
    if tipo not in comandos:
        return "❌ Tipo inválido."

    resposta = await consultar(tipo, dado)
    return f"/{comandos.get(tipo)} {dado}\n\n{resposta}"
