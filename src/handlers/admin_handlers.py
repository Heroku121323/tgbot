"""
Обработчики для администраторов
"""
import aiosqlite
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from config import ADMINS, IMAGES, CLIENTS_PER_PAGE, DATABASE_PATH
from src.database.db_manager import get_orders, complete_order_db, get_all_clients


async def admin_menu(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню админ-панели"""
    # Проверяем, что передано - Update или CallbackQuery
    if hasattr(update_or_query, 'effective_user'):
        # Это Update
        user_id = update_or_query.effective_user.id
        message = update_or_query.message
    else:
        # Это CallbackQuery
        user_id = update_or_query.from_user.id
        message = update_or_query.message
    
    if user_id not in ADMINS:
        return await message.reply_text("⛔ Доступ только для админов.")
    
    buttons = [
        [InlineKeyboardButton("📋 Показать заказы", callback_data="admin_list")],
        [InlineKeyboardButton("👥 Все клиенты", callback_data="admin_clients")],
        [InlineKeyboardButton("🔄 Обновить", callback_data="admin_refresh")]
    ]
    
    # Отправляем изображение админ-панели с кнопками
    try:
        with open(IMAGES['admin_panel'], 'rb') as photo:
            await message.reply_photo(
                photo=photo,
                caption="🔐 Админ-панель TrueParts82",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    except FileNotFoundError:
        # Если изображение не найдено, отправляем обычное текстовое сообщение
        await message.reply_text(
            "🔐 Админ-панель TrueParts82",
            reply_markup=InlineKeyboardMarkup(buttons)
        )


async def show_orders(msg, context: ContextTypes.DEFAULT_TYPE):
    """Показать все заказы"""
    orders = await get_orders()
    if not orders:
        return await msg.reply_text("📭 Заказов нет.")
    
    text = "📋 Активные заказы:\n"
    buttons = []
    
    for order in orders:
        text += (
            f"\n#{order[0]} @{order[7] or order[8]}\n"
            f"Категория: {order[2]}\n"
            f"Запчасти: {order[3]}\n"
            f"Контакт: {order[4]}\n"
            f"📝 {order[5]}\n"
            f"📅 {order[7]}\n"
        )
        buttons.append([
            InlineKeyboardButton(f"✅ Завершить заказ #{order[0]}", callback_data=f"complete_{order[0]}"),
            InlineKeyboardButton(f"📦 Готов к выдаче #{order[0]}", callback_data=f"ready_{order[0]}")
        ])
    
    await msg.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


async def show_clients(msg, context: ContextTypes.DEFAULT_TYPE, page=0):
    """Показать всех клиентов с пагинацией"""
    limit = CLIENTS_PER_PAGE
    offset = page * limit
    
    clients, total_count = await get_all_clients(limit, offset)
    
    if not clients:
        return await msg.reply_text("📭 Клиентов нет.")
    
    text = f"👥 Все клиенты (страница {page + 1} из {(total_count + limit - 1) // limit}):\n\n"
    
    for client in clients:
        orders_count = int(client[6]) if client[6] else 0  # client[6] = orders_count
        orders_text = f"{orders_count} заказов" if orders_count > 0 else "нет заказов"
        last_order = f" | Последний заказ: {client[7]}" if client[7] else ""  # client[7] = last_order_date
        phone = client[8] if client[8] else "не указан"  # client[8] = last_contact
        
        text += (
            f"👤 @{client[1] or 'без username'} ({client[2]})\n"  # client[1] = username, client[2] = first_name
            f"🆔 ID: {client[0]}\n"  # client[0] = user_id
            f"📞 Телефон: {phone}\n"
            f"📊 {orders_text}{last_order}\n"
            f"📅 Регистрация: {client[4]}\n\n"  # client[4] = created_at
        )
    
    # Создаем кнопки навигации
    buttons = []
    nav_buttons = []
    
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"clients_page_{page-1}"))
    
    if (page + 1) * limit < total_count:
        nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"clients_page_{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton("🔙 В админ-панель", callback_data="admin_menu")])
    
    await msg.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback запросов от администраторов"""
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

    if data == "admin_list":
        await show_orders(query.message, context)

    elif data == "admin_clients":
        await show_clients(query.message, context, page=0)

    elif data == "admin_refresh":
        # Просто обновляем админ-панель
        await admin_menu(query, context)

    elif data == "admin_menu":
        # Возвращаемся в админ-панель
        await admin_menu(query, context)

    elif data.startswith("clients_page_"):
        page = int(data.split("_", 2)[2])
        await show_clients(query.message, context, page=page)

    elif data.startswith("complete_"):
        order_id = int(data.split("_", 1)[1])
        if uid not in ADMINS:
            try:
                await query.answer("❌ Нет доступа.")
            except:
                pass
            return
        
        user_id = await complete_order_db(order_id)
        if user_id:
            try:
                await query.answer(f"✅ Заказ #{order_id} завершён.")
            except:
                pass
            # Отправляем уведомление с кнопкой "Новый заказ"
            keyboard = [[InlineKeyboardButton("🆕 Новый заказ", callback_data="new_order")]]
            await context.bot.send_message(
                chat_id=user_id, 
                text=f"✅ Ваш заказ #{order_id} выполнен!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            # Обновляем список заказов
            await show_orders(query.message, context)
        else:
            try:
                await query.answer("❌ Заказ не найден.")
            except:
                pass

    elif data.startswith("ready_"):
        order_id = int(data.split("_", 1)[1])
        if uid not in ADMINS:
            try:
                await query.answer("❌ Нет доступа.")
            except:
                pass
            return
        
        # Получаем информацию о заказе из базы данных
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT user_id FROM orders WHERE order_id = ?', (order_id,))
            order = await cursor.fetchone()
            if order:
                await context.bot.send_message(
                    chat_id=order[0],
                    text=f"✅ Ваш заказ №{order_id} готов к выдаче! Можете забирать."
                )
                try:
                    await query.answer(f"📤 Уведомление по заказу #{order_id} отправлено.")
                except:
                    pass
            else:
                try:
                    await query.answer("❌ Заказ не найден.")
                except:
                    pass
