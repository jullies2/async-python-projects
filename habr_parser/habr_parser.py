import asyncio
import aiohttp
import bs4
import json

def save_to_json(titles, filename):
    #file_data = json.dumps(titles, ensure_ascii=False)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(titles, f, indent=2, ensure_ascii=False)

def parse_titles(http):
    soup = bs4.BeautifulSoup(http, 'html.parser')
    all_titles = soup.find_all('a', class_="tm-title__link")
    filteredTitles = []
    for title in all_titles:
        if title.find('span') is not None:
            filteredTitles.append(title.text)
    save_to_json(filteredTitles, 'titles.json')

async def fetch_url(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.text()
            else:
                return f"Error: {response.status}"
            
async def main():
    url = 'https://habr.com/ru/flows/develop/articles/'
    result = await fetch_url(url)
    parse_titles(result)

if __name__ == '__main__':
    asyncio.run(main())