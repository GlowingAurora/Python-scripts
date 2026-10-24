# Qwen did this not me
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import requests
import random
import time
import os
import hashlib
import json
import re

# ===== ФИЛЬТР МУСОРНЫХ ВВОДОВ ОТ VS CODE =====
VSCODE_GARBAGE_PATTERNS = [
    r'Set-ExecutionPolicy',
    r'Activate\.ps1',
    r'venv\\Scripts',
    r'&\s+c:\\',
    r'&\s+c:/',
    r'python\s+["\']?',
    r'py\s+["\']?',
    r'conda\s+activate',
]

def is_vscode_garbage(text):
    for pattern in VSCODE_GARBAGE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def safe_input(prompt):
    while True:
        try:
            value = input(prompt).strip()
        except EOFError:
            return ""
        if is_vscode_garbage(value):
            print(f"  ⚠ Обнаружена мусорная команда от VS Code, игнорирую. Введите заново.")
            continue
        return value


class PinterestDownloaderSelenium:
    def __init__(self):
        self.base_download_dir = "pinterest_images"
        if not os.path.exists(self.base_download_dir):
            os.makedirs(self.base_download_dir)
        
        self.downloaded_hashes = set()
        self.driver = None
        self.cookies_file = "pinterest_cookies.json"
        self.current_query_dir = None
    
    def sanitize_folder_name(self, query):
        sanitized = re.sub(r'[<>:"/\\|?*]', '', query)
        sanitized = sanitized.replace(' ', '_')
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
        sanitized = sanitized.rstrip('.')
        return sanitized if sanitized else "untitled"
    
    def setup_query_directory(self, query):
        folder_name = self.sanitize_folder_name(query)
        self.current_query_dir = os.path.join(self.base_download_dir, folder_name)
        
        if not os.path.exists(self.current_query_dir):
            os.makedirs(self.current_query_dir)
            print(f"  ✓ Создана папка: {folder_name}")
        else:
            print(f"  ✓ Папка существует: {folder_name}")
        
        self.load_existing_hashes()
        return self.current_query_dir
    
    def load_existing_hashes(self):
        self.downloaded_hashes.clear()
        
        if not os.path.exists(self.current_query_dir):
            return
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        existing_files = 0
        
        for filename in os.listdir(self.current_query_dir):
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in image_extensions:
                filepath = os.path.join(self.current_query_dir, filename)
                try:
                    with open(filepath, 'rb') as f:
                        img_hash = hashlib.md5(f.read()).hexdigest()
                        self.downloaded_hashes.add(img_hash)
                        existing_files += 1
                except Exception as e:
                    print(f"    ⚠ Не удалось прочитать {filename}: {str(e)[:30]}")
        
        if existing_files > 0:
            print(f"  ✓ Загружено {existing_files} существующих изображений для проверки уникальности")
        else:
            print(f"  ℹ Папка пуста, начинаем с нуля")
    
    def setup_driver(self):
        print("  [1/6] Инициализация браузера...")
        
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            print("  [2/6] Запуск Chrome...")
            self.driver = webdriver.Chrome(options=chrome_options)
            print("  ✓ Браузер запущен")
            
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                """
            })
        except Exception as e:
            print(f"  ✗ Ошибка запуска: {str(e)}")
            raise
    
    def load_cookies(self):
        if not os.path.exists(self.cookies_file):
            return False
        
        try:
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            
            self.driver.get("https://www.pinterest.com/")
            time.sleep(2)
            
            for cookie in cookies:
                try:
                    cookie_dict = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie.get('domain', '.pinterest.com'),
                        'path': cookie.get('path', '/'),
                    }
                    if 'expiry' in cookie:
                        cookie_dict['expiry'] = cookie['expiry']
                    
                    self.driver.add_cookie(cookie_dict)
                except Exception as e:
                    print(f"    ⚠ Не удалось добавить cookie {cookie.get('name')}: {str(e)[:30]}")
            
            print("  ✓ Cookies загружены")
            return True
        except Exception as e:
            print(f"  ✗ Ошибка загрузки cookies: {str(e)}")
            return False
    
    def save_cookies(self):
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
            print(f"  ✓ Cookies сохранены в {self.cookies_file}")
        except Exception as e:
            print(f"  ✗ Ошибка сохранения cookies: {str(e)}")
    
    def manual_login(self):
        print("\n" + "="*60)
        print("🔐 ТРЕБУЕТСЯ ВХОД В PINTEREST")
        print("="*60)
        print("\nСейчас откроется браузер Pinterest.")
        print("Пожалуйста, войдите в свой аккаунт вручную.")
        print("\nПосле успешного входа:")
        print("  1. Убедитесь, что вы видите главную страницу Pinterest")
        print("  2. Нажмите ENTER в этом окне для сохранения cookies")
        print("="*60 + "\n")
        
        self.driver.get("https://www.pinterest.com/login/")
        
        safe_input("👉 Нажмите ENTER после успешного входа...")
        
        if "login" in self.driver.current_url.lower():
            print("⚠ Похоже, вы не вошли. Попробуйте еще раз.")
            return False
        
        self.save_cookies()
        print("\n✓ Вход выполнен успешно! Cookies сохранены.\n")
        return True
    
    def check_login_status(self):
        try:
            self.driver.get("https://www.pinterest.com/")
            time.sleep(3)
            
            page_source = self.driver.page_source.lower()
            
            if 'sign in' in page_source or 'log in' in page_source or 'регистрация' in page_source:
                return False
            
            if 'account' in page_source or 'профиль' in page_source:
                return True
            
            if 'login' in self.driver.current_url.lower():
                return False
            
            return True
        except Exception as e:
            print(f"  ⚠ Ошибка проверки статуса: {str(e)}")
            return False
    
    def get_image_hash(self, image_data):
        return hashlib.md5(image_data).hexdigest()
    
    def is_unique_image(self, image_data):
        img_hash = self.get_image_hash(image_data)
        if img_hash in self.downloaded_hashes:
            return False
        self.downloaded_hashes.add(img_hash)
        return True
    
    def collect_image_urls(self):
        """Собирает все URL изображений через JavaScript"""
        script = """
            var images = document.querySelectorAll('img[src*="i.pinimg.com"]');
            var urls = [];
            for (var i = 0; i < images.length; i++) {
                var src = images[i].getAttribute('src');
                if (src && (src.indexOf('236x') !== -1 || src.indexOf('736x') !== -1 || src.indexOf('originals') !== -1)) {
                    var highQuality = src.replace('/236x/', '/736x/').replace('/150x150/', '/736x/');
                    urls.push(highQuality);
                }
            }
            return [...new Set(urls)];
        """
        
        try:
            urls = self.driver.execute_script(script)
            return urls if urls else []
        except Exception as e:
            print(f"  ⚠ Ошибка при сборе URL: {str(e)[:50]}")
            return []
    
    def smooth_scroll_and_collect(self, max_images):
        """
        Плавный скролл с постепенным сбором URL.
        Решает проблему lazy loading — Pinterest успевает подгрузить изображения.
        """
        all_urls = set()
        
        # Сначала собираем URL с текущей позиции (без скролла)
        print("  Сбор изображений с текущей позиции...")
        initial_urls = self.collect_image_urls()
        all_urls.update(initial_urls)
        print(f"    Найдено: {len(all_urls)} изображений")
        
        # Ждем немного, чтобы Pinterest подгрузил еще
        time.sleep(2)
        
        # Плавный скролл вниз
        scroll_step = 800  # Шаг скролла в пикселях
        max_scrolls = 30   # Максимальное количество шагов
        no_new_count = 0   # Счетчик шагов без новых изображений
        
        print(f"  Плавный скролл для загрузки всех изображений...")
        
        for scroll_num in range(max_scrolls):
            # Прокручиваем на шаг
            self.driver.execute_script(f"window.scrollBy(0, {scroll_step});")
            
            # Ждем, чтобы Pinterest подгрузил изображения
            time.sleep(random.uniform(1.5, 2.5))
            
            # Собираем новые URL
            new_urls = self.collect_image_urls()
            previous_count = len(all_urls)
            all_urls.update(new_urls)
            current_count = len(all_urls)
            
            # Проверяем, появились ли новые изображения
            if current_count == previous_count:
                no_new_count += 1
                print(f"    Скролл {scroll_num+1}: нет новых изображений ({current_count} всего)")
            else:
                no_new_count = 0
                print(f"    Скролл {scroll_num+1}: +{current_count - previous_count} новых ({current_count} всего)")
            
            # Если достаточно изображений — останавливаемся
            if current_count >= max_images * 2:
                print(f"    ✓ Достаточно изображений найдено")
                break
            
            # Если 3 раза подряд нет новых — значит достигли конца
            if no_new_count >= 3:
                print(f"    ✓ Достигнут конец ленты")
                break
        
        return list(all_urls)
    
    def download_with_selenium(self, query, max_images=10):
        print(f"\n{'='*60}")
        print(f"🔍 Поиск: '{query}'")
        print(f"🎯 Цель: {max_images} изображений")
        print(f"{'='*60}\n")
        
        try:
            self.setup_driver()
            
            print("  [3/6] Проверка авторизации...")
            
            if os.path.exists(self.cookies_file):
                print("  Найдены сохраненные cookies")
                self.load_cookies()
            
            if not self.check_login_status():
                print("  ⚠ Требуется вход в аккаунт")
                if not self.manual_login():
                    print("✗ Не удалось войти в аккаунт")
                    return 0
            else:
                print("  ✓ Авторизация подтверждена")
            
            print("  [4/6] Настройка папки для сохранения...")
            self.setup_query_directory(query)
            
            url = f"https://www.pinterest.com/search/pins/?q={query.replace(' ', '%20')}"
            print(f"  [5/6] Открытие страницы поиска...")
            
            self.driver.get(url)
            time.sleep(random.uniform(4, 7))
            print("  ✓ Страница загружена")
            
            print("  [6/6] Плавный скролл и сбор изображений...")
            
            # 🔥 ИСПОЛЬЗУЕМ ПЛАВНЫЙ СКРОЛЛ
            image_urls = self.smooth_scroll_and_collect(max_images)
            
            print(f"\n  ✓ Всего найдено {len(image_urls)} уникальных URL\n")
            
            if not image_urls:
                print("  ⚠ Не удалось найти изображения")
                return 0
            
            downloaded = 0
            skipped = 0
            processed_urls = set()
            
            cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}
            
            for url_to_download in image_urls:
                if downloaded >= max_images:
                    break
                
                if url_to_download in processed_urls:
                    continue
                processed_urls.add(url_to_download)
                
                try:
                    delay = random.uniform(1, 5)
                    print(f"  [{downloaded+1}/{max_images}] Ожидание {delay:.1f} сек...", end='\r')
                    time.sleep(delay)
                    
                    response = requests.get(url_to_download, timeout=15, cookies=cookies, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': 'https://www.pinterest.com/'
                    })
                    
                    if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                        if self.is_unique_image(response.content):
                            ext = '.jpg'
                            filename = f"image_{downloaded+1}_{int(time.time())}{ext}"
                            filepath = os.path.join(self.current_query_dir, filename)
                            
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            
                            downloaded += 1
                            print(f"  ✓ [{downloaded}/{max_images}] {filename} ({len(response.content)//1024} KB)   ")
                        else:
                            skipped += 1
                            print(f"  ~ Дубликат пропущен                                          ")
                    else:
                        print(f"  ✗ Ошибка загрузки (код {response.status_code})                 ")
                        
                except Exception as e:
                    print(f"  ✗ Ошибка: {str(e)[:40]}                                        ")
                    continue
            
            print(f"\n{'='*60}")
            print(f"✅ РЕЗУЛЬТАТ:")
            print(f"   Скачано: {downloaded}")
            print(f"   Пропущено: {skipped}")
            print(f"   Папка: {os.path.abspath(self.current_query_dir)}")
            print(f"{'='*60}\n")
            
            return downloaded
            
        except Exception as e:
            print(f"\n✗ Ошибка: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0
            
        finally:
            if self.driver:
                print("\n  Закрытие браузера...")
                self.driver.quit()


def main():
    print("="*60)
    print("📌 Pinterest Downloader (с плавным скроллом)")
    print("="*60)
    print("\nТребования:")
    print("  • Google Chrome установлен")
    print("  • pip install selenium requests")
    print("  • Аккаунт Pinterest\n")
    
    downloader = PinterestDownloaderSelenium()
    
    while True:
        try:
            query = safe_input("🔍 Введите запрос (или 'exit'): ")
            
            if query.lower() in ['exit', 'quit', 'выход']:
                print("\n👋 До свидания!")
                break
            
            if not query:
                print("⚠ Введите текст\n")
                continue
            
            while True:
                try:
                    max_input = safe_input("📊 Количество (по умолчанию 10): ")
                    if not max_input:
                        max_images = 10
                        break
                    max_images = int(max_input)
                    if max_images <= 0:
                        print("⚠ Введите число больше 0")
                        continue
                    if max_images > 150:
                        print("⚠ Максимум 150")
                        max_images = 150
                    break
                except ValueError:
                    print("⚠ Введите число")
            
            print(f"\n🚀 Начинаю...")
            downloader.download_with_selenium(query, max_images)
            
        except KeyboardInterrupt:
            print("\n\n⚠ Прервано")
            if downloader.driver:
                downloader.driver.quit()
            break
        except Exception as e:
            print(f"\n✗ Ошибка: {str(e)}")


if __name__ == "__main__":
    main()