import os
import zipfile
import shutil
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
LOG_SOURCE = 'bot_trading.log'
BACKUP_DIR = './backups_logs/'
RETENTION_DAYS = 7

# Telegram Config (Validated credentials)
TELEGRAM_TOKEN = '8795405421:AAEOndjMCjCmr7l1Oxb53fQvOoC7UZp1VEk'
CHAT_ID = '6283854841'

def send_telegram_notification(message):
    """Sends a backup status notification via Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': f"📦 *LTD BOT: BACKUP LOG* 📦\n\n{message}",
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")
        return False

def run_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    # 1. Create filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"log_backup_{timestamp}.zip"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    # 2. Compress current log file
    if os.path.exists(LOG_SOURCE):
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(LOG_SOURCE)
        
        success_msg = f"✅ Backup criado com sucesso!\n📁 Arquivo: `{backup_filename}`\n📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        print(f"[SUCESSO] Backup criado: {backup_path}")
        send_telegram_notification(success_msg)
    else:
        err_msg = f"❌ Erro ao criar backup: Arquivo `{LOG_SOURCE}` não encontrado."
        print(f"[ERRO] {LOG_SOURCE} não encontrado.")
        send_telegram_notification(err_msg)
        return

    # 3. Clean up old backups (Retention Policy)
    now = datetime.now()
    for file in os.listdir(BACKUP_DIR):
        file_path = os.path.join(BACKUP_DIR, file)
        if os.path.isfile(file_path):
            file_age = datetime.fromtimestamp(os.path.getctime(file_path))
            if now - file_age > timedelta(days=RETENTION_DAYS):
                os.remove(file_path)
                print(f"[LIMPEZA] Backup antigo removido: {file}")

if __name__ == '__main__':
    run_backup()
