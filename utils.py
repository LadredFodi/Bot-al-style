from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import requests, logging
import json

from config import TOKEN, TARGET_URL, CLICK_DELAY, SHORT_DELAY, MEDIUM_DELAY, STANDARD_DELAY, PAGE_LOAD_DELAY, LONG_DELAY, ENABLE_DEBUG_LOGS, HEADLESS_MODE, HEADLESS_EXTRA_DELAY, HEADLESS_PAGE_LOAD


def debug_log(message):
    """Функция для контролируемого вывода debug логов"""
    if ENABLE_DEBUG_LOGS:
        logging.debug(message)


def get_delay(base_delay):
    """Получить задержку с учетом headless режима"""
    if HEADLESS_MODE:
        return base_delay + HEADLESS_EXTRA_DELAY
    return base_delay


def get_cart_articles():
    """Получить список артикулов товаров, уже находящихся в корзине"""
    try:
        request = requests.get(f'https://api.al-style.kz/cart-api/get?access-token={TOKEN}')
        data = json.loads(request.text)
        articles = []
        
        for i, j in data['data'].items():
            articles.append(str(j['article']) + 'y')
        
        logging.info(f"Найдено {len(articles)} товаров в корзине: {articles}")
        return articles
    except Exception as e:
        logging.error(f"Ошибка при получении товаров из корзины: {e}")
        return []


def safe_click(wait, xpath, timeout=10):
    """Безопасный клик по элементу, если он существует и доступен для клика"""
    try:
        element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        element.click()
        return True
    except Exception as e:
        logging.error(f"Не удалось кликнуть на элемент {xpath}: {e}")
        return False


def safe_robust_click(driver, wait, element, element_name="элемент"):
    """Усиленная функция безопасного клика с множественными попытками"""
    try:
        if not element.is_displayed():
            debug_log(f"{element_name} не отображается")
            return False
            
        if not element.is_enabled():
            debug_log(f"{element_name} отключен")
            return False
        
        dismiss_overlays(driver)
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
        time.sleep(get_delay(MEDIUM_DELAY))
        
        try:
            wait.until(EC.element_to_be_clickable(element))
            element.click()
            debug_log(f"Успешный клик по {element_name} (обычный)")
            return True
        except Exception as e1:
            debug_log(f"Обычный клик не сработал для {element_name}: {e1}")
            
            try:
                driver.execute_script("arguments[0].click();", element)
                debug_log(f"Успешный клик по {element_name} (JavaScript)")
                return True
            except Exception as e2:
                debug_log(f"JS клик не сработал для {element_name}: {e2}")
                
                try:
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(driver)
                    actions.move_to_element(element).click().perform()
                    debug_log(f"Успешный клик по {element_name} (ActionChains)")
                    return True
                except Exception as e3:
                    debug_log(f"ActionChains клик не сработал для {element_name}: {e3}")
                    
                    try:
                        actions = ActionChains(driver)
                        actions.move_to_element_with_offset(element, 0, 0).click().perform()
                        debug_log(f"Успешный клик по {element_name} (центр элемента)")
                        return True
                    except Exception as e4:
                        logging.warning(f"Все способы клика не сработали для {element_name}")
                        return False
                        
    except Exception as e:
        logging.error(f"Критическая ошибка при клике по {element_name}: {e}")
        return False


def safe_find(wait, xpath, timeout=10):
    """Безопасный поиск элемента, если он существует"""
    try:
        return wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    except Exception as e:
        logging.error(f"Элемент не найден {xpath}: {e}")
        return None


def switch_to_new_tab(driver, wait, main_window):
    """Переключиться на новую вкладку и вернуться на основную после обработки"""
    wait.until(lambda d: len(d.window_handles) > 1)
    new_window = [window for window in driver.window_handles if window != main_window][0]
    driver.switch_to.window(new_window)
    logging.info("Переключились на новую вкладку")
    
    try:
        process_markdown_links(driver, wait)
    finally:
        driver.close()
        driver.switch_to.window(main_window)
        logging.info("Вернулись на основную вкладку")


def process_markdown_links(driver, wait):
    """Найти и кликнуть все кнопки markdown-link в текущей вкладке"""
    time.sleep(PAGE_LOAD_DELAY)
    
    markdown_links = driver.find_elements(By.CSS_SELECTOR, "a.markdown-link")
    if not markdown_links:
        markdown_links = driver.find_elements(By.XPATH, "//a[contains(@class, 'markdown-link')]")
    
    logging.info(f"Найдено {len(markdown_links)} кнопок markdown-link")
    
    for idx, link in enumerate(markdown_links, 1):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
            time.sleep(CLICK_DELAY)
            link.click()
            logging.info(f"Кликнули на кнопку markdown-link {idx}")
            time.sleep(CLICK_DELAY)
        except Exception as e:
            logging.error(f"Не удалось кликнуть на кнопку markdown-link {idx}: {e}")


def login(driver, wait, username, password):
    """Выполнение операции входа в систему с проверкой URL после авторизации"""
    login_url = "https://api.al-style.kz/site/login"
    driver.get(login_url)
    
    if driver.current_url != login_url:
        logging.info("Уже авторизованы, пропускаем вход")
        return True
    
    email_field = safe_find(wait, '//*[@id="loginform-username"]')
    password_field = safe_find(wait, '//*[@id="loginform-password"]')
    
    if email_field and password_field:
        email_field.send_keys(username)
        password_field.send_keys(password)
        
        if safe_click(wait, '//button[@type="submit" and contains(text(), "Войти на портал")]'):
            logging.info("Форма входа отправлена")
            
            try:
                wait.until(lambda driver: driver.current_url != login_url)
                logging.info("Авторизация прошла успешно")
                return True
            except Exception as e:
                logging.error("Не удалось авторизоваться: остались на странице входа")
                if "Неверные учетные данные" in driver.page_source:
                    logging.error("Причина: неверные учетные данные")
                return False
    
    logging.error("Не удалось выполнить вход")
    return False


def navigate_to_target_page(driver, wait):
    """Переход на целевую страницу и обработка начальных всплывающих окон"""
    driver.get(TARGET_URL)
    logging.info("Перешли на целевую страницу")
    
    if HEADLESS_MODE:
        time.sleep(HEADLESS_PAGE_LOAD)
        logging.info("Дополнительное ожидание для headless режима")
    
    if safe_click(wait, '//*[@id="notification_modal"]/div/div/div[1]/button'):
        logging.info("Закрыли модальное окно уведомления")

    time.sleep(get_delay(LONG_DELAY))
    
    if safe_click(wait, '/html/body/div[3]/div/div/div/div[1]/a[5]'):
        logging.info("Закрыли дополнительное всплывающее окно")


def expand_all_categories(driver, wait, subcategories):
    """Развернуть все кнопки категорий с улучшенной обработкой ошибок"""
    category_buttons = subcategories.find_elements(By.XPATH, ".//*[contains(@class, 'collapsed') or contains(@class, 'subcategory')]")
    logging.info(f"Найдено {len(category_buttons)} кнопок категорий для развертывания")
    
    successful_clicks = 0
    
    for idx, button in enumerate(category_buttons, 1):
        try:
            if safe_robust_click(driver, wait, button, f"кнопка категории {idx}"):
                successful_clicks += 1
                logging.info(f"Успешно развернули кнопку категории {idx}")
                time.sleep(CLICK_DELAY)
            else:
                logging.warning(f"Не удалось развернуть кнопку категории {idx}")
                
        except Exception as e:
            logging.error(f"Критическая ошибка при обработке кнопки категории {idx}: {e}")
    
    logging.info(f"Успешно развернуто {successful_clicks} из {len(category_buttons)} кнопок категорий")


def click_all_markdown_links(driver, wait, subcategories):
    """Кликнуть каждую вторую ссылку markdown"""
    markdown_links = subcategories.find_elements(By.CLASS_NAME, 'markdown-link')
    logging.info(f"Найдено {len(markdown_links)} ссылок markdown")
    
    for idx, link in enumerate(markdown_links, 1):
        if idx % 3 == 1 or idx == 1:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                time.sleep(MEDIUM_DELAY)
                link.click()
                logging.info(f"Кликнули на markdown-link {idx}")
                time.sleep(CLICK_DELAY)
            except Exception as e:
                logging.error(f"Не удалось кликнуть на markdown-link {idx}: {e}")


def click_all_plus_buttons(driver, wait):
    """Кликнуть все кнопки 'плюс' для товаров со скидкой согласно доступному количеству"""
    cart_articles = get_cart_articles()
    
    product_rows = wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, "tr.product-item.markdown-item")
    ))
    logging.info(f"Найдено {len(product_rows)} строк с товарами со скидкой")
    
    for idx, row in enumerate(product_rows, 1):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", row)
            time.sleep(MEDIUM_DELAY)
            
            try:
                article_element = row.find_element(By.CSS_SELECTOR, "td.text-center.article.up-arrow span span")
                article = article_element.text.strip()
            except:
                article_element = row.find_element(By.CSS_SELECTOR, "td.text-center.sku span")
                article = article_element.text.strip()
            
            logging.debug(f"Артикул: {article}, Товары в корзине: {cart_articles}")
            if article in cart_articles:
                logging.info(f"Товар со скидкой {idx} с артикулом {article} уже в корзине - пропускаем")
                continue
            
            quantity_element = row.find_element(By.CSS_SELECTOR, "td.text-end.quantity span.text-nowrap.all-transition.remains div.faq-group span")
            quantity_text = quantity_element.text.strip()
            
            try:
                quantity = int(quantity_text)
                logging.info(f"Товар со скидкой {idx} (артикул: {article}) имеет количество: {quantity}")
            except ValueError:
                logging.warning(f"Не удалось распознать количество для товара со скидкой {idx}, используем значение по умолчанию 1")
                quantity = 1
            

            time.sleep(STANDARD_DELAY)
            plus_button = row.find_element(By.CSS_SELECTOR, "td.text-center div.cart-control i.cart-control-btn.cart-plus.icon-plus")
            
            for click_num in range(quantity):
                plus_button.click()
                logging.info(f"Кликнули на кнопку плюс для товара со скидкой {idx} ({click_num+1}/{quantity})")
                time.sleep(SHORT_DELAY)
            
        except Exception as e:
            logging.error(f"Не удалось обработать строку товара со скидкой {idx}: {e}")


def dismiss_overlays(driver):
    """Улучшенная функция для скрытия перекрывающих элементов"""
    try:
        overlay_selectors = [
            "//*[contains(@class,'overlay')]",
            "//*[contains(@class,'modal')]", 
            "//*[contains(@class,'popup')]",
            "//*[contains(@class,'backdrop')]",
            "//*[contains(@class,'mask')]",
            "//*[contains(@style,'position: fixed')]",
            "//*[contains(@style,'z-index')][@style[contains(.,'999')]]"
        ]
        
        overlays_found = 0
        for selector in overlay_selectors:
            overlays = driver.find_elements(By.XPATH, selector)
            for overlay in overlays:
                if overlay.is_displayed():
                    driver.execute_script("arguments[0].style.display='none'", overlay)
                    driver.execute_script("arguments[0].style.visibility='hidden'", overlay)
                    driver.execute_script("arguments[0].remove()", overlay)
                    overlays_found += 1
        
        if overlays_found > 0:
            debug_log(f"Скрыто {overlays_found} перекрывающих элементов")
            
    except Exception as e:
        debug_log(f"Не удалось скрыть оверлей: {e}")


def handle_category_selection(driver, wait):
    """Обработка выбора категории и подкатегории с разделенной логикой"""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            dismiss_overlays(driver)
            time.sleep(STANDARD_DELAY)
            
            category_button = wait.until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div[2]/div[3]/div[10]/a[1]'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", category_button)
            
            try:
                category_button.click()
            except:
                driver.execute_script("arguments[0].click();", category_button)
            
            logging.info("Кликнули на основную кнопку категории")
            break
        except Exception as e:
            logging.warning(f"Попытка {attempt + 1} из {max_attempts} не удалась: {e}")
            if attempt == max_attempts - 1:
                raise
            time.sleep(PAGE_LOAD_DELAY)
    
    time.sleep(STANDARD_DELAY)
    
    subcategories = safe_find(wait, "/html/body/div[4]/div[2]/div[3]/div[13]")
    if subcategories:
        logging.info("Найден контейнер подкатегорий")
        expand_all_categories(driver, wait, subcategories)
        time.sleep(STANDARD_DELAY)
        click_all_markdown_links(driver, wait, subcategories)
        time.sleep(STANDARD_DELAY)
        click_all_plus_buttons(driver, wait)