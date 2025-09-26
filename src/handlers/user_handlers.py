"""
Обработчики для пользователей
"""
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import ContextTypes
from config import PARTS_LIST, IMAGES
from src.database.db_manager import save_user, save_order, get_user_orders, save_support_message
from src.utils.message_utils import update_main_message, delete_user_message

# Глобальные переменные для состояния пользователей
user_state = {}
user_parts = {}
user_contact = {}
last_order_time = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await save_user(user.id, user.username, user.first_name, user.last_name)
    
    # Создаем клавиатуру
    keyboard = [
        [InlineKeyboardButton("Автозапчасти", callback_data="cat_parts")],
        [InlineKeyboardButton("Аксессуары", callback_data="cat_accessories")],
        [InlineKeyboardButton("Другое", callback_data="cat_other")],
        [InlineKeyboardButton("Поддержка", callback_data="support")],
        [InlineKeyboardButton("Мои заказы", callback_data="my_orders")]
    ]
    
    # Отправляем изображение с приветствием и кнопками в одном сообщении
    try:
        with open(IMAGES['start_menu'], 'rb') as photo:
            message = await update.message.reply_photo(
                photo=photo,
                caption="Добро пожаловать в TrueParts82!\n"
                        "Здесь говорят на языке деталей - честно, по делу и с уважением к клиенту.\n"
                        "📩 Пиши сразу: марку, модель, год, что ищешь - подберём, проконсультируем, отправим!\n"
                        "📦 Отправка по РФ, ответ по делу, без 'посмотрим на складе через неделю'.\n"
                        "🎯 Здесь быстро, чётко и без лишнего.\n\n"
                        "👇 Выберите, что вам нужно:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except FileNotFoundError:
        # Если изображение не найдено, отправляем обычное текстовое сообщение с кнопками
        message = await update.message.reply_text(
            "Добро пожаловать в TrueParts82!\n"
            "Здесь говорят на языке деталей - честно, по делу и с уважением к клиенту.\n"
            "📩 Пиши сразу: марку, модель, год, что ищешь - подберём, проконсультируем, отправим!\n"
            "📦 Отправка по РФ, ответ по делу, без 'посмотрим на складе через неделю'.\n"
            "🎯 Здесь быстро, чётко и без лишнего.\n\n"
            "👇 Выберите, что вам нужно:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # Сохраняем ID сообщения для последующего редактирования
    context.user_data['main_message_id'] = message.message_id


async def handle_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback запросов от пользователей"""
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        # Игнорируем ошибки с устаревшими callback query
        if "Query is too old" in str(e) or "query id is invalid" in str(e):
            return
        else:
            raise e
    
    uid = query.from_user.id
    data = query.data

    if data.startswith("cat_"):
        cat = data.split("_", 1)[1]
        user_state[uid] = {"category": cat, "step": "choosing"}
        user_parts[uid] = []
        if cat == "parts":
            buttons = [InlineKeyboardButton(p, callback_data=f"part_{i}") for i, p in enumerate(PARTS_LIST)]
            rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
            rows.append([InlineKeyboardButton("Готово", callback_data="done_parts")])
            await update_main_message(update, context, "🛠 Выберите автозапчасти:", rows)
        else:
            user_state[uid]["step"] = "waiting_contact"
            await update_main_message(update, context, "✍️ Укажите имя и номер телефона:")

    elif data.startswith("part_"):
        idx = int(data.split("_", 1)[1])
        part = PARTS_LIST[idx]
        sel = user_parts.get(uid, [])
        if part in sel:
            sel.remove(part)
        else:
            sel.append(part)
        buttons = [InlineKeyboardButton(("✅ " + p) if p in sel else p, callback_data=f"part_{i}") for i, p in enumerate(PARTS_LIST)]
        rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        rows.append([InlineKeyboardButton("Готово", callback_data="done_parts")])
        await update_main_message(update, context, "🛠 Выберите автозапчасти:", rows)

    elif data == "done_parts":
        if not user_parts.get(uid):
            return await query.message.reply_text("⚠️ Выберите хотя бы одну запчасть.")
        user_state[uid]["step"] = "waiting_contact"
        await update_main_message(update, context, "✍️ Укажите имя и номер телефона:")

    elif data == "support":
        user_state[uid] = {"step": "support_mode"}
        await query.message.reply_text(
            "📬 Напишите нам прямо сюда — наши менеджеры свяжутся с вами в ближайшее время!\n\n"
            "Для выхода из режима поддержки используйте /start"
        )

    elif data == "my_orders":
        orders = await get_user_orders(uid)
        if not orders:
            await query.message.reply_text("📭 У вас пока нет заказов.")
        else:
            text = "📋 Ваши заказы:\n\n"
            for order in orders:
                status_emoji = "✅" if order[5] == "completed" else "⏳"
                text += f"{status_emoji} Заказ #{order[0]}\n"
                text += f"📂 Категория: {order[1]}\n"
                text += f"🔧 Запчасти: {order[2]}\n"
                text += f"📞 Контакт: {order[3]}\n"
                text += f"📝 Описание: {order[4]}\n"
                text += f"📅 Дата: {order[6]}\n\n"
            await query.message.reply_text(text)

    elif data == "new_order":
        # Возвращаем пользователя в главное меню
        user_state.pop(uid, None)
        user_parts.pop(uid, None)
        user_contact.pop(uid, None)
        
        # Создаем клавиатуру главного меню
        keyboard = [
            [InlineKeyboardButton("Автозапчасти", callback_data="cat_parts")],
            [InlineKeyboardButton("Аксессуары", callback_data="cat_accessories")],
            [InlineKeyboardButton("Другое", callback_data="cat_other")],
            [InlineKeyboardButton("Поддержка", callback_data="support")],
            [InlineKeyboardButton("Мои заказы", callback_data="my_orders")]
        ]
        
        # Обновляем главное сообщение
        try:
            with open(IMAGES['start_menu'], 'rb') as photo:
                await context.bot.edit_message_media(
                    chat_id=update.effective_chat.id,
                    message_id=context.user_data.get('main_message_id'),
                    media=InputMediaPhoto(
                        media=photo,
                        caption="Добро пожаловать в TrueParts82!\n"
                                "Здесь говорят на языке деталей - честно, по делу и с уважением к клиенту.\n"
                                "📩 Пиши сразу: марку, модель, год, что ищешь - подберём, проконсультируем, отправим!\n"
                                "📦 Отправка по РФ, ответ по делу, без 'посмотрим на складе через неделю'.\n"
                                "🎯 Здесь быстро, чётко и без лишнего.\n\n"
                                "👇 Выберите, что вам нужно:"
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        except:
            # Если не удается отредактировать медиа, обновляем текст
            await update_main_message(
                update, context,
                "Добро пожаловать в TrueParts82!\n"
                "Здесь говорят на языке деталей - честно, по делу и с уважением к клиенту.\n"
                "📩 Пиши сразу: марку, модель, год, что ищешь - подберём, проконсультируем, отправим!\n"
                "📦 Отправка по РФ, ответ по делу, без 'посмотрим на складе через неделю'.\n"
                "🎯 Здесь быстро, чётко и без лишнего.\n\n"
                "👇 Выберите, что вам нужно:",
                keyboard
            )


async def handle_user_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений от пользователей"""
    user = update.effective_user
    uid = user.id
    now = time.time()

    if uid not in user_state:
        return await update.message.reply_text("❗ Начните с /start")

    step = user_state[uid].get("step")
    text = update.message.text.strip()

    if now - last_order_time.get(uid, 0) < 30:
        return await update.message.reply_text("⏳ Подождите 30 секунд между заказами.")

    if step == "waiting_contact":
        if len(text) < 5:
            await delete_user_message(update, context)
            return await update.message.reply_text("⚠️ Введите корректное имя и номер.")
        
        user_contact[uid] = text
        user_state[uid]["step"] = "waiting_notes"
        await delete_user_message(update, context)
        await update_main_message(update, context, "✍️ Напишите VIN код (или номер машины) и коротко опишите заказ:")
        return

    if step == "waiting_notes":
        if len(text) < 5:
            await delete_user_message(update, context)
            return await update.message.reply_text("⚠️ Опишите подробнее, минимум 5 символов.")
        
        last_order_time[uid] = now
        category = user_state[uid]["category"]
        parts = ", ".join(user_parts.get(uid, [])) if category == "parts" else "-"
        contact = user_contact.get(uid, "-")
        notes = text
        
        # Сохраняем заказ в базу данных
        order_id = await save_order(uid, category, parts, contact, notes)
        
        # Удаляем сообщение пользователя
        await delete_user_message(update, context)
        
        # Создаем кнопку "Назад" для нового заказа
        back_keyboard = [[InlineKeyboardButton("🆕 Новый заказ", callback_data="new_order")]]
        
        await update_main_message(
            update, context,
            f"✅ Заказ #{order_id} оформлен!\n"
            f"Категория: {category}\n"
            f"Контакт: {contact}\n\n"
            f"Наш менеджер рассмотрит вашу заявку в ближайшее время.",
            back_keyboard
        )
        
        # Отправляем уведомление админам
        from config import ADMINS
        msg = (
            f"📥 Новый заказ #{order_id} от @{user.username or user.first_name}:\n"
            f"📂 Категория: {category}\n"
            f"🔧 Запчасти: {parts}\n"
            f"📞 Контакт: {contact}\n"
            f"📝 Описание: {notes}"
        )
        for a in ADMINS:
            await context.bot.send_message(chat_id=a, text=msg)

        user_state.pop(uid, None)
        user_parts.pop(uid, None)
        user_contact.pop(uid, None)

    if step == "support_mode":
        # Сохраняем сообщение поддержки в базу данных
        await save_support_message(uid, text)
        
        # Удаляем сообщение пользователя
        await delete_user_message(update, context)
        
        # Пересылаем сообщение админам с информацией о пользователе
        from config import ADMINS
        username = user.username or user.first_name or "Без имени"
        support_msg = (
            f"📞 Сообщение от пользователя:\n"
            f"👤 @{username} (ID: {uid})\n"
            f"💬 {text}"
        )
        for admin_id in ADMINS:
            await context.bot.send_message(chat_id=admin_id, text=support_msg)
        
        await update.message.reply_text(
            "✅ Ваше сообщение отправлено менеджерам!\n"
            "Мы свяжемся с вами в ближайшее время.\n\n"
            "Для выхода из режима поддержки используйте /start"
        )
