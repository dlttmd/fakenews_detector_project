import re
from bs4 import BeautifulSoup
import requests
import pandas as pd
from tqdm import tqdm

def makePgNum(num):
    if num == 1:
        return num
    elif num == 0:
        return num + 1
    else:
        return num + 9 * (num - 1)
    
def makeUrl(search, start_pg, end_pg, sort=1):
    if start_pg == end_pg:
        start_page = makePgNum(start_pg)
        url = f"https://search.naver.com/search.naver?where=news&sm=tab_pge&query={search}&start={start_page}&sort={sort}"
        return url
    else:
        urls = []
        for i in range(start_pg, end_pg + 1):
            page = makePgNum(i)
            url = f"https://search.naver.com/search.naver?where=news&sm=tab_pge&query={search}&start={page}&sort={sort}"
            urls.append(url)
        return urls
    
def news_attrs_crawler(articles, attrs):
    attrs_content = []
    for i in articles:
        attrs_content.append(i.attrs[attrs])
    return attrs_content

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/98.0.4758.102"}

def articles_crawler(url):
    original_html = requests.get(url, headers=headers)
    html = BeautifulSoup(original_html.text, "html.parser")
    url_naver = html.select(
        "div.group_news > ul.list_news > li div.news_area > div.news_info > div.info_group > a.info")
    url = news_attrs_crawler(url_naver, 'href')
    return url

def get_news_dataframe(search, start_page, end_page, sort=1):
    url = makeUrl(search, start_page, end_page, sort)
    news_url = []
    for i in url:
        urls = articles_crawler(i)
        news_url.extend(urls)

    # NAVER 뉴스만 남기기
    final_urls = []
    for i in tqdm(news_url):
        if "news.naver.com" in i:
           final_urls.append(i)
    firm = ['MBC연예','마이데일리']
    news_titles = []
    news_contents = []
    news_dates = []
    news_press = []
    
    for i in tqdm(final_urls):
        news = requests.get(i, headers=headers)
        news_html = BeautifulSoup(news.text, "html.parser")
        html = news.content
        soup = BeautifulSoup(html, 'html.parser')
        press = soup.find('img')['alt']
        title = news_html.select_one("#ct > div.media_end_head.go_trans > div.media_end_head_title > h2")
        if title is None:
            title = news_html.select_one("#content > div.end_ct > div > h2")
        content = news_html.select("article#dic_area")
        if not content:
            content = news_html.select("#articeBody")
        content = ''.join(str(content))
        pattern1 = '<[^>]*>'
        title = re.sub(pattern=pattern1, repl='', string=str(title))
        content = re.sub(pattern=pattern1, repl='', string=content)
        pattern2 = """[\n\n\n\n\n// flash 오류를 우회하기 위한 함수 추가\nfunction _flash_removeCallback() {}"""
        content = content.replace(pattern2, '')
        news_press.append(press)
        news_titles.append(title)
        news_contents.append(content)
        try:
            html_date = news_html.select_one(
                "div#ct> div.media_end_head.go_trans > div.media_end_head_info.nv_notrans > div.media_end_head_info_datestamp > div > span")
            news_date = html_date.attrs['data-date-time']
        except AttributeError:
            news_date = news_html.select_one("#content > div.end_ct > div > div.article_info > span > em")
            news_date = re.sub(pattern=pattern1, repl='', string=str(news_date))
        news_dates.append(news_date)
    news_df = pd.DataFrame({'date': news_dates, 'title': news_titles, 'content': news_contents, 'press': news_press})
    return news_df

def main():
  search = input('검색할 키워드를 입력하세요:')

  page = int(input('크롤링할 시작 페이지를 입력하세요. ex) 1 (숫자만 입력):'))

  page2 = int(input('크롤링할 종료 페이지를 입력하세요. ex) 1 (숫자만 입력):'))

  news_df = get_news_dataframe(search, page, page2)

  return news_df