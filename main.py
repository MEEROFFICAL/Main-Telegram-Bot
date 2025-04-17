import csv
import time
import logging
import telebot
import os
import requests

# Logging setup
logging.basicConfig(level=logging.INFO)

# Bot token & admins
MAINTENANCE_MODE = False
TOKEN = "Your_Bot_Token"  # Replace with your actual bot token
ADMIN_IDS = [8112061255, 5657619953]
bot = telebot.TeleBot(TOKEN)

# Approved users storage
APPROVED_FILE = "approved_users.txt"

def load_approved_users():
    if os.path.exists(APPROVED_FILE):
        with open(APPROVED_FILE, "r") as f:
            return [int(i.strip()) for i in f.readlines()]
    return []

def save_approved_users():
    with open(APPROVED_FILE, "w") as f:
        f.writelines(f"{uid}\n" for uid in approved_users)

approved_users = load_approved_users()

# Load item data
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

# Loading animation
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

# Google Drive ZIP links
ZIP_LINKS = {
    "skin": "https://drive.google.com/uc?export=download&id=1b8Sl8yI_Hf6CUutNsLNC3aIGwLBltG6z",
    "multiskin": "https://drive.google.com/uc?export=download&id=1b8Sl8yI_Hf6CUutNsLNC3aIGwLBltG6z",
    "xsuits": "https://drive.google.com/uc?export=download&id=1P5BVKNYJokG6M8JUMQjXgWJWKTW9AepZ"
}

# Download & Send ZIP
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

# Handle command
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

# Handlers and admin functions should follow here
# Example handler (you can add more)
@bot.message_handler(commands=['skin', 'multiskin', 'xsuits'])
def command_handler(message):
    cmd = message.text.split()[0][1:]  # Extract command name
    handle_command(message, cmd)

# Start bot
if __name__ == "__main__":
    bot.infinity_polling(timeout=20, long_polling_timeout=5)
