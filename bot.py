import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import firebase_admin
from firebase_admin import credentials, db

# 1. HARDCODED CREDENTIALS
BOT_TOKEN = "8607997903:AAGGTIrAaP3mh58C2ykiUB1579MjGYztoAk"
FIREBASE_DB_URL = "https://dogla-de225-default-rtdb.firebaseio.com"

# 2. LOGGING SETUP
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 3. FIREBASE INITIALIZATION
if not firebase_admin._apps:
    try:
        options = {'databaseURL': FIREBASE_DB_URL}
        firebase_admin.initialize_app(options=options)
        logger.info("Firebase successfully connected.")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")

# 4. COMMAND HANDLERS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generates the 3-column matrix grid menu automatically."""
    total_buttons = 42
    columns = 3
    
    keyboard = []
    current_row = []
    
    for i in range(1, total_buttons + 1):
        # Create button structure with distinct callback markers
        button = InlineKeyboardButton(
            text=f"🎯 Target {i}", 
            callback_data=f"node_{i}"
        )
        current_row.append(button)
        
        # Grid layout chunking rules
        if len(current_row) == columns:
            keyboard.append(current_row)
            current_row = []
            
    if current_row:
        keyboard.append(current_row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text="🔥 *50 Active Targets Ready!*\nSelect a target to view live statistics:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processes selections from the grid and queries the database."""
    query = update.callback_query
    await query.answer() # Prevent button spinning animation
    
    selected_node = query.data # Retrieves 'node_1', 'node_2', etc.
    node_index = selected_node.split("_")[1]

    try:
        # Reference a specific node index structure inside your database root
        ref = db.reference(f'/targets/target_{node_index}') 
        data = ref.get()

        if data and isinstance(data, dict):
            status = data.get('status', 'Unknown')
            battery = data.get('battery', 'N/A')
            last_seen = data.get('last_seen', 'N/A')
            
            response_text = (
                f"📊 *Target {node_index} Data Matrix*\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"🟢 *Status:* {status}\n"
                f"🔋 *Battery:* {battery}%\n"
                f"🕒 *Last Activity:* {last_seen}\n"
            )
        else:
            # Fallback text if the specific node has no data generated yet
            response_text = (
                f"📊 *Target {node_index} Data Matrix*\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ No active key-value data found for target index {node_index} in the root database path."
            )

    except Exception as e:
        logger.error(f"Database read error: {e}")
        response_text = f"❌ *Connection Error:* Unable to fetch data for Target {node_index}."

    # Provide an inline back button to return to the original grid matrix view
    back_keyboard = [[InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(back_keyboard)

    await query.edit_message_text(text=response_text, reply_markup=reply_markup, parse_mode="Markdown")

async def back_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Allows navigating back to the main menu view without sending a new message."""
    query = update.callback_query
    await query.answer()
    
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

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="🔥 *50 Active Targets Ready!*\nSelect a target to view live statistics:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# 5. EXECUTION ENGINE
def main() -> None:
    """Initializes and runs the pooling loop application."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Route explicit commands and prefix dynamic callback expressions
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_selection, pattern="^node_"))
    application.add_handler(CallbackQueryHandler(back_menu, pattern="^back_to_menu$"))

    logger.info("Bot execution started...")
    application.run_polling()

if __name__ == "__main__":
    main()
