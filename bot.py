import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# 1. HARDCODED BOT CREDENTIALS
BOT_TOKEN = "8607997903:AAGGTIrAaP3mh58C2ykiUB1579MjGYztoAk"

# 2. LOGGING SETUP
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 3. LOCAL DATA STORAGE (Replaces Firebase entirely)
# You can change these values right here in the code!
def get_target_data(node_index):
    """
    Simulates database data. Since you don't have a firebase console, 
    this dictionary provides instant mock data for all 42 targets.
    """
    # Default fallback data structure
    data = {
        "status": "Online",
        "battery": "78",
        "last_seen": "Just now"
    }
    
    # Example: Customizing data for specific targets manually in code
    if node_index == "1":
        data["status"] = "Online"
        data["battery"] = "94"
    elif node_index == "2":
        data["status"] = "Offline"
        data["battery"] = "0"
        data["last_seen"] = "2 hours ago"
        
    return data

# 4. MATRIX MENU GENERATOR
def build_menu_keyboard():
    total_buttons = 42
    columns = 3
    keyboard = []
    current_row = []
    for i in range(1, total_buttons + 1):
        button = InlineKeyboardButton(text=f"🎯 Target {i}", callback_data=f"node_{i}")
        current_row.append(button)
        if len(current_row) == columns:
            keyboard.append(current_row)
            current_row = []
    if current_row:
        keyboard.append(current_row)
    return InlineKeyboardMarkup(keyboard)

# 5. COMMAND HANDLERS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        text="🔥 *50 Active Targets Ready!*\nSelect a target to view live statistics:",
        reply_markup=build_menu_keyboard(),
        parse_mode="Markdown"
    )

async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    selected_node = query.data
    node_index = selected_node.split("_")[1]

    # Fetch data directly from the local function instead of Firebase
    data = get_target_data(node_index)

    response_text = (
        f"📊 *Target {node_index} Data Matrix*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 *Status:* {data['status']}\n"
        f"🔋 *Battery:* {data['battery']}%\n"
        f"🕒 *Last Activity:* {data['last_seen']}\n\n"
        f"📂 _Storage Mode: Self-contained Local Script_"
    )

    back_keyboard = [[InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back_to_menu")]]
    await query.edit_message_text(
        text=response_text, 
        reply_markup=InlineKeyboardMarkup(back_keyboard), 
        parse_mode="Markdown"
    )

async def back_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text="🔥 *50 Active Targets Ready!*\nSelect a target to view live statistics:",
        reply_markup=build_menu_keyboard(),
        parse_mode="Markdown"
    )

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_selection, pattern="^node_"))
    application.add_handler(CallbackQueryHandler(back_menu, pattern="^back_to_menu$"))
    logger.info("Local standalone bot started successfully.")
    application.run_polling()

if __name__ == "__main__":
    main()
            
