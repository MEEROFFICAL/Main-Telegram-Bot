import csv
import time
import logging
import telebot
import os

# Logging setup
logging.basicConfig(level=logging.INFO)

# Bot token & admins
MAINTENANCE_MODE = False  # Global maintenance mode flag
TOKEN = "7501669029:AAEYIc7z5TPn49i3JiMA654WWU2ICIpgoSU"  # Replace with your bot token
ADMIN_IDS = [8112061255, 5657619953]    # Admin Telegram IDs
bot = telebot.TeleBot(TOKEN)

# Persistent approved user storage
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
        "[□□□□□□□□□□] 0%", "[■□□□□□□□□□] 10%", "[■■□□□□□□□□] 20%",
        "[■■■□□□□□□□] 30%", "[■■■■□□□□□□] 40%", "[■■■■■□□□□□] 50%",
        "[■■■■■■□□□□] 60%", "[■■■■■■■□□□] 70%", "[■■■■■■■■□□] 80%",
        "[■■■■■■■■■□] 90%", "[■■■■■■■■■■] 100%"
    ]
    msg = bot.send_message(chat_id, "⏳ Please wait...")
    for step in progress:
        time.sleep(0.1)
        bot.edit_message_text(step, chat_id, msg.message_id)

# Create inline buttons for admin
def get_admin_buttons(user_id):
    markup = telebot.types.InlineKeyboardMarkup()
    approve_btn = telebot.types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}")
    disapprove_btn = telebot.types.InlineKeyboardButton("❌ Disapprove", callback_data=f"disapprove_{user_id}")
    markup.add(approve_btn, disapprove_btn)
    return markup

def get_admin_menu(chat_id):
    global MAINTENANCE_MODE
    admin_msg = (
        "👑 *Admin Control Panel*\n\n"
        "Welcome back, Administrator!\n\n"
        "🔧 *System Status:*\n"
        f"Maintenance Mode: {'ON 🔴' if MAINTENANCE_MODE else 'OFF 🟢'}\n"
        f"Active Users: {len(approved_users)}\n\n"
        "Select an option below:"
    )
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    maintenance_on = telebot.types.InlineKeyboardButton("🔧 Maintenance ON", callback_data="maintenance_on")
    maintenance_off = telebot.types.InlineKeyboardButton("✅ Maintenance OFF", callback_data="maintenance_off")
    view_users = telebot.types.InlineKeyboardButton("👥 View Users", callback_data="view_users")
    broadcast = telebot.types.InlineKeyboardButton("📢 Broadcast", callback_data="broadcast_msg")
    block_user = telebot.types.InlineKeyboardButton("🚫 Block User", callback_data="block_user")
    refresh = telebot.types.InlineKeyboardButton("🔄 Refresh Menu", callback_data="refresh_menu")
    markup.add(maintenance_on, maintenance_off)
    markup.add(view_users, broadcast)
    markup.add(block_user, refresh)
    try:
        bot.send_message(chat_id, admin_msg, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        logging.error(f"Failed to send admin menu: {str(e)}")
        bot.send_message(chat_id, "❌ Error displaying admin menu. Please try again.")

# Handle button callbacks
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        global MAINTENANCE_MODE
        logging.info(f"Callback received: {call.data} from user {call.from_user.id}")

        # Verify admin
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "⚠️ Only admin can use these buttons!", show_alert=True)
            return

        # Handle maintenance mode
        if call.data == "maintenance_on":
            MAINTENANCE_MODE = True
            bot.answer_callback_query(call.id, "✅ Maintenance mode enabled")
            get_admin_menu(call.message.chat.id)
            return

        if call.data == "maintenance_off":
            MAINTENANCE_MODE = False
            bot.answer_callback_query(call.id, "✅ Maintenance mode disabled")
            get_admin_menu(call.message.chat.id)
            return

        if call.data == "view_users":
            users_list = "👥 *Current Users:*\n\n"
            for uid in approved_users:
                users_list += f"• `{uid}`\n"
            bot.edit_message_text(chat_id=call.message.chat.id,
                                   message_id=call.message.message_id,
                                   text=users_list,
                                   parse_mode="Markdown")
            return

        if call.data == "broadcast_msg":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(call.message.chat.id,
                                    "📢 *Send your broadcast message:*\n_Reply to this message_",
                                    parse_mode="Markdown")
            bot.register_next_step_handler(msg, handle_broadcast)
            return

        if call.data == "block_user":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(call.message.chat.id,
                                    "🚫 *Enter user ID to block:*",
                                    parse_mode="Markdown")
            bot.register_next_step_handler(msg, handle_block_user)
            return

        if call.data == "refresh_menu":
            bot.answer_callback_query(call.id, "🔄 Refreshing menu...")
            get_admin_menu(call.message.chat.id)
            return

        # Show processing message for other actions
        bot.answer_callback_query(call.id, "⚙️ Processing your request...")

        # Parse callback data for approve/disapprove
        if "_" in call.data:
            action, user_id = call.data.split('_')
            user_id = int(user_id)
            logging.info(f"Processing {action} for user {user_id}")

            if action == "approve":
                if user_id not in approved_users:
                    approved_users.append(user_id)
                    save_approved_users()
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=f"✅ User {user_id} has been approved!",
                        parse_mode="Markdown"
                    )
                    bot.send_message(
                        user_id,
                        "🎉 *Welcome to HYPER SKINS BOT!*\n\n"
                        "✅ You have been approved!\n\n"
                        "📱 *Available Commands:*\n"
                        "• `/skin <real_id> <mod_id>`\n"
                        "• `/multiskin <real> <mod> <real> <mod>`\n"
                        "• `/xsuits <real_id> <mod_id>`\n\n"
                        "Start mixing skins now! 🔥",
                        parse_mode="Markdown"
                    )
                    bot.answer_callback_query(call.id, "✅ User approved successfully!")
                else:
                    bot.answer_callback_query(call.id, "User already approved!")

            elif action == "disapprove":
                if user_id in approved_users:
                    approved_users.remove(user_id)
                    save_approved_users()
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=f"❌ User {user_id} has been disapproved!",
                        parse_mode="Markdown"
                    )
                    bot.send_message(
                        user_id,
                        "⚠️ Your access has been revoked by admin.",
                        parse_mode="Markdown"
                    )
                    bot.answer_callback_query(call.id, "❌ User disapproved successfully!")
                else:
                    bot.answer_callback_query(call.id, "User was not in approved list!")

    except Exception as e:
        logging.error(f"Callback error: {str(e)}")
        try:
            bot.answer_callback_query(call.id, "❌ An error occurred", show_alert=True)
        except Exception as edit_error:
            logging.error(f"Failed to update markup: {str(edit_error)}")

def handle_broadcast(message):
    text = message.text
    sent = 0
    for uid in approved_users:
        try:
            bot.send_message(uid, f"📢 Announcement:\n{text}", parse_mode="Markdown")
            sent += 1
        except:
            continue
    bot.reply_to(message, f"✅ Message sent to {sent} users.")

def handle_block_user(message):
    try:
        user_id = int(message.text)
        if user_id in approved_users:
            approved_users.remove(user_id)
            save_approved_users()
            bot.reply_to(message, f"🚫 User {user_id} has been blocked.")
        else:
            bot.reply_to(message, f"⚠️ User {user_id} is not in the approved list.")
    except ValueError:
        bot.reply_to(message, "❌ Invalid user ID. Please enter a valid integer.")

@bot.message_handler(commands=["start"])
def start(message):
    uid = message.chat.id
    user_name = message.from_user.first_name

    if uid in approved_users and uid not in ADMIN_IDS:
        approved_users.remove(uid)
        save_approved_users()
        logging.info(f"User {uid} removed from approved users due to bot restart")

    if uid in ADMIN_IDS and uid not in approved_users:
        approved_users.append(uid)
        save_approved_users() 

    if uid in ADMIN_IDS:
        get_admin_menu(uid)

    if uid not in approved_users and uid not in ADMIN_IDS:
        admin_msg = (f"🆕 *New User Request*\n\n"
                    f"👤 Name: {user_name}\n"
                    f"🆔 User ID: `{uid}`")
        for admin_id in ADMIN_IDS:
            try:
                markup = get_admin_buttons(uid)
                bot.send_message(admin_id, admin_msg, parse_mode="Markdown", reply_markup=markup)
            except Exception as e:
                logging.error(f"Failed to notify admin {admin_id} about user {uid}: {str(e)}")

    if uid in approved_users:
        bot.reply_to(message, 
            f"*Welcome Back, {user_name}* 🌟\n\n"
            "Your access has been confirmed ✓\n\n"
            "📱 *Available Commands:*\n"
            "• `/skin <real_id> <mod_id>` - Create custom skin\n"
            "• `/multiskin <real> <mod> <real> <mod>` - Mix multiple skins\n"
            "• `/xsuits <real_id> <mod_id>` - Customize X-Suits\n\n"
            "💫 _HYPER SKINS BOT - Elevate Your Gaming Experience_",
            parse_mode="Markdown"
        )
    else:
        bot.reply_to(message,
            "*Welcome to HYPER SKINS BOT* 🎯\n\n"
            "📝 Your access request is being processed.\n"
            "⏳ Our team will review your request shortly.\n"
            "✨ You'll receive a confirmation message upon approval.\n\n"
            "_Thank you for choosing HYPER SKINS BOT_",
            parse_mode="Markdown")
        logging.info(f"Request by {uid}")

def is_admin_command(command):
    admin_commands = ['approve', 'disapprove', 'broadcast', 'users']
    return command.lower().strip('/') in admin_commands

@bot.message_handler(commands=["approve"])
def approve(message):
    if not message.chat.id in ADMIN_IDS:
        bot.reply_to(message, "⚠️ You cannot use admin commands!")
        return
    try:
        new_id = int(message.text.split()[1])
        if new_id not in approved_users:
            approved_users.append(new_id)
            save_approved_users()
            approval_msg = f"✅ *User {new_id} has been approved successfully!*"
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(admin_id, approval_msg, parse_mode="Markdown")
                except Exception as e:
                    logging.error(f"Failed to notify admin {admin_id}: {str(e)}")
            welcome_msg = (
                "*Welcome to HYPER SKINS BOT* ⚡\n\n"
                "✓ *Access Granted Successfully*\n\n"
                "📱 *Command Suite:*\n"
                "• `/skin <real_id> <mod_id>` - Create Custom Skin\n"
                "• `/multiskin <real> <mod> <real> <mod>` - Multiple Skin Fusion\n"
                "• `/xsuits <real_id> <mod_id>` - X-Suit Customization\n\n"
                "💡 *Pro Tips:*\n"
                "• Verify skin IDs before processing\n"
                "• Allow animation to complete\n"
                "• Download and apply your custom skins\n\n"
                "_HYPER SKINS BOT - Where Creativity Meets Gaming_"
            )
            bot.send_message(new_id, welcome_msg, parse_mode="Markdown")
        else:
            bot.reply_to(message, "ℹ️ *This user is already approved*", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ *Usage:* `/approve <user_id>`", parse_mode="Markdown")

@bot.message_handler(commands=["disapprove"])
def disapprove(message):
    if not message.chat.id in ADMIN_IDS:
        bot.reply_to(message, "⚠️ You cannot use admin commands!")
        return
    try:
        remove_id = int(message.text.split()[1])
        if remove_id in approved_users:
            approved_users.remove(remove_id)
            save_approved_users()
            disapproval_msg = f"❌ *User {remove_id} has been disapproved*"
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(admin_id, disapproval_msg, parse_mode="Markdown")
                except Exception as e:
                    logging.error(f"Failed to notify admin {admin_id}: {str(e)}")
            revoke_msg = (
                "⚠️ *Access Revoked*\n\n"
                "Your access to HYPER SKINS BOT has been revoked by the administrator.\n"
                "If you believe this is a mistake, please contact support.\n\n"
                "Thank you for using our service!"
            )
            bot.send_message(remove_id, revoke_msg, parse_mode="Markdown")
        else:
            bot.reply_to(message, "ℹ️ *This user is not in the approved list*", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ *Usage:* `/disapprove <user_id>`", parse_mode="Markdown")

@bot.message_handler(commands=["users"])
def list_users(message):
    if not message.chat.id in ADMIN_IDS:
        bot.reply_to(message, "⚠️ You cannot use admin commands!")
        return
    users_list = "👥 *Users List:*\n\n"
    for user_id in approved_users:
        status = "✅ Approved" if user_id in approved_users else "⏳ Pending"
        users_list += f"🆔 `{user_id}` - {status}\n"
        markup = get_admin_buttons(user_id)
        bot.send_message(ADMIN_IDS[0], f"User ID: `{user_id}`\nStatus: {status}", 
                        parse_mode="Markdown", 
                        reply_markup=markup)
    bot.reply_to(message, "✅ Users list has been generated above")

@bot.message_handler(commands=["broadcast"])
def broadcast(message):
    if not message.chat.id in ADMIN_IDS:
        bot.reply_to(message, "⚠️ You cannot use admin commands!")
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        bot.reply_to(message, "❌ Use: /broadcast <message>")
        return
    sent = 0
    for uid in approved_users:
        try:
            bot.send_message(uid, f"📢 Announcement:\n{text}", parse_mode="Markdown")
            sent += 1
        except:
            continue
    bot.reply_to(message, f"✅ Message sent to {sent} users.")

def is_valid_command(message):
    cmd = message.text.split()[0].lower()
    valid_commands = ['/skin', '/multiskin', '/xsuits']
    return cmd in valid_commands

def handle_command(message, cmd):
    uid = message.chat.id
    global MAINTENANCE_MODE

    if MAINTENANCE_MODE:
        bot.reply_to(message, 
            "🛠 *Server Maintenance Mode*\n\n"
            "Our server is currently undergoing maintenance.\n"
            "Please try again later.\n\n"
            "_We apologize for any inconvenience._",
            parse_mode="Markdown")
        return

    if not is_valid_command(message):
        bot.reply_to(message, "❌ Invalid command! Valid commands are:\n/skin <id> <id>\n/multiskin <id> <id>\n/xsuits <id> <id>")
        return

    args = message.text.split()[1:]

    if uid not in approved_users:
        bot.reply_to(message,
            "🎉 Welcome to HYPER SKINS BOT!\n\n"
            "👁 Please wait while we review your access request.\n"
            "▲ You will be notified once your access is approved.\n"
            "✅ Thank you for your patience!")
        return

    if len(args) < 2:
        bot.reply_to(message, f"❌ Use: /{cmd} <id1> <id2> ...")
        return

    item_ids = [int(arg) for arg in args if arg.isdigit()]
    invalid_ids = [sid for sid in item_ids if sid not in ITEMS]
    if invalid_ids:
        bot.reply_to(message, "⚠ Invalid ID(s) detected!\nPlease re-check the format or the skin IDs you've entered.", parse_mode="Markdown")
        return

    result = f"*{cmd.upper()} LOOKUP RESULTS* 🔍\n\n"
    for sid in item_ids:
        result += f"• ID `{sid}`: _{ITEMS[sid]}_\n"
    result += "\n_Processing your request..._"
    bot.send_message(uid, result, parse_mode="Markdown")

    loading_animation(uid)

    zip_file = ""
    if cmd in ["skin", "multiskin"]:
        zip_file = "HYPERSKINS1.zip"
    elif cmd == "xsuits":
        zip_file = "HYPERSKINS.zip"

    logging.info(f"Sending {zip_file} for command {cmd}")

    if zip_file and os.path.exists(zip_file):
        with open(zip_file, "rb") as z:
            bot.send_document(uid, z)
        bot.send_message(uid, "✅ Your mixed skin has been created! Enjoy!\n\n¹ HYPERSKINS BOT")
    else:
        bot.send_message(uid, f"❌ {zip_file} not found.")

@bot.message_handler(commands=["skin"])
def skin_cmd(message): handle_command(message, "skin")

@bot.message_handler(commands=["multiskin"])
def multiskin_cmd(message): handle_command(message, "multiskin")

@bot.message_handler(commands=["xsuits"])
def xsuits_cmd(message): handle_command(message, "xsuits")

@bot.message_handler(func=lambda message: message.text.startswith('/'))
def handle_wrong_command(message):
    command = message.text.split()[0].lower().strip('/')
    if is_admin_command(command) and message.chat.id not in ADMIN_IDS:
        bot.reply_to(message, "⚠️ You cannot use admin commands!")
        return
    if command not in ['skin', 'multiskin', 'xsuits', 'start', 'approve', 'disapprove', 'broadcast', 'users']:
        bot.reply_to(message, 
            "❌ *Invalid Command!*\n\n"
            "📝 *Available Commands:*\n"
            "• `/skin <id> <id>`\n"
            "• `/multiskin <id> <id>`\n"
            "• `/xsuits <id> <id>`\n\n"
            "Please check your command and try again!", 
            parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_invalid_message(message):
    if message.text and not message.text.startswith('/'):
        bot.reply_to(message,
            "❌ *Invalid Message!*\n\n"
            "Please use one of these commands:\n"
            "• `/skin <id> <id>` - Create custom skin\n"
            "• `/multiskin <id> <id>` - Mix multiple skins\n"
            "• `/xsuits <id> <id>` - Customize X-Suits\n\n"
            "_Use the commands exactly as shown above._",
            parse_mode="Markdown")

def run_bot():
    global MAINTENANCE_MODE
    max_retries = 3
    retry_count = 0

    while True:
        try:
            if retry_count >= max_retries:
                MAINTENANCE_MODE = True
                logging.warning("Bot entered maintenance mode due to repeated errors")

            logging.info("Bot starting..." if not MAINTENANCE_MODE else "Bot running in maintenance mode...")
            bot.infinity_polling(timeout=20, long_polling_timeout=5)

            # If we get here, reset retry count as bot is running normally
            retry_count = 0
            MAINTENANCE_MODE = False

        except Exception as e:
            logging.error(f"Bot error: {str(e)}")
            retry_count += 1

            if retry_count >= max_retries:
                MAINTENANCE_MODE = True
                logging.warning("Switching to maintenance mode due to errors")

            time.sleep(5)  # Wait before retry
            continue

if __name__ == "__main__":
    run_bot()