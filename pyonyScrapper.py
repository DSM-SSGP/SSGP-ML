import requests
import pandas as pd

from tqdm import tqdm

from bs4 import BeautifulSoup

BASE_URL = 'https://pyony.com/search'
conv = {
    'gs25(지에스25)': 'GS25',
    '7-eleven(세븐일레븐)': 'Seven Eleven',
    'cu(씨유)': 'CU',
    'emart24(이마트24)': 'Emart24',
    'ministop(미니스톱)': 'MINISTOP'
}

remove = ', 원\n()'

def remstr(s, r):
    for c in r:
        s = s.replace(c, '')
    return s

def getPageAll():
    url = BASE_URL + '?item=100'
    res = requests.get(url)
    
    soup = BeautifulSoup(res.text, 'lxml')
    body = soup.find('body')
    
    page_cnt = int(body.find_all('li', {'class': 'page-item'})[-1].find('a', {'class': 'page-link'}).attrs['href'][6:-9])
    df = pd.concat([getPage(i) for i in tqdm(range(page_cnt))])
    df.index = range(len(df))
    
    return df

def getPage(page):
    url = BASE_URL + '?page={}&item=100'.format(page)
    res = requests.get(url)
    
    soup = BeautifulSoup(res.text, 'lxml')
    body = soup.find('body')
    
    lst = body.find_all('div', {'class': 'col-md-6'})
    
    return pd.DataFrame([{
        'conv': conv[item.find('small').text.lower()],
        'name': item.find('strong').text.lower(),
        'cost': remstr(item.find('i', {'class': 'fa fa-coins text-warning pr-1'}).next_sibling, remove),
        'price': remstr(item.find('span').text, remove),
        'event': item.find_all('span')[1].text,
        'path': item.find('img', {'class': 'prod_img'}).attrs['src']
    } for item in lst])

if __name__ == "__main__":
    getPageAll()