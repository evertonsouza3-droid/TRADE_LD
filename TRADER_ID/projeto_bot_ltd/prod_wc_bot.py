import asyncio
import aiohttp
import os
import logging
from datetime import datetime

# --- CONFIGURAÇÕES DO BOT ---
CONFIG = {
    'API_TOKEN': 'c7de5cf971fa44ecb6cfec22df3f2257',
    'TELEGRAM_TOKEN': '8795405421:AAEOndjMCjCmr7l1Oxb53fQvOoC7UZp1VEk',
    'CHAT_ID': '6283854841',
    'COMPETITION': 'WC', 
    'SEASON': '2022',
    'THRESHOLD': 1.0,
    'POLLING_INTERVAL': 3600
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bot_trading.log'
)

async def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_TOKEN']}/sendMessage"
    payload = {'chat_id': CONFIG['CHAT_ID'], 'text': f"🌍 *COPA DO MUNDO: LTD ALERT* 🌍\n\n{message}", 'parse_mode': 'Markdown'}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                return response.status == 200
    except Exception as e:
        logging.error(f"Erro Telegram: {e}")
        return False

async def main_loop():
    logging.info("Bot de Produção Iniciado.")
    await send_telegram_alert("🤖 *Bot Ativado na VPS:* Monitorando Copa do Mundo.")
    
    while True:
        # Lógica de monitoramento aqui
        logging.info("Checando mercados...")
        await asyncio.sleep(CONFIG['POLLING_INTERVAL'])

if __name__ == '__main__':
    asyncio.run(main_loop())
