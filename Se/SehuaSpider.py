#!/usr/bin/env python
# coding:utf-8
# 
# @Time : 2021-06-21 21:04:57 
# @Autor: 于玉菊@九八堂
# @File :  SehuaSpider.py
# 


import os
import sys
import time
import requests
from lxml import etree
import asyncio
from aiohttp import ClientSession
import json
import configparser
from concurrent.futures import ThreadPoolExecutor
import logging


BASE_URL = "https://www.qwewqewqq2.xyz/"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STORAGE_DIR = BASE_DIR + '\\SeHua\\'

"""**************************************************************************
FILTER_DIC格式: 分类的编号: [起始页， 结尾页]
例如： 爬取 欧美无码的第 3 页到第 10 页
        FILTER_DIC = {
            '38': [3, 10]
        }
        
      同时爬取 亚洲无码的第 1 页到第 200 页和 亚洲有码的第 20 页到 60 页
        FILTER_DIC = {
            '36': [1, 200]，
            '37': [20, 60]
        }
**************************************************************************"""
FILTER_DICT = {
    '36': [50, 55],
    '37': [15, 20],
}

CATEGORY_NAME_MAPPING = {
    '36': '亚洲无码原创',
    '37': '亚洲有码原创',
    '38': '欧美无码',
    '39': '动漫原创',
    '103': '高清中文字幕'
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36"
}

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] [%(lineno)s]\t%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S %p',
                    filename='./sehua.log'
                    )
logging.FileHandler('sehua.log', encoding='utf-8')


class ProgressBar:
    def __init__(self, sym1="#", sym2="-", scale=50):
        self.scale = scale
        self.sym1 = sym1
        self.sym2 = sym2

    def show_progress_bar(self, prog, start, msg):
        show_prog = prog * self.scale // 100
        rest = self.scale - show_prog
        dur = time.perf_counter() - start
        fomt = f"\r{self.sym1 * show_prog}{self.sym2 * rest} {prog:^3.0f}%  {dur:.1f}s"
        sys.stdout.write(f"{fomt}  {msg}")
        sys.stdout.flush()


async def parse_page(url, exp):
    async with ClientSession() as session:
        async with session.get(url=url, headers=HEADERS) as response:
            response = await response.read()
            tree = etree.HTML(response)
            return tree.xpath(exp)


def get_ids():
    exp = '//*[contains(@id,"normalthread")]/tr/th/a[2]/@href'
    futures = []
    all_av_ids = []
    for fid, limit_list in FILTER_DICT.items():
        start_page_num = 1 if limit_list[0] == 0 else limit_list[0]
        end_page_num = limit_list[1]
        msg = f'{CATEGORY_NAME_MAPPING.get(fid)},{start_page_num}页到{end_page_num}页'
        logging.info(msg)
        for i in range(start_page_num, end_page_num + 1):
            url = BASE_URL + f'forum-{fid}-{i}.html'
            future = asyncio.ensure_future(parse_page(url, exp))
            futures.append(future)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(futures))
    for future in futures:
        id_list = [i.split('-')[1] for i in future.result()]
        all_av_ids.extend(id_list)
    return all_av_ids


def get_av_item(ids):
    pool = ThreadPoolExecutor(30)
    future_tasks = []
    start_time = time.perf_counter()
    bar = ProgressBar()
    for tid in ids:
        future = pool.submit(save_av, tid)
        future_tasks.append(future)
    for i, future in enumerate(future_tasks):
        future.result()
        prog = int(((i + 1) / len(ids)) * 100)
        bar.show_progress_bar(prog, start_time, f"{i + 1}/{len(ids)}")


def save_av(tid):
    try:
        url = BASE_URL + f"thread-{tid}-1-1.html"
        response = requests.get(url=url, headers=HEADERS)
        tree = etree.HTML(response.text)
        category_name = tree.xpath('//*[@id="pt"]/div/a[4]/text()')[0]
        info_list = tree.xpath('//div[@id="postlist"]/div[1]//div[@class="t_fsz"]//td[@class="t_f"]//text()')
        img_name_list = tree.xpath(
            '//div[@id="postlist"]/div[1]//div[@class="t_fsz"]//td[@class="t_f"]/ignore_js_op/div/div[1]/p[1]/strong/text()')
        img_url_list = tree.xpath(
            '//div[@id="postlist"]/div[1]//div[@class="t_fsz"]//td[@class="t_f"]/ignore_js_op/img/@file')
        img_dict = dict(zip(img_name_list, img_url_list))
        save_path = os.path.join(STORAGE_DIR, category_name)
        save_path = os.path.join(save_path, tid)
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        save_text(info_list, tid, save_path)
        save_img(img_dict, save_path)
    except Exception as e:
        msg = f"<{tid}> {e}"
        logging.error(msg)


def save_text(text_list, name, path):
    name = name + '.txt'
    text_path = os.path.join(path, name)
    text_str = ''
    for i in range(len(text_list)):
        if i < 6:
            text_str += text_list[i]
        if 'magnet' in text_list[i]:
            text_str = text_str + "\n【磁力链接】：" + text_list[i]
    with open(text_path, 'w', encoding='utf8') as fw:
        fw.write(text_str)


def save_img(dic, path):
    try:
        if not dic:
            return
        for img_name, img_url in dic.items():
            img_path = os.path.join(path, img_name)
            img_data = requests.get(url=img_url, headers=HEADERS).content
            with open(img_path, 'wb') as fw:
                fw.write(img_data)
    except Exception as e:
        logging.error(e)


def del_repeat(ids):
    saved_ids = get_local_ids()
    for i in saved_ids:
        if i in ids:
            ids.remove(i)


def get_local_ids():
    ids = []
    if os.path.exists(STORAGE_DIR):
        for path in os.listdir(STORAGE_DIR):
            ids.extend(os.listdir(os.path.join(STORAGE_DIR, path)))
    return ids


def start(ids):
    if not ids:
        ids = get_ids()
        del_repeat(ids)
    get_av_item(ids)
    logging.info(f"共爬取 {len(ids)} 条数据\n")
    print("\n爬取完成！")


if __name__ == '__main__':
    '''
    有时，可能由于网络原因，有的资源爬取失败，有的图片没有爬取下来
        对于爬取失败资源，ID 会被记录到 sehua.log 文件中,将其 ID 号复制到 ids 中， 如：ids = ['535947'， '535852'] 
        等一段时间再次进行爬取，图片爬取失败的也适用，爬取完成后清空 ids = []
        图片加载失败的另一种方法就是，删除所有图片爬取失败资源的文件夹，再次进行爬取。
    '''
    ids = []        # 爬取指定 id 文件
    start(ids)
