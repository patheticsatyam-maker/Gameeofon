import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import firebase_admin
from firebase_admin import credentials, db

# 1. HARDCODED BOT CREDENTIALS
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
        cred_json_string = os.getenv("FIREBASE_CONFIG_JSON")
        if cred_json_string:
            cred_dict = json.loads(cred_json_string)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})
            logger.info("Firebase successfully connected using Service Account JSON.")
        else:
            firebase_admin.initialize_app(options={'databaseURL': FIREBASE_DB_URL})
            logger.warning("Firebase initialized via raw URL. Ensure your database Rules allow public reading.")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")

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
    """Sends the initial grid selection panel."""
    await update.message.reply_text(
        text="🔥 *50 Active Targets Ready!*\nSelect a target to view live statistics:",
        reply_markup=build_menu_keyboard(),
        parse_mode="Markdown"
    )

async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches real-time status data from Firebase database path."""
    query = update.callback_query
    await query.answer()
    
    selected_node = query.data
    node_index = selected_node.split("_")[1]

    try:
        # 🟢 PATH MAPPING STRATEGY
        # Change this path if your Firebase database layout uses different keys
        target_path = f'/targets/target_{node_index}'
        
        logger.info(f"Querying Firebase path: {target_path}")
        ref = db.reference(target_path) 
        data = ref.get()

        if data:
            logger.info(f"Data received for Target {node_index}: {data}")
            
            if isinstance(data, dict):
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
                response_text = f"📊 *Target {node_index} Raw Data*\n━━━━━━━━━━━━━━━━━━━\nValue: `{data}`"
        else:
            response_text = (
                f"⚠️ *Data Missing*\n\n"
                f"Path `{target_path}` returned empty.\n"
                f"Verify that your Firebase database structure matches this exact layout."
            )

    except Exception as e:
        logger.error(f"Database connection error: {e}")
        response_text = (
            f"❌ *Connection Error*\n\n"
            f"Unable to read path for Target {node_index}.\n"
            f"Ensure your Firebase rules allow read operations."
        )

    back_keyboard = [[InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back_to_menu")]]
    await query.edit_message_text(
        text=response_text, 
        reply_markup=InlineKeyboardMarkup(back_keyboard), 
        parse_mode="Markdown"
    )

async def back_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Brings the user back to the primary multi-column menu grid."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text="🔥 *50 Active Targets Ready!*\nSelect a target to view live statistics:",
        reply_markup=build_menu_keyboard(),
        parse_mode="Markdown"
    )

# 6. ENGINE START
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_selection, pattern="^node_"))
    application.add_handler(CallbackQueryHandler(back_menu, pattern="^back_to_menu$"))
    
    logger.info("Bot deployment initialization complete.")
    application.run_polling()

if __name__ == "__main__":
    main()
