import asyncio
import aiohttp
import bs4
import json
import os

RETRY_STATUSES = {429, 500, 502, 503, 504}

class HTTPError(Exception):
    def __init__(self, status, url):
        self.status = status
        self.url = url
        super().__init__(f'HTTP {self.status} для {url}')

def load_config(config_path: str = 'config.json') -> dict:
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_to_json(titles, filename):
    """ Сохранение файла в формате json """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(titles, f, indent=2, ensure_ascii=False)
        print(f"Данный успешно сохранены в: {filename}")
        return True
    except PermissionError:
        print(f"Ошибка. Нет прав для записи в файл {filename}")
        return False
    except OSError as e:
        print(f"Системная ошибка: {e}")
        return False

def parse_titles(http, selector):
    """ Получение заголовков статей """
    soup = bs4.BeautifulSoup(http, 'html.parser')
    titles = [title.text for title in soup.select(selector)]
    if not titles:
        print("Не найдено ни одного заголовка")
    return titles

async def fetch_url(url, retries = 3, timeout_config = None):
    """ Создание запроса и получение xtml текста """
    if timeout_config is None:
        timeout_config = {
            "total": 30, 
            "connect": 10, 
            "sock_connect": 10,
            "sock_read": 10
        }
    timeout = aiohttp.ClientTimeout(
        total = timeout_config.get("total", 30),
        connect = timeout_config.get("connect", 10),
        sock_connect = timeout_config.get("sock_connect", 10),
        sock_read = timeout_config.get("sock_read", 10)
    )
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for attempt in range(retries):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                
                    elif response.status in RETRY_STATUSES:
                        if attempt == retries - 1:
                            raise HTTPError(response.status, url)
                        await asyncio.sleep(2 ** attempt)
                
                    else:
                        raise HTTPError(response.status, url)
            except (aiohttp.ClientConnectionError, 
                    aiohttp.ClientConnectorError,
                    aiohttp.ServerDisconnectedError,
                    asyncio.TimeoutError
                    ) as e:
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
            except (aiohttp.ClientSSLError, aiohttp.ClientOSError) as e:
                raise
                                
async def main(config):
    result = await fetch_url(
        config["habr"]["base_url"], 
        config["settings"]["retries"], 
        config["settings"].get("timeout")
    )
    titles = parse_titles(result, config["habr"]["selectors"]["title"])
    if not save_to_json(titles, config["output"]["filename"]):
        print('Не удалось сохранить результаты')

if __name__ == '__main__':
    config = load_config()
    asyncio.run(main(config))