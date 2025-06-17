import os
import re
import time
import json
import random
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, date
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, WebDriverException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from selenium.webdriver.remote.webdriver import WebDriver
from dataclasses import dataclass

logger = logging.getLogger("OzonParser")

REMOTE_WEBDRIVER_URL = os.environ.get("REMOTE_WEBDRIVER_URL", "http://selenium:4444/wd/hub")

@dataclass
class OzonConfig:
    base_url: str = "https://www.ozon.ru/"
    max_reviews: int = 500
    max_pages: int = 20
    timeout_seconds: int = 30
    max_empty_streak: int = 3
    scroll_step: int = 1000
    scroll_pause: float = 0.2
    page_load_timeout: int = 10

class OzonSelectors:
    REVIEW_ELEMENTS = "//div[@data-review-uuid]"
    
    AUTHOR_NAME = ".//span[contains(@class, 'xp5_30')]"
    REVIEW_TEXT = ".//span[contains(@class, 'q9q_30')]"
    REVIEW_DATE = ".//div[contains(@class, 'q6q_30')]"
    REVIEW_RATING = ".//div[contains(@class, 'a5d01-a0')]//svg"
    
    NEXT_BUTTON = "//a[.//div[contains(text(), 'Дальше')]]"
    
    CAPTCHA_INDICATORS = [
        "//div[contains(@class, 'captcha')]",
        "//iframe[contains(@src, 'captcha')]"
    ]
    
    BLOCK_INDICATORS = ["//*[contains(text(), 'Доступ ограничен')]"]
    
    REVIEWS_WIDGET = "div[data-widget='webListReviews']"


class WebDriverManager:
    def __init__(self):
        self.driver = None

    def __enter__(self) -> WebDriver:
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        try:
            self.driver = webdriver.Remote(
                command_executor=REMOTE_WEBDRIVER_URL,
                options=chrome_options
            )
            self._apply_stealth()
            return self.driver
        except WebDriverException as e:
            logger.error(f"Не удалось создать WebDriver: {e}", exc_info=True)
            raise RuntimeError(f"Не удалось инициализировать WebDriver: {e}") from e

    def _apply_stealth(self):
        try:
            stealth(self.driver,
                languages=["ru-RU", "ru"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
        except Exception as e_stealth:
            logger.warning(f"Stealth не сработал, применяем базовую маскировку: {e_stealth}")
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU', 'ru']})")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Ошибка при закрытии драйвера: {e}")


class OzonParser:
    
    def __init__(self, base_url="https://www.ozon.ru/"):
        self.config = OzonConfig(base_url=base_url)
        self.selectors = OzonSelectors()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": self.config.base_url,
            "Referer": self.config.base_url,
        }

    
    def parse_reviews(self, product_id: str, max_reviews: int = 500) -> List[Dict[str, Any]]:
  
        if not self.is_valid_product_id(product_id):
            logger.error(f"Неверный формат ID товара: {product_id}")
            return []
        
        logger.info(f"Начало парсинга отзывов для товара с ID: {product_id}")
        
        product_info = {
            "id": product_id,
            "name": f"Товар с OZON {product_id}",
            "brand": "",
            "price": 0,
            "rating": 0,
            "image_url": "",
            "url": f"https://www.ozon.ru/product/{product_id}/",
            "source": "ozon"
        }
        
        reviews_url = f"https://www.ozon.ru/product/{product_id}/reviews/"
        
        try:
            with WebDriverManager() as driver:
                return self._parse_reviews_with_selenium(driver, reviews_url, max_reviews, product_info)
        except (WebDriverException, RuntimeError) as e:
            logger.error(f"Критическая ошибка WebDriver при парсинге: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Непредвиденная ошибка на верхнем уровне парсинга: {e}", exc_info=True)
        
        return []
    
    def get_product_info(self, product_id: str) -> Dict[str, Any]:
        return {
            "id": product_id,
            "name": f"Товар с OZON {product_id}",
            "brand": "",
            "price": 0,
            "rating": 0,
            "image_url": "",
            "url": f"https://www.ozon.ru/product/{product_id}/",
            "source": "ozon"
        }
    
    def _parse_reviews_with_selenium(self, driver: WebDriver, url: str, max_reviews: int, product_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info(f"Открываем страницу отзывов: {url}")
        driver.get(url)
        time.sleep(1) 

        self._close_popups(driver)

        if not self._handle_initial_checks(driver):
            return []

        return self._extract_reviews_from_all_pages(driver, max_reviews, product_info)

    def _close_popups(self, driver: WebDriver):
        try:
            close_buttons = driver.find_elements(By.XPATH, "//*[contains(@class, 'close') or contains(text(), 'Закрыть') or contains(text(), 'Понятно') or @aria-label='Закрыть модальное окно']")
            for button in close_buttons:
                if button.is_displayed():
                    button.click()
                    time.sleep(0.5)
        except Exception:
            pass 

    def _handle_initial_checks(self, driver: WebDriver) -> bool:
        if self._has_captcha(driver):
            logger.warning("Обнаружена CAPTCHA. Завершаем парсинг.")
            return False
            
        if self._has_blocked_access(driver):
            logger.warning("Доступ ограничен. Завершаем парсинг.")
            return False
        
        if not self._has_reviews(driver):
            logger.warning("На странице не найдены отзывы. Завершаем парсинг.")
            return False
        
        return True

    def _extract_reviews_from_all_pages(self, driver: WebDriver, max_reviews: int, product_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        all_reviews = []
        
        for page_num in range(1, self.config.max_pages + 1):
            logger.info(f"Обработка страницы отзывов #{page_num}")
            
            self._scroll_to_bottom(driver)
            time.sleep(0.5) 

            page_reviews, stop_parsing = self._get_reviews_from_page(driver, product_info, page_num)
            
            if page_reviews:
                all_reviews.extend(page_reviews)

            if stop_parsing or len(all_reviews) >= max_reviews:
                break
            
            if not self._go_to_next_page(driver, page_num):
                break
        return all_reviews[:max_reviews]

    def _scroll_to_bottom(self, driver) -> None:
        try:
            last_height = driver.execute_script("return document.body.scrollHeight")
            for _ in range(10): 
                driver.execute_script(f"window.scrollBy(0, {self.config.scroll_step});")
                time.sleep(self.config.scroll_pause)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
        except Exception as e:
            logger.warning(f"Ошибка при прокрутке страницы: {e}")

    def _go_to_next_page(self, driver, page_num: int) -> bool:
        try:
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, self.selectors.NEXT_BUTTON))
            )
            driver.execute_script("arguments[0].click();", next_button)
            WebDriverWait(driver, 10).until(lambda d: f"page={page_num + 1}" in d.current_url)
            return True
        except TimeoutException:
            return False
        except ElementClickInterceptedException:
            logger.warning("Клик по кнопке 'Дальше' перехвачен. Пробуем прокрутить и повторить.")
            driver.execute_script("window.scrollBy(0, 250);")
            time.sleep(0.5)
            try:
                next_button = driver.find_element(By.XPATH, self.selectors.NEXT_BUTTON)
                driver.execute_script("arguments[0].click();", next_button)
                WebDriverWait(driver, 10).until(lambda d: f"page={page_num + 1}" in d.current_url)
                return True
            except Exception as e_retry:
                logger.error(f"Повторная попытка клика не удалась: {e_retry}")
                return False
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при переходе на следующую страницу: {e}", exc_info=True)
            return False
    
    def is_valid_product_id(self, product_id: str) -> bool:

        if not product_id:
            return False
        
        return bool(re.fullmatch(r"^\d+$", product_id))
    
    def extract_product_id_from_url(self, url: str) -> str:

        if not url:
            return ""
        
        patterns = [
            r"ozon\.ru/product/([^/]+)-(\d+)",  
            r"ozon\.ru/context/detail/id/(\d+)",  
            r"/product/([^/]+)-(\d+)",  
            r"/context/detail/id/(\d+)",  
            r"sku=(\d+)", 
            r"/(\d+)(?:/|$)",  
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(match.lastindex)
        
        logger.warning(f"Не удалось извлечь ID товара из URL: {url}")
        return ""
    

    
    def _has_captcha(self, driver) -> bool:

        for selector in self.selectors.CAPTCHA_INDICATORS:
            try:
                if driver.find_elements(By.XPATH, selector):
                    logger.warning(f"Обнаружен индикатор CAPTCHA по селектору: {selector}")
                    return True
            except Exception:
                continue
        return False

    def _has_blocked_access(self, driver) -> bool:

        for selector in self.selectors.BLOCK_INDICATORS:
            try:
                if driver.find_elements(By.XPATH, selector):
                    logger.warning(f"Обнаружен индикатор блокировки по селектору: {selector}")
                    return True
            except Exception:
                continue
        return False 

    def _has_reviews(self, driver) -> bool:
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors.REVIEWS_WIDGET))
            )
            
            review_elements = driver.find_elements(By.XPATH, self.selectors.REVIEW_ELEMENTS)
            if review_elements:
                return True
            else:
                logger.warning("Виджет отзывов найден, но самих отзывов на странице нет.")
                return False

        except TimeoutException:
            logger.warning("Не найден виджет отзывов на странице.")
            return False
        except Exception as e:
            logger.error(f"Ошибка при проверке наличия отзывов: {e}", exc_info=True)
            return False
    
    def _get_product_info_from_page(self, driver) -> Dict[str, Any]:
        try:
            current_url = driver.current_url
            product_id = self.extract_product_id_from_url(current_url)
            
            return {
                "id": product_id,
                "name": f"Товар с OZON {product_id}",
                "brand": "",
                "rating": 0,
                "price": 0,
                "image_url": "",
                "url": current_url,
                "source": "ozon",
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении базовой информации о товаре: {e}")
            return {
                "id": "unknown",
                "name": "Товар с OZON",
                "brand": "",
                "rating": 0,
                "price": 0,
                "image_url": "",
                "url": "",
                "source": "ozon",
            }
    
    def _get_reviews_from_page(self, driver, product_info: Dict[str, Any], page_num: int) -> Tuple[List[Dict[str, Any]], bool]:
        
        page_reviews = []
        empty_reviews_streak = 0
        
        try:
            review_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, self.selectors.REVIEW_ELEMENTS))
            )
            
            for review_element in review_elements:
                try:
                    review_data = self._extract_review_data(review_element, product_info)
                    if review_data:
                        page_reviews.append(review_data)
                        empty_reviews_streak = 0  
                    else:
                        empty_reviews_streak += 1

                    if empty_reviews_streak >= self.config.max_empty_streak:
                        logger.warning(f"Обнаружено {empty_reviews_streak} пустых отзывов подряд. Прекращаем обработку.")
                        return page_reviews, True  

                except StaleElementReferenceException:
                    logger.warning("Элемент отзыва устарел (StaleElementReferenceException), пропускаем.")
                    continue
                except Exception as e_inner:
                    logger.error(f"Ошибка при извлечении данных из одного отзыва: {e_inner}", exc_info=True)
                    empty_reviews_streak += 1

        except TimeoutException:
            logger.warning(f"На странице #{page_num} не найдены отзывы (таймаут).")
            return [], False
        except Exception as e:
            logger.error(f"Критическая ошибка при получении отзывов со страницы: {e}", exc_info=True)
            return [], False

        return page_reviews, False
    
    def _extract_review_data(self, review_element, product_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            author = review_element.find_element(By.XPATH, self.selectors.AUTHOR_NAME).text.strip()
            text = review_element.find_element(By.XPATH, self.selectors.REVIEW_TEXT).text.strip()
            date_str = review_element.find_element(By.XPATH, self.selectors.REVIEW_DATE).text.strip()
            rating_elements = review_element.find_elements(By.XPATH, self.selectors.REVIEW_RATING)
            rating = len(rating_elements)
            
            if not text:
                return None

            return {
                "id": review_element.get_attribute('data-review-uuid'),
                "product_id": product_info.get("id"),
                "author": author,
                "date": self._parse_date(date_str),
                "rating": rating,
                "text": text,
                "images": [],
                "source": "ozon"
            }
        except NoSuchElementException as e:
            return None
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных из элемента отзыва: {e}", exc_info=True)
            return None

    def _parse_date(self, date_str: str) -> str:
        date_str = date_str.lower().replace("изменен ", "")
        months = {
            'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04', 'мая': '05', 'июня': '06',
            'июля': '07', 'августа': '08', 'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'
        }
        try:
            for month_name, month_number in months.items():
                if month_name in date_str:
                    date_str = date_str.replace(month_name, month_number)
                    break
            
            parsed_date = datetime.strptime(date_str, '%d %m %Y')
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            logger.warning(f"Не удалось распознать дату '{date_str}'. Используется текущая дата.")
            return date.today().strftime('%Y-%m-%d')