#!/usr/bin/env python3
"""
Скрипт для просмотра содержимого базы данных
"""
import asyncio
import aiosqlite
from config import DATABASE_PATH


async def view_database():
    """Просмотр всех таблиц базы данных"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        print("🗄️ Содержимое базы данных TrueParts82\n")
        
        # Просмотр таблицы пользователей
        print("👥 Пользователи:")
        cursor = await db.execute('SELECT * FROM users')
        users = await cursor.fetchall()
        if users:
            for user in users:
                print(f"  ID: {user[0]}, Username: @{user[1]}, Имя: {user[2]}, Регистрация: {user[4]}")
        else:
            print("  Пользователей нет")
        
        print("\n📋 Заказы:")
        cursor = await db.execute('SELECT * FROM orders')
        orders = await cursor.fetchall()
        if orders:
            for order in orders:
                print(f"  Заказ #{order[0]}: {order[2]} | {order[3]} | Статус: {order[6]}")
        else:
            print("  Заказов нет")
        
        print("\n💬 Сообщения поддержки:")
        cursor = await db.execute('SELECT * FROM support_messages')
        support = await cursor.fetchall()
        if support:
            for msg in support:
                print(f"  От пользователя {msg[1]}: {msg[2][:50]}...")
        else:
            print("  Сообщений поддержки нет")


if __name__ == "__main__":
    asyncio.run(view_database())
