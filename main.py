import csv
import time
import logging
import telebot
import os
import requests
from flask import Flask, request

# Logging
logging.basicConfig(level=logging.INFO)

# Bot token & Webhook config from environment variables
TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # e.g., https://your-render-url.onrender.com

# Maintenance mode and admin list
MAINTENANCE_MODE = False
ADMIN_IDS = [8112061255, 5657619953]

bot = telebot.TeleBot(TOKEN, threaded=False)
APPROVED_FILE = "approved_users.txt"

# Flask app
app = Flask(__name__)
WEBHOOK_PATH = f"/{TOKEN}/"
FULL_WEBHOOK_URL = f"{WEBHOOK_URL}{WEBHOOK_PATH}"

# Approved users loading/saving
def load_approved_users():
    if os.path.exists(APPROVED_FILE):
        with open(APPROVED_FILE, "r") as f:
            return [int(i.strip()) for i in f.readlines()]
    return []

def save_approved_users():
    with open(APPROVED_FILE, "w") as f:
        f.writelines(f"{uid}\n" for uid in approved_users)

approved_users = load_approved_users()

# Item loading
def load_items():
    items = {}
    try:
        with open("items.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                items[int(row[0])] = row[1]
    except FileNotFoundError:
        logging.warning("❌ items.csv not found.")
    return items

ITEMS = load_items()

# Progress animation
def loading_animation(chat_id):
    progress = [
        "[□□□□□□□□□□] 0%", "[■□□□□□□□□□] 10%", "[■■□□□□□□□□] 20%", "[■■■□□□□□□□] 30%",
        "[■■■■□□□□□□] 40%", "[■■■■■□□□□□] 50%", "[■■■■■■□□□□] 60%", "[■■■■■■■□□□] 70%",
        "[■■■■■■■■□□] 80%", "[■■■■■■■■■□] 90%", "[■■■■■■■■■■] 100%"
    ]
    msg = bot.send_message(chat_id, "⏳ Please wait...")
    for step in progress:
        time.sleep(0.1)
        bot.edit_message_text(step, chat_id, msg.message_id)

# File download & send
ZIP_LINKS = {
    "skin": "https://drive.google.com/uc?export=download&id=1b8Sl8yI_Hf6CUutNsLNC3aIGwLBltG6z",
    "multiskin": "https://drive.google.com/uc?export=download&id=1b8Sl8yI_Hf6CUutNsLNC3aIGwLBltG6z",
    "xsuits": "https://drive.google.com/uc?export=download&id=1P5BVKNYJokG6M8JUMQjXgWJWKTW9AepZ"
}

def download_and_send_zip(command, chat_id):
    url = ZIP_LINKS.get(command)
    if not url:
        bot.send_message(chat_id, "❌ No file linked to this command!")
        return
    try:
        filename = f"{command}.zip"
        response = requests.get(url)
        with open(filename, "wb") as f:
            f.write(response.content)
        with open(filename, "rb") as f:
            bot.send_document(chat_id, f)
        os.remove(filename)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error sending file: {e}")

# Main command handler
def handle_command(message, cmd):
    uid = message.chat.id
    global MAINTENANCE_MODE

    if MAINTENANCE_MODE:
        bot.reply_to(message, "🛠 Maintenance Mode Enabled.")
        return

    args = message.text.split()[1:]
    if uid not in approved_users:
        bot.reply_to(message, "⏳ Waiting for approval!")
        return

    if len(args) < 2:
        bot.reply_to(message, f"❌ Use: /{cmd} <id1> <id2> ...")
        return

    item_ids = [int(arg) for arg in args if arg.isdigit()]
    invalid_ids = [sid for sid in item_ids if sid not in ITEMS]
    if invalid_ids:
        bot.reply_to(message, "⚠ Invalid ID(s)! Please check and try again.")
        return

    result = f"{cmd.upper()} LOOKUP RESULTS 🔍\n\n"
    for sid in item_ids:
        result += f"• ID {sid}: {ITEMS[sid]}\n"
    result += "\n_Processing your request..._"

    bot.send_message(uid, result, parse_mode="Markdown")
    loading_animation(uid)
    download_and_send_zip(cmd, uid)
    bot.send_message(uid, "✅ Your mixed skin has been created! Enjoy!\n\n¹ HYPERSKINS BOT")

# Command handlers
@bot.message_handler(commands=['skin', 'multiskin', 'xsuits'])
def command_handler(message):
    cmd = message.text.split()[0][1:]
    handle_command(message, cmd)

@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(message.chat.id, "👋 Welcome! Use /skin <id1> <id2> to begin!")

# Flask route for webhook
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.data.decode("utf-8"))
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid request', 403

# Set webhook before first request
@app.before_first_request
def setup_webhook():
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=FULL_WEBHOOK_URL)

# Start Flask app with correct port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
