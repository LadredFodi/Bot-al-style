from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
import time
import logging

from utils import login, navigate_to_target_page, handle_category_selection
from config import USERNAME, PASSWORD, STANDARD_DELAY, HEADLESS_MODE

logging.basicConfig(level=logging.INFO)


def test_headless_compatibility(driver):
    """Проверка совместимости headless режима"""
    try:
        driver.get("https://www.google.com")
        logging.info("✓ Headless режим: успешная загрузка тестовой страницы")
        
        size = driver.get_window_size()
        logging.info(f"✓ Headless режим: размер окна {size['width']}x{size['height']}")
        
        result = driver.execute_script("return navigator.userAgent")
        logging.info(f"✓ Headless режим: JavaScript работает, User-Agent: {result[:50]}...")
        
        return True
    except Exception as e:
        logging.error(f"✗ Headless режим: тест не пройден - {e}")
        return False


def initialize_driver():
    """Инициализация и настройка Chrome WebDriver"""
    chrome_options = Options()
    
    # Условные настройки в зависимости от режима
    if HEADLESS_MODE:
        logging.info("🔧 Запуск в headless режиме")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
    else:
        logging.info("🔧 Запуск в обычном режиме (с видимым браузером)")
        chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-dev-tools")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--enable-features=NetworkService,NetworkServiceLogging")
    chrome_options.add_argument("--force-color-profile=srgb")
    chrome_options.add_argument("--metrics-recording-only")
    chrome_options.add_argument("--use-mock-keychain")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("detach", True)
        
    prefs = {
        
        "profile.managed_default_content_settings.images": 2,
        
        "profile.default_content_setting_values.notifications": 2,
        
        "profile.managed_default_content_settings.media_stream": 2,
        
        "profile.managed_default_content_settings.plugins": 2,
        
        "profile.default_content_setting_values.media_stream_mic": 2,
        "profile.default_content_setting_values.media_stream_camera": 2,
        
        "profile.default_content_setting_values.geolocation": 2
    }
    
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
    
    if HEADLESS_MODE:
        driver.set_window_size(1920, 1080)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        wait = WebDriverWait(driver, 30)
    else:
        wait = WebDriverWait(driver, 20)
    return driver, wait


def main():
    """Основной поток выполнения"""
    while True:
        try:
            driver, wait = initialize_driver()
            
            if not test_headless_compatibility(driver):
                logging.error("Headless режим работает некорректно, завершаем работу")
                driver.quit()
                break
            
        except WebDriverException as wd_error:
            logging.error(f"Ошибка инициализации WebDriver: {wd_error}")
            logging.error("Проверьте, установлен ли ChromeDriver и Chrome браузер")
            break
        except Exception as init_error:
            logging.error(f"Критическая ошибка инициализации: {init_error}")
            break
        
        try:
            # Пытаемся авторизоваться
            if not login(driver, wait, USERNAME, PASSWORD):
                logging.error("Не удалось авторизоваться, завершаем работу")
                break
                
            # Продолжаем работу только при успешной авторизации
            navigate_to_target_page(driver, wait)
            time.sleep(STANDARD_DELAY)
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