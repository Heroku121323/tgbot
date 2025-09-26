"""
Модуль для работы с базой данных
"""
import aiosqlite
from config import DATABASE_PATH


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Таблица пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица заказов
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                parts TEXT,
                contact TEXT,
                notes TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица сообщений поддержки
        await db.execute('''
            CREATE TABLE IF NOT EXISTS support_messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        await db.commit()


async def save_user(user_id, username, first_name, last_name=None):
    """Сохранение/обновление пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, last_activity)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, username, first_name, last_name))
        await db.commit()


async def save_order(user_id, category, parts, contact, notes):
    """Сохранение заказа"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO orders (user_id, category, parts, contact, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, category, parts, contact, notes))
        order_id = cursor.lastrowid
        await db.commit()
        return order_id


async def get_orders():
    """Получение всех заказов"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            SELECT o.*, u.username, u.first_name
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            WHERE o.status = 'pending'
            ORDER BY o.created_at DESC
        ''')
        rows = await cursor.fetchall()
        return rows


async def complete_order_db(order_id):
    """Завершение заказа"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Получаем информацию о заказе
        cursor = await db.execute('SELECT user_id FROM orders WHERE order_id = ?', (order_id,))
        order = await cursor.fetchone()
        
        if order:
            # Обновляем статус заказа
            await db.execute('''
                UPDATE orders 
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP 
                WHERE order_id = ?
            ''', (order_id,))
            await db.commit()
            return order[0]  # Возвращаем user_id
        return None


async def save_support_message(user_id, message_text):
    """Сохранение сообщения поддержки"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO support_messages (user_id, message_text)
            VALUES (?, ?)
        ''', (user_id, message_text))
        await db.commit()


async def get_user_orders(user_id):
    """Получение заказов пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            SELECT order_id, category, parts, contact, notes, status, created_at
            FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        rows = await cursor.fetchall()
        return rows


async def get_all_clients(limit=10, offset=0):
    """Получение всех клиентов с пагинацией"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Получаем общее количество клиентов
        cursor = await db.execute('SELECT COUNT(*) FROM users')
        total_count = (await cursor.fetchone())[0]
        
        # Получаем клиентов с пагинацией и контактной информацией из последнего заказа
        cursor = await db.execute('''
            SELECT u.user_id, u.username, u.first_name, u.last_name, u.created_at, u.last_activity,
                   COUNT(o.order_id) as orders_count,
                   MAX(o.created_at) as last_order_date,
                   (SELECT contact FROM orders o2 WHERE o2.user_id = u.user_id ORDER BY o2.created_at DESC LIMIT 1) as last_contact
            FROM users u
            LEFT JOIN orders o ON u.user_id = o.user_id
            GROUP BY u.user_id, u.username, u.first_name, u.last_name, u.created_at, u.last_activity
            ORDER BY u.last_activity DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        clients = await cursor.fetchall()
        
        return clients, total_count
