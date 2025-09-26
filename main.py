#!/usr/bin/env python3
"""
Telegram Bot для TrueParts82
Автозапчасти и аксессуары с доставкой по РФ
"""
import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN, ADMINS
from src.database.db_manager import init_db
from src.handlers.user_handlers import start, handle_user_callback, handle_user_text
from src.handlers.admin_handlers import admin_menu, handle_admin_callback


# Настройка логирования
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def is_admin(update):
    """Проверяет, является ли пользователь администратором"""
    return update.effective_user.id in ADMINS


async def callback_handler(update, context):
    """Обработчик callback запросов"""
    if is_admin(update):
        await handle_admin_callback(update, context)
    else:
        await handle_user_callback(update, context)


async def text_handler(update, context):
    """Обработчик текстовых сообщений"""
    if is_admin(update):
        # Админы могут использовать команды
        if update.message.text.startswith('/admin'):
            await admin_menu(update, context)
        return
    else:
        await handle_user_text(update, context)


def main():
    """Главная функция"""
    # Инициализация базы данных
    asyncio.run(init_db())
    
    # Создание приложения
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавление обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_menu))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    # Запуск бота
    logger.info("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
