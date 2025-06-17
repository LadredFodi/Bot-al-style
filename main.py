from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import time
import logging

from utils import login, navigate_to_target_page, handle_category_selection
from config import USERNAME, PASSWORD

logging.basicConfig(level=logging.INFO)


def initialize_driver():
    """Инициализация и настройка Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--headless")  # Режим без графического интерфейса
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)
    return driver, wait


def main():
    """Основной поток выполнения"""
    while True:
        driver, wait = initialize_driver()
        
        try:
            # Пытаемся авторизоваться
            if not login(driver, wait, USERNAME, PASSWORD):
                logging.error("Не удалось авторизоваться, завершаем работу")
                break
                
            # Продолжаем работу только при успешной авторизации
            navigate_to_target_page(driver, wait)
            time.sleep(1)
            handle_category_selection(driver, wait)
            
        except Exception as main_error:
            logging.error(f"Произошла основная ошибка: {main_error}")
            driver.save_screenshot('error_screenshot.png')
            logging.info("Скриншот ошибки сохранен как 'error_screenshot.png'")
            
        finally:
            driver.quit()
            logging.info("Браузер закрыт")


if __name__ == "__main__":
    main()