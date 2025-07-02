from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
import requests, logging
import json

from config import TOKEN, TARGET_URL, CLICK_DELAY, SHORT_DELAY, MEDIUM_DELAY, STANDARD_DELAY, PAGE_LOAD_DELAY, LONG_DELAY, HEADLESS_MODE, HEADLESS_EXTRA_DELAY, HEADLESS_PAGE_LOAD, SUBCATEGORIES_DATA_ID, CATEGORY_HIERARCHY




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
            logging.debug(f"{element_name} не отображается")
            return False
            
        if not element.is_enabled():
            logging.debug(f"{element_name} отключен")
            return False
        
        dismiss_overlays(driver)
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", element)
        time.sleep(get_delay(SHORT_DELAY))
        
        try:
            driver.execute_script("arguments[0].click();", element)
            logging.debug(f"Успешный клик по {element_name} (JavaScript)")
            return True
        except Exception as e1:
            logging.debug(f"JS клик не сработал для {element_name}: {e1}")
            
            try:
                element.click()
                logging.debug(f"Успешный клик по {element_name} (обычный)")
                return True
            except Exception as e2:
                logging.debug(f"Обычный клик не сработал для {element_name}: {e2}")
                
                try:
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(driver)
                    actions.move_to_element(element).click().perform()
                    logging.debug(f"Успешный клик по {element_name} (ActionChains)")
                    return True
                except Exception as e3:
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
    try:
        driver.get(TARGET_URL)
        time.sleep(SHORT_DELAY)
        
        # Проверяем, авторизованы ли мы уже
        if "login" not in driver.current_url:
            logging.info("Уже авторизованы, используем существующую сессию")
            return True
            
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
    except Exception as e:
        logging.error(f"Ошибка при попытке входа: {e}")
        return False


def navigate_to_target_page(driver, wait):
    """Переход на целевую страницу и обработка начальных всплывающих окон"""
    driver.get(TARGET_URL)
    logging.info("Перешли на целевую страницу")
    
    if HEADLESS_MODE:
        time.sleep(HEADLESS_PAGE_LOAD)
        logging.info("Дополнительное ожидание для headless режима")
    
    try:
        # Пытаемся закрыть все модальные окна одновременно
        driver.execute_script("""
            var modals = document.querySelectorAll('#notification_modal .close, .modal .close');
            modals.forEach(function(modal) { modal.click(); });
        """)
        logging.info("Закрыли модальные окна")
    except Exception as e:
        logging.debug(f"Ошибка при закрытии модальных окон: {e}")


def expand_category(driver, wait, category_id):
    """Разворачивает категорию по её ID с проверками"""
    try:
        short_wait = WebDriverWait(driver, 2)
        category_selector = f"a[data-category='{category_id}']"
        
        try:
            category_button = short_wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, category_selector))
            )
        except:
            logging.info(f"Категория с ID {category_id} не найдена на странице - пропускаем")
            return False
            
        category_name = category_button.text.strip()
        
        is_expanded = category_button.get_attribute('aria-expanded') == 'true'
        if is_expanded:
            logging.info(f"Категория '{category_name}' (ID: {category_id}) уже развернута")
            return True
            
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", category_button)
        time.sleep(SHORT_DELAY)
        
        if safe_robust_click(driver, wait, category_button, f"категория {category_name} (ID: {category_id})"):
            logging.info(f"Успешно развернута категория '{category_name}' (ID: {category_id})")
            time.sleep(SHORT_DELAY)
            return True
        else:
            logging.info(f"Не удалось развернуть категорию '{category_name}' (ID: {category_id}) - пропускаем")
            return False
            
    except Exception as e:
        logging.info(f"Пропускаем категорию {category_id}: {str(e)}")
        return False


def expand_category_level(driver, wait, category_ids):
    """Разворачивает все категории одного уровня"""
    results = []
    
    # Получаем все категории сразу
    category_elements = {}
    for category_id in category_ids:
        try:
            category_selector = f"a[data-category='{category_id}']"
            element = driver.find_element(By.CSS_SELECTOR, category_selector)
            if element.is_displayed() and element.is_enabled():
                category_elements[category_id] = element
        except:
            logging.info(f"Категория с ID {category_id} не найдена на странице - пропускаем")
            continue
    
    # Разворачиваем найденные категории
    for category_id, element in category_elements.items():
        try:
            is_expanded = element.get_attribute('aria-expanded') == 'true'
            if is_expanded:
                logging.info(f"Категория '{element.text.strip()}' (ID: {category_id}) уже развернута")
                results.append(True)
                continue
                
            # Быстрый скролл к элементу
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", element)
            time.sleep(SHORT_DELAY)
            
            # Используем JavaScript клик как самый быстрый
            driver.execute_script("arguments[0].click();", element)
            logging.info(f"Успешно развернута категория '{element.text.strip()}' (ID: {category_id})")
            results.append(True)
            time.sleep(SHORT_DELAY)
            
        except Exception as e:
            logging.debug(f"Ошибка при развертывании категории {category_id}: {e}")
            results.append(False)
            
    return any(results)


def process_cart(driver, wait):
    """Обработка страницы корзины"""
    try:
        driver.get('https://api.al-style.kz/cart')
        logging.info("Перешли на страницу корзины")
        time.sleep(STANDARD_DELAY)
        
        short_wait = WebDriverWait(driver, 2)
        try:
            modal_close = short_wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#notification_modal .close"))
            )
            modal_close.click()
            logging.info("Закрыли модальное окно")
        except:
            logging.info("Модальное окно не найдено")

        cart_items = get_cart_articles()
        if not cart_items:
            logging.info("Корзина пуста - завершаем работу")
            return False
            
        submit_button = None
        selectors = [
            "button.btn.btn-success.btn-lg[type='submit']",
            "button.btn-success[type='submit']",
            "button[type='submit'].btn-success",
            "button[data-bs-original-title*='Резерв товара']",
            "button.btn-lg[type='submit']"
        ]
        
        for selector in selectors:
            try:
                logging.info(f"Пробуем найти кнопку по селектору: {selector}")
                submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                if submit_button and submit_button.is_displayed():
                    logging.info(f"Кнопка найдена по селектору: {selector}")
                    break
            except:
                continue
                
        if not submit_button:
            try:
                submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Отправить')]")
                logging.info("Кнопка найдена по тексту 'Отправить'")
            except:
                pass
                
        if not submit_button:
            logging.info("Не удалось найти кнопку.")
            cart_html = driver.find_element(By.TAG_NAME, 'body').get_attribute('innerHTML')
            return False
            
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", submit_button)
        time.sleep(SHORT_DELAY)
        
        try:
            submit_button.click()
            logging.info("Успешно отправили заказ (обычный клик)")
            return True
        except:
            try:
                driver.execute_script("arguments[0].click();", submit_button)
                logging.info("Успешно отправили заказ (JavaScript клик)")
                return True
            except:
                try:
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(driver)
                    actions.move_to_element(submit_button).click().perform()
                    logging.info("Успешно отправили заказ (ActionChains клик)")
                    return True
                except Exception as e:
                    logging.error(f"Все способы клика не сработали: {str(e)}")
                    return False
                    
    except Exception as e:
        logging.error(f"Ошибка при обработке корзины: {str(e)}")
        return False


def handle_category_selection(driver, wait):
    """Обработка выбора категорий по уровням с последующей обработкой товаров"""
    try:
        level1_success = expand_category_level(driver, wait, CATEGORY_HIERARCHY["level1"])
        if not level1_success:
            logging.info("Категории первого уровня не найдены - переходим к поиску markdown-ссылок")
        else:
            time.sleep(SHORT_DELAY)
            
            level2_success = expand_category_level(driver, wait, CATEGORY_HIERARCHY["level2"])
            if not level2_success:
                logging.info("Категории второго уровня не найдены - переходим к поиску markdown-ссылок")
            else:
                time.sleep(SHORT_DELAY)
                
                level3_success = expand_category_level(driver, wait, CATEGORY_HIERARCHY["level3"])
                if not level3_success:
                    logging.info("Категории третьего уровня не найдены - переходим к поиску markdown-ссылок")
                
                time.sleep(SHORT_DELAY)
        
        try:
            short_wait = WebDriverWait(driver, 2)
            markdown_links = short_wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'markdown-link'))
            )
            logging.info(f"Найдено {len(markdown_links)} markdown-ссылок")
            click_all_markdown_links(driver, wait, driver)
            time.sleep(SHORT_DELAY)
            click_all_plus_buttons(driver, wait)
        except:
            logging.info("Markdown-ссылки не найдены на текущей странице")
            
        time.sleep(STANDARD_DELAY)
        # ================================
        process_cart(driver, wait)
        # ================================
    except Exception as e:
        logging.error(f"Ошибка при обработке категорий: {str(e)}")


def click_all_markdown_links(driver, wait, container):
    """Кликнуть каждую вторую ссылку markdown"""
    try:
        # Пробуем найти все ссылки сразу
        markdown_links = container.find_elements(By.CLASS_NAME, 'markdown-link')
        if not markdown_links:
            markdown_links = container.find_elements(By.CSS_SELECTOR, "a.markdown-link")
            
        logging.info(f"Найдено {len(markdown_links)} ссылок markdown")
        

        
        # Кликаем по отфильтрованным ссылкам
        for idx, link in enumerate(markdown_links, 1):
            if idx % 3 == 1 or idx == 1:
                try:
                    # Быстрый скролл и клик
                    driver.execute_script("""
                        arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});
                        arguments[0].click();
                        """, link)
                    logging.info(f"Успешно кликнули на markdown-link {idx}")
                    time.sleep(CLICK_DELAY)
                except Exception as e:
                    logging.error(f"Ошибка при клике на markdown-link {idx}: {e}")
                    
    except Exception as e:
        logging.error(f"Ошибка при поиске markdown-ссылок: {e}")


def click_all_plus_buttons(driver, wait):
    """Кликнуть все кнопки 'плюс' для товаров со скидкой согласно доступному количеству"""
    cart_articles = get_cart_articles()
    
    # Получаем все строки товаров сразу
    product_rows = wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, "tr.product-item.markdown-item")
    ))
    logging.info(f"Найдено {len(product_rows)} строк с товарами со скидкой")
    
    # Подготавливаем данные для всех товаров
    products_data = []
    for row in product_rows:
        try:
            try:
                article_element = row.find_element(By.CSS_SELECTOR, "td.text-center.article.up-arrow span span")
                article = article_element.text.strip()
            except:
                article_element = row.find_element(By.CSS_SELECTOR, "td.text-center.sku span")
                article = article_element.text.strip()
            
            if article in cart_articles:
                continue
            
            quantity_element = row.find_element(By.CSS_SELECTOR, "td.text-end.quantity span.text-nowrap.all-transition.remains div.faq-group span")
            quantity = int(quantity_element.text.strip())
            
            plus_button = row.find_element(By.CSS_SELECTOR, "td.text-center div.cart-control i.cart-control-btn.cart-plus.icon-plus")
            
            products_data.append({
                'row': row,
                'article': article,
                'quantity': quantity,
                'plus_button': plus_button
            })
        except Exception as e:
            logging.error(f"Ошибка при подготовке данных товара: {e}")
            continue
    
    for idx, product in enumerate(products_data, 1):
        try:
            logging.info(f"Товар со скидкой {idx} (артикул: {product['article']}) имеет количество: {product['quantity']}")
            
            # Быстрый скролл к строке
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", product['row'])
            time.sleep(SHORT_DELAY)
            
            # Кликаем нужное количество раз
            for click_num in range(product['quantity']):
                driver.execute_script("arguments[0].click();", product['plus_button'])
                logging.info(f"Кликнули на кнопку плюс для товара со скидкой {idx} ({click_num+1}/{product['quantity']})")
                time.sleep(SHORT_DELAY)
            
        except Exception as e:
            logging.error(f"Не удалось обработать строку товара со скидкой {idx}: {e}")
            continue


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
            logging.debug(f"Скрыто {overlays_found} перекрывающих элементов")
            
    except Exception as e:
        logging.debug(f"Не удалось скрыть оверлей: {e}")


def find_subcategories_by_data_id(driver, wait, data_id):
    """Поиск контейнера subcategories по data-id"""
    try:
        element_with_data_id = wait.until(
            EC.presence_of_element_located((By.XPATH, f"//*[@data-id='{data_id}']"))
        )
        logging.info(f"Найден элемент с data-id='{data_id}'")
        
        try:
            subcategories_container = element_with_data_id.find_element(
                By.XPATH, "./following-sibling::*[contains(@class, 'sub-categories')]"
            )
            logging.info("Найден контейнер subcategories через following-sibling")
            return subcategories_container
        except:
            pass
        try:
            parent = element_with_data_id.find_element(By.XPATH, "./..")
            subcategories_container = parent.find_element(
                By.XPATH, ".//*[contains(@class, 'sub-categories')]"
            )
            logging.info("Найден контейнер subcategories через родительский элемент")
            return subcategories_container
        except:
            pass
        
        try:
            subcategories_container = driver.find_element(
                By.XPATH, f"//*[contains(@class, 'children{data_id}')]"
            )
            logging.info(f"Найден контейнер subcategories с классом children{data_id}")
            return subcategories_container
        except:
            pass
        
        logging.warning(f"Специальный контейнер subcategories не найден, возвращаем элемент с data-id='{data_id}'")
        return element_with_data_id
        
    except Exception as e:
        logging.error(f"Не удалось найти элемент с data-id='{data_id}': {e}")
        return None