import requests
import time
import re
from tqdm import tqdm
from bs4 import BeautifulSoup


def get_mgt(target):
    req = requests.get(url=target)
    req.encoding = 'utf-8'
    html = req.text
    mgt = re.findall(r'magnet:\?xt=urn:btih:[0-9a-fA-F]{40,}', html)
    content = ''.join(mgt)
    return content


if __name__ == '__main__':
    server = "https://www.qwewqewqq2.xyz/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
    }
    x = input("请输入页码数:\n")
    target = ("https://www.qwewqewqq2.xyz/forum-2-" + x + ".html")
    book_name = ('98T_'+x+'.txt')
    req = requests.get(url=target, headers=headers)
    req.encoding = 'utf-8'
    html = req.text
    bs = BeautifulSoup(html, 'lxml')
    flt = bs.find('div', id='threadlist')
    flink = flt.find_all(attrs={'class': 's xst'})
    # print(flink)
    for flink_f in tqdm(flink):
        mgt_name = flink_f.string
        url = server + flink_f.get('href')
        content = get_mgt(url)
        with open(book_name, 'a', encoding='utf-8') as f:
            f.write(mgt_name)
            f.write('\n')
            f.write(content)
            f.write('\n\n')