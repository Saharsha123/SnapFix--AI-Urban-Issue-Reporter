"""
SnapFix Telegram Bot - Frontend for SnapFix Backend
Requires: python-telegram-bot>=20, requests, python-dotenv, pillow

SnapFix Telegram Bot
Frontend interface for reporting and tracking civic issues.
Communicates with SnapFix Flask backend.
"""

import os
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv


from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode


# ================= ENV & CONFIG ================= #


load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5000")


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ================= STATES ================= #


(
    MAIN_MENU,
    REPORT_CHOICE,
    REPORT_LOCATION,
    REPORT_DESCRIPTION,
    REPORT_PHOTO,
    CONFIRM_REPORT,
    TRACKING_ID,
) = range(7)


user_sessions = {}


# ================= HELPERS ================= #


def get_user_session(user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    return user_sessions[user_id]


def clear_user_session(user_id):
    user_sessions.pop(user_id, None)


# ================= START ================= #


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📸 New Report", callback_data="new_report"),
            InlineKeyboardButton("📍 Track Issue", callback_data="track_issue"),
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="help"),
        ],
    ]
    await update.message.reply_text(
        "🚨 *Welcome to SnapFix*\n\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )
    return MAIN_MENU


# ================= MAIN MENU ================= #


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = get_user_session(update.effective_user.id)
    
    if query.data in ["back_to_menu", "menu"]:
        keyboard = [
            [
                InlineKeyboardButton("📸 New Report", callback_data="new_report"),
                InlineKeyboardButton("📍 Track Issue", callback_data="track_issue"),
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data="help"),
            ],
        ]
        await query.edit_message_text(
            "📱 *Main Menu*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MAIN_MENU


    if query.data == "new_report":
        keyboard = [
            [InlineKeyboardButton("📸 Upload Photo", callback_data="upload_photo")],
            [InlineKeyboardButton("✍️ Manual Report", callback_data="manual_report")],
        ]
        await query.edit_message_text(
            "How would you like to report?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return REPORT_CHOICE


    if query.data == "track_issue":
        await query.edit_message_text("Enter Tracking ID:")
        return TRACKING_ID


    if query.data == "help":
        help_text = (
            "📱 *SnapFix Help*\n\n"
            "🔹 *New Report:* Upload a photo or describe an issue to report it.\n"
            "🔹 *Track Issue:* Enter your tracking ID to check the status.\n"
            "🔹 *Help:* View this help message.\n\n"
            "Questions? Contact support@snapfix.local"
        )
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🏠 Back", callback_data="back_to_menu")]]
        )
        await query.edit_message_text(help_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        return MAIN_MENU


# ================= REPORT FLOW ================= #


async def report_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = get_user_session(update.effective_user.id)

    if query.data == "manual_report":
        keyboard = [
            [
                InlineKeyboardButton("🕳️ Pothole", callback_data="pothole_road_crack"),
                InlineKeyboardButton("💧 Water Log", callback_data="water_logging"),
            ],
            [
                InlineKeyboardButton("🗑️ Garbage", callback_data="garbage"),
                InlineKeyboardButton("⚡ No Power", callback_data="no_electricity"),
            ],
        ]
        await query.edit_message_text(
            "Select issue type:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return REPORT_CHOICE

    if query.data == "upload_photo":
        await query.edit_message_text(
            "📍 Please send your location (attach via Telegram)."
        )
        return REPORT_LOCATION


async def issue_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = get_user_session(update.effective_user.id)
    session["issue_type"] = query.data

    await query.edit_message_text("📍 Please send your location (attach via Telegram).")
    return REPORT_LOCATION


async def report_location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_user_session(update.effective_user.id)
    session["latitude"] = update.message.location.latitude
    session["longitude"] = update.message.location.longitude
    await update.message.reply_text(
        "📝 Add description (or type 'skip'):",
        reply_markup=ReplyKeyboardRemove(),
    )
    return REPORT_DESCRIPTION


async def report_description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_user_session(update.effective_user.id)
    session["description"] = (
        "" if update.message.text.lower() == "skip" else update.message.text
    )

    await update.message.reply_text(
        "📸 Upload a photo of the issue (or type 'skip'):",
        reply_markup=ReplyKeyboardRemove(),
    )

    return REPORT_PHOTO


async def report_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_user_session(update.effective_user.id)

    # CASE 1: TEXT-ONLY (skip photo)
    if update.message.text and update.message.text.lower() == "skip":
        session["photo_file_id"] = None

        try:
            data = {"description": session.get("description", "")}
            r = requests.post(f"{BACKEND_URL}/api/classify", data=data)

            if r.status_code == 200:
                res = r.json()
                session["issue_type"] = res.get("issueType", session.get("issue_type", "Unknown"))
                session["probability"] = res.get("probability", 0)
                session["priority"] = res.get("priority", "Medium")
                session["decision_source"] = res.get("decisionSource")
                session["raw_label"] = res.get("issueType")

                await update.message.reply_text(
                    f"✅ Text classified!\n"
                    f"Type: {session['issue_type']}\n"
                    f"Confidence: {session['probability']*100:.1f}%\n"
                    f"Priority: {session['priority']}"
                )
            else:
                await update.message.reply_text("⚠️ Classification failed.")
        except Exception as e:
            logging.error(f"Text classify error: {e}")
            await update.message.reply_text("⚠️ Error classifying.")

        await proceed_to_confirm(update, session)
        return CONFIRM_REPORT

    # CASE 2: PHOTO
    if not update.message.photo:
        await update.message.reply_text("❌ Please send a valid photo or type 'skip'.")
        return REPORT_PHOTO

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    photo_bytes = await file.download_as_bytearray()

    try:
        files = {'file': ('photo.jpg', photo_bytes, 'image/jpeg')}
        data = {'description': session.get("description", "")}
        r = requests.post(f"{BACKEND_URL}/api/classify", files=files, data=data)

        if r.status_code == 200:
            data = r.json()
            session["issue_type"] = data.get("issueType", session.get("issue_type"))
            session["probability"] = data.get("probability", 0)
            session["priority"] = data.get("priority", "Medium")
            session["photo_file_id"] = photo.file_id
            session["decision_source"] = data.get("decisionSource")
            session["raw_label"] = data.get("issueType")

            await update.message.reply_text(
                f"✅ Photo classified!\n"
                f"Type: {session['issue_type']}\n"
                f"Confidence: {session['probability']*100:.1f}%\n"
                f"Priority: {session['priority']}"
            )
        else:
            await update.message.reply_text("⚠️ Classification failed.")
            session["photo_file_id"] = photo.file_id
    except Exception as e:
        logging.error(f"Classify error: {e}")
        await update.message.reply_text("⚠️ Error uploading photo.")
        session["photo_file_id"] = photo.file_id

    await proceed_to_confirm(update, session)
    return CONFIRM_REPORT


async def proceed_to_confirm(update: Update, session):
    priority = session.get("priority", "Medium")
    await update.message.reply_text(
        f"📋 Confirm report?\n"
        f"Type: {session.get('issue_type', 'Unknown')}\n"
        f"Priority: {priority}",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✅ Submit", callback_data="submit"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
                ]
            ]
        ),
    )


async def confirm_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = get_user_session(update.effective_user.id)

    if query.data == "submit":
        payload = {
            "telegram_id": update.effective_user.id,
            "issueType": session["issue_type"],
            "location": f"{session['latitude']},{session['longitude']}",
            "description": session["description"],
            "timestamp": datetime.now().isoformat(),
            "priority": session.get("priority", "Medium"),
            "probability": session.get("probability"),
            "decisionSource": session.get("decision_source"),
            "rawLabel": session.get("raw_label", session["issue_type"]),
        }
        r = requests.post(f"{BACKEND_URL}/api/report", json=payload)
        print("REPORT DEBUG:", r.status_code, r.text)

        if r.status_code == 200:
            data = r.json()
            tid = data["tracking_id"]
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("📱 Main Menu", callback_data="back_to_menu")]]
            )
            await query.edit_message_text(
                f"✅ Report submitted!\nTracking ID: `{tid}`",
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN,
            )
            return MAIN_MENU
        else:
            await query.edit_message_text("❌ Submission failed. Please try again.")
            return MAIN_MENU

    elif query.data == "cancel":
        await query.edit_message_text("❌ Report cancelled.")
        keyboard = [
            [
                InlineKeyboardButton("📸 New Report", callback_data="new_report"),
                InlineKeyboardButton("📍 Track Issue", callback_data="track_issue"),
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data="help"),
            ],
        ]
        await update.callback_query.edit_message_text(
            "📱 *Main Menu*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MAIN_MENU


# ================= TRACKING ================= #


async def tracking_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = update.message.text.strip()
    r = requests.get(f"{BACKEND_URL}/api/track", params={"id": tid})
    
    if r.status_code == 200:
        data = r.json()
        msg = (
            f"📋 Tracking ID: {data['tracking_id']}\n"
            f"Issue: {data['issuetype']}\n"
            f"Department: {data['primary_department']}\n"
            f"Priority: {data['priority']}\n\n"
            f"📊 Admin Status: {data['status']}\n"
            f"Admin Remarks: {data.get('remarks', 'No remarks')}\n\n"
            f"🔧 Department Status: {data.get('dept_status', 'Not Assigned')}\n"
            f"Department Remarks: {data.get('dept_remarks', 'No remarks')}\n\n"
            f"Timestamp: {data['timestamp']}"
        )
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("📱 Main Menu", callback_data="back_to_menu")]]
        )
        await update.message.reply_text(msg, reply_markup=keyboard)
    else:
        await update.message.reply_text("❌ Tracking ID not found.")
    
    return MAIN_MENU

# ================= MAIN ================= #


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(main_menu_callback)],
                        REPORT_CHOICE: [
                CallbackQueryHandler(
                    report_type_selection, pattern="^(manual_report|upload_photo)$"
                ),
                CallbackQueryHandler(
                    issue_selected,
                    pattern="^(pothole_road_crack|water_logging|garbage|no_electricity)$",
                ),
            ],
            REPORT_LOCATION: [
                MessageHandler(filters.LOCATION, report_location_handler)
            ],
            REPORT_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, report_description_handler)
            ],
            REPORT_PHOTO: [
                MessageHandler(
                    filters.PHOTO | (filters.TEXT & ~filters.COMMAND),
                    report_photo_handler,
                )
            ],
            CONFIRM_REPORT: [CallbackQueryHandler(confirm_report)],
            TRACKING_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tracking_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )

    app.add_handler(conv)
    app.run_polling()


if __name__ == "__main__":
    main()
