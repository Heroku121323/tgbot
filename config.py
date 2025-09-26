"""
Конфигурация бота TrueParts82
"""

# Токен бота
BOT_TOKEN = '7602433028:AAGWxfVufZLuQ2o_61aEaJ2r2bNqPPv_2kE'

# ID администраторов
ADMINS = [672618367, 1638519942]

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
