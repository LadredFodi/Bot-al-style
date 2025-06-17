import os, dotenv


dotenv.load_dotenv('.env')

# Конфигурация
TOKEN = os.getenv('TOKEN')
BASE_URL = os.getenv('BASE_URL')
TARGET_URL = os.getenv('TARGET_URL')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')