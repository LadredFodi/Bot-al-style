import os, dotenv


dotenv.load_dotenv('.env')

# Конфигурация
TOKEN = "KDoIjA1X4-kGz31DdvWzQ7XSLKYRwf_y"
BASE_URL = "https://api.al-style.kz/#show_markdown"
TARGET_URL = BASE_URL
USERNAME = "maks5554377@gmail.com"
PASSWORD = "Maks5555"

# Настройки профиля браузера
PROFILE_DIR = "browser_profiles"  # Директория для хранения профилей
PROFILE_NAME = "main_profile"     # Имя профиля

# Константы задержек (в секундах) - оптимизированные значения
CLICK_DELAY = 0.3        # Задержка между кликами
SHORT_DELAY = 0.3          # Короткая задержка
MEDIUM_DELAY = 0.6          # Средняя задержка для скроллинга
STANDARD_DELAY = 0.5        # Стандартная задержка
PAGE_LOAD_DELAY = 2       # Задержка загрузки страницы
LONG_DELAY = 1.5              # Длинная задержка для сложных операций


HEADLESS_MODE = True      # Включить headless режим (False для отладки с видимым браузером)

# Дополнительные задержки для headless режима
HEADLESS_EXTRA_DELAY = 1 # Дополнительная задержка для headless режима
HEADLESS_PAGE_LOAD = 2      # Время загрузки страниц в headless режиме

# Настройки парсинга
SUBCATEGORIES_DATA_ID = "5751"  # data-id для поиска subcategories

CATEGORY_HIERARCHY = {
    "level1": ["5751"],  # Первый уровень категорий
    "level2": ["3586", "3613"],  # Второй уровень категорий
    "level3": ["3593", "3590", "3587", "3615"]  # Третий уровень категорий
}