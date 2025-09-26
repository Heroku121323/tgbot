"""
Утилиты для работы с сообщениями
"""
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


async def update_main_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, buttons=None):
    """Обновляет главное сообщение в чате"""
    try:
        # Пытаемся отредактировать существующее сообщение
        if buttons:
            reply_markup = InlineKeyboardMarkup(buttons)
        else:
            reply_markup = None
            
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=context.user_data.get('main_message_id'),
            text=text,
            reply_markup=reply_markup
        )
    except Exception:
        # Если не удается отредактировать, отправляем новое сообщение
        if buttons:
            reply_markup = InlineKeyboardMarkup(buttons)
        else:
            reply_markup = None
            
        message = await update.message.reply_text(text, reply_markup=reply_markup)
        context.user_data['main_message_id'] = message.message_id


async def delete_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет сообщение пользователя"""
    try:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
    except Exception:
        # Игнорируем ошибки при удалении сообщений
        pass
