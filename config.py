"""
Конфигурация бота TrueParts82
"""

# Токен бота (замените на свой)
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'

# ID администраторов (замените на свои)
ADMINS = [123456789, 987654321]

# Список автозапчастей
PARTS_LIST = [
    "Фильтры",
    "Детали подвески",
    "Система охлаждения",
    "Тормозные колодки",
    "Масло двигателя",
    "Свечи зажигания"
]

# Пути к изображениям
IMAGES = {
    'start_menu': 'assets/images/startmenu.png',
    'admin_panel': 'assets/images/adminpanel.png'
}

# Настройки базы данных
DATABASE_PATH = 'bot_database.db'

# Настройки пагинации
CLIENTS_PER_PAGE = 5
