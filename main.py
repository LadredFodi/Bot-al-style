from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
import time
import logging
import os
import shutil

from utils import login, navigate_to_target_page, handle_category_selection
from config import USERNAME, PASSWORD, STANDARD_DELAY, HEADLESS_MODE, PROFILE_DIR, PROFILE_NAME

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


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


def ensure_profile_dir():
    """Создание и проверка директории профиля"""
    profile_path = os.path.join(os.getcwd(), PROFILE_DIR, PROFILE_NAME)
    if not os.path.exists(profile_path):
        os.makedirs(profile_path, exist_ok=True)
        logging.info(f"Создана директория профиля: {profile_path}")
    return profile_path


def backup_profile():
    """Создание резервной копии профиля"""
    profile_path = os.path.join(os.getcwd(), PROFILE_DIR, PROFILE_NAME)
    backup_path = os.path.join(os.getcwd(), PROFILE_DIR, f"{PROFILE_NAME}_backup")
    
    if os.path.exists(profile_path):
        try:
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            shutil.copytree(profile_path, backup_path)
            logging.info("Создана резервная копия профиля")
        except Exception as e:
            logging.error(f"Ошибка при создании резервной копии профиля: {e}")


def restore_profile_from_backup():
    """Восстановление профиля из резервной копии"""
    profile_path = os.path.join(os.getcwd(), PROFILE_DIR, PROFILE_NAME)
    backup_path = os.path.join(os.getcwd(), PROFILE_DIR, f"{PROFILE_NAME}_backup")
    
    if os.path.exists(backup_path):
        try:
            if os.path.exists(profile_path):
                shutil.rmtree(profile_path)
            shutil.copytree(backup_path, profile_path)
            logging.info("Профиль восстановлен из резервной копии")
            return True
        except Exception as e:
            logging.error(f"Ошибка при восстановлении профиля: {e}")
    return False


def initialize_driver():
    """Инициализация и настройка Chrome WebDriver с сохранением профиля"""
    chrome_options = Options()
    
    # Настройка профиля
    profile_path = ensure_profile_dir()
    chrome_options.add_argument(f"user-data-dir={profile_path}")
    
    if HEADLESS_MODE:
        logging.info("Запуск в headless режиме")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
    else:
        logging.info("Запуск в обычном режиме (с видимым браузером)")
        chrome_options.add_argument("--start-maximized")
        
    # Оптимизация производительности
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
    chrome_options.add_argument("--disable-javascript-harmony-shipping")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-component-extensions-with-background-pages")
    
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
        "profile.default_content_setting_values.geolocation": 2,
        "profile.default_content_settings.popups": 2, 
        "profile.default_content_setting_values.automatic_downloads": 1,
        "profile.default_content_settings.state.flash": 0,
        "profile.managed_default_content_settings.javascript": 1, 
        "profile.managed_default_content_settings.cookies": 1,  
        "profile.default_content_settings.cookies": 1
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
        wait = WebDriverWait(driver, 20)
    else:
        wait = WebDriverWait(driver, 15)
    return driver, wait


def main():
    """Основной поток выполнения"""
    backup_profile()
    
    try:
        driver, wait = initialize_driver()
        
        if not test_headless_compatibility(driver):
            logging.error("Headless режим работает некорректно, завершаем работу")
            driver.quit()
            return
            
    except WebDriverException as wd_error:
        logging.error(f"Ошибка инициализации WebDriver: {wd_error}")
        if restore_profile_from_backup():
            logging.info("Профиль восстановлен, пробуем снова")
            try:
                driver, wait = initialize_driver()
            except Exception as e:
                logging.error(f"Не удалось инициализировать драйвер после восстановления: {e}")
                return
        else:
            logging.error("Проверьте, установлен ли ChromeDriver и Chrome браузер")
            return
    except Exception as init_error:
        logging.error(f"Критическая ошибка инициализации: {init_error}")
        return
        
    try:
        while True:
            try:
                if not driver.get_cookie('PHPSESSID'):
                    if not login(driver, wait, USERNAME, PASSWORD):
                        logging.error("Не удалось авторизоваться, завершаем работу")
                        break
                else:
                    logging.info("Используем существующую сессию")
                    
                navigate_to_target_page(driver, wait)
                time.sleep(STANDARD_DELAY)
                handle_category_selection(driver, wait)
                
            except Exception as main_error:
                logging.error(f"Произошла основная ошибка: {main_error}")
                try:
                    driver.save_screenshot('error_screenshot.png')
                    logging.info("Скриншот ошибки сохранен как 'error_screenshot.png'")
                except:
                    logging.error("Не удалось сохранить скриншот ошибки")
                    
    finally:
        try:
            driver.quit()
            logging.info("Браузер закрыт")
        except:
            logging.error("Ошибка при закрытии браузера")


if __name__ == "__main__":
    main()