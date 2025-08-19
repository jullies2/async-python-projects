import asyncio
import aiohttp
import bs4
import json
import os

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
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(titles, f, indent=2, ensure_ascii=False)

def parse_titles(http):
    """ Получение заголовков статей """
    soup = bs4.BeautifulSoup(http, 'html.parser')
    all_titles = soup.find_all('a', class_="tm-title__link")
    filteredTitles = []
    for title in all_titles:
        if title.find('span') is not None:
            filteredTitles.append(title.text)
    save_to_json(filteredTitles, 'titles.json')

async def fetch_url(url, retries = 3):
    """ Создание запроса и получение xtml текста """
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status in (429, 500, 502, 503, 504):
                        if attempt == retries - 1:
                            raise HTTPError(response.status, url)
                        await asyncio.sleep(2 ** attempt)  # Экспоненциальная задержка
                    else:
                        raise HTTPError(response.status, url)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
            
async def main(config):
    result = await fetch_url(config["habr"]["base_url"], config["settings"]["retries"])
    parse_titles(result)

if __name__ == '__main__':
    config = load_config()
    asyncio.run(main(config))