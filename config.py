import os, dotenv


dotenv.load_dotenv('.env')

# Конфигурация
TOKEN = os.getenv('TOKEN')
BASE_URL = os.getenv('BASE_URL')
TARGET_URL = os.getenv('TARGET_URL')
USERNAME = "maks5554377@gmail.com" #os.getenv('USERNAME')
PASSWORD = "Maks5555" #os.getenv('PASSWORD')

# Константы задержек (в секундах)
CLICK_DELAY = 0.3           # Задержка между кликами
SHORT_DELAY = 0.2           # Короткая задержка
MEDIUM_DELAY = 0.3          # Средняя задержка для скроллинга
STANDARD_DELAY = 0.7         # Стандартная задержка
PAGE_LOAD_DELAY = 2         # Задержка загрузки страницы
LONG_DELAY = 3              # Длинная задержка для сложных операций

# Настройки отладки
ENABLE_DEBUG_LOGS = True    # Включить детальные логи отладки
HEADLESS_MODE = True      # Включить headless режим (False для отладки с видимым браузером)

# Дополнительные задержки для headless режима
HEADLESS_EXTRA_DELAY = 1    # Дополнительная задержка для headless режима
HEADLESS_PAGE_LOAD = 5      # Время загрузки страниц в headless режиме

# Настройки парсинга
SUBCATEGORIES_DATA_ID = "5751"  # data-id для поиска subcategories