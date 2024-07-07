from typing import Final
import logging
from telegram import (
    Update,
    InlineQueryResultPhoto,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    filters,
    MessageHandler,
    InlineQueryHandler,
    CallbackQueryHandler
)
# SIGPIPE management
# from signal import signal, SIGPIPE, SIG_DFL
# signal(SIGPIPE,SIG_DFL)
from mongo_client import AdsMongoClient


# Command handlers
BOT_TOKEN: Final = "6899268959:AAE-QtnkxdLK7HOZfvwExH_6BqUmcVIobhQ"
db_client = AdsMongoClient("localhost", 27017)
dev_ids = [198211817]
CATEGORY, PHOTO, DESCRIPTION, EDIT_DESCRIPTION, EDIT_DESCRIPTION_CONFIRMATION = range(5)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

async def start_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="سلام، من ربات ثبت آگهی هستم. برای ثبت آگهی جدید از دستور /add استفاده کنید.",
        reply_to_message_id=update.effective_message.id,
    )

async def add_category_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in dev_ids:
        category = " ".join(context.args)
        db_client.add_category(category=category)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"دسته بندی {category} با موفقیت اضافه شد.",
            reply_to_message_id=update.effective_message.id,
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="شما اجازه دسترسی به این دستور را ندارید.",
            reply_to_message_id=update.effective_message.id,
        )

async def add_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    categories = db_client.get_categories()
    keyboard = [
        [InlineKeyboardButton(category, callback_data=f"choice_category:{category}")] for category in categories
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "لطفا از بین دسته بندی های زیر یکی را انتخاب کنید:",
        reply_to_message_id=update.effective_message.id,
        reply_markup=reply_markup
    )
    return CATEGORY


async def choice_category_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action, context.user_data["category"] = query.data.split(":")
    # context.user_data["category"] = query.data
    if action == "choice_category":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text = "لطفا عکس آگهی خود را ارسال کنید.",
            reply_to_message_id=update.effective_message.id,
        )
        return PHOTO

async def photo_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["photo_url"] = update.effective_message.photo[-1].file_id
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "لطفا توضیحات آگهی خود را وارد کنید. در توضیحات می توانید اطلاعاتی مانند قیمت، شماره تماس و ... را وارد کنید.",
        reply_to_message_id=update.effective_message.id,
    )
    return DESCRIPTION

async def description_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["description"] = update.effective_message.text
    db_client.add_advertising(
        user_id=update.effective_user.id,
        category=context.user_data["category"],
        photo_url=context.user_data["photo_url"],
        description=context.user_data["description"]
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "آگهی شما با موفقیت ثبت شد.",
        reply_to_message_id=update.effective_message.id,
    )
    return ConversationHandler.END

async def edit_description_callback_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, context.user_data["ad_id_for_description_edit"] = query.data.split(":")
    if action == "edit_description":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text = "لطفا توضیحات جدید آگهی خود را وارد کنید.",
            reply_to_message_id=update.effective_message.id,
        )
        return EDIT_DESCRIPTION_CONFIRMATION

async def edit_description_confirmation_handler(update:Update, context: ContextTypes.DEFAULT_TYPE):
    db_client.update_description(doc_id=context.user_data["ad_id_for_description_edit"], edited_description=update.effective_message.text)
    context.user_data["ad_id_for_description_edit"] = None  # Clear the ad_id after updating
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="توضیحات آگهی با موفقیت به روز شد.",
        reply_to_message_id=update.message.message_id,
    )
    return ConversationHandler.END

async def cancel_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "عملیات ثبت آگهی لغو شد. برای ثبت آگهی جدید از دستور /add استفاده کنید.",
        reply_to_message_id=update.effective_message.id,
    )
    return ConversationHandler.END

async def my_ads_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ads = db_client.get_ads_by_user_id(update.effective_user.id)
    if ads:
        for ad in ads:
            keyboard = [
                [
                    InlineKeyboardButton("ویرایش توضیحات", callback_data=f"edit_description:{ad['id']}"),
                    InlineKeyboardButton("حذف آگهی", callback_data=f"delete_ad:{ad['id']}"),
                ]
            ]
            await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=ad["photo_url"],
            caption=ad["description"],
            reply_to_message_id=update.effective_message.id,
            reply_markup=InlineKeyboardMarkup(keyboard)
            )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text = "شما هیچ آگهی ثبت نکرده‌اید.",
            reply_to_message_id=update.effective_message.id,
        )

async def delete_ad_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, ad_id = query.data.split(":")
    if action == "delete_ad":
        db_client.delete_advertising(user_id=update.effective_user.id, doc_id=ad_id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text = "آگهی با موفقیت حذف شد.",
            reply_to_message_id=update.effective_message.id,
        )

async def search_ads_by_category_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    if not query:
        return
    ads = db_client.get_ads_by_category(query)
    results = [
        InlineQueryResultPhoto(
            id=ad["id"],
            title=ad["description"],
            photo_url=ad["photo_url"],
            thumbnail_url=ad["photo_url"],
            caption=ad["description"]
        )
        for ad in ads
    ]
    await context.bot.answer_inline_query(update.inline_query.id, results)

async def undefined_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="دستور وارد شده نامعتبر است. لطفاً یک دستور معتبر انتخاب کنید.",
        reply_to_message_id=update.effective_message.id,
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command_handler))
    app.add_handler(CommandHandler("add_category", add_category_command_handler))
    app.add_handler(CommandHandler("my_ads", my_ads_command_handler))
    app.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("add", add_command_handler)],
            states={
                CATEGORY: [
                    CallbackQueryHandler(choice_category_message_handler, pattern="^choice_category"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, choice_category_message_handler)
                ],
                PHOTO: [
                    MessageHandler(filters.PHOTO, photo_message_handler),
                ],
                DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, description_message_handler)
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_command_handler),
            ],
            allow_reentry=True,
        )
    )
    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(edit_description_callback_handler, pattern="^edit_description:")],
            states={
                EDIT_DESCRIPTION_CONFIRMATION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, edit_description_confirmation_handler)
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_command_handler),
            ],
            allow_reentry=True,
        )
    )
    app.add_handler(InlineQueryHandler(search_ads_by_category_inline_query))
    app.add_handler(CallbackQueryHandler(delete_ad_command_handler, pattern="^delete_ad:"))
    # Add the catch-all handler for undefined commands
    app.add_handler(MessageHandler(filters.COMMAND, undefined_command_handler))
    app.run_polling()