import math
import requests
from bs4 import BeautifulSoup

def get_game_count(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # <td>タグ内の数字（例: <td>27</td>）をすべて抽出し、最大値をチーム試合数とする
    game_count = None
    tr = soup.find('tr', class_='topInning')
    if tr:
        td_tags = tr.find_all('td')
        if len(td_tags) > 1:
            text = td_tags[1].get_text(strip=True)
            if text.isdigit():
                game_count = int(text)
    return game_count

def calc_regulation_at_bats(game_count):
    if game_count is None:
        return None
    return math.ceil(game_count * 1.8)

if __name__ == '__main__':
    url = 'https://teams.one/teams/ryunen_busters/stats'
    game_count = get_game_count(url)
    print(f'試合数: {game_count}')
    regulation_at_bats = calc_regulation_at_bats(game_count)
    print(f'規定打席: {regulation_at_bats}')
