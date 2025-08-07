import requests
from bs4 import BeautifulSoup
from mysqlhelper import MySQLHelper
import logging

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 防止重复添加 handler
# mysqlhelper.py 中可能已经配置了日志
if not logger.handlers:
    # 文件日志
    file_handler = logging.FileHandler('douban_top100_search.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # 控制台日志
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

def douban_top100():
    movies = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    for start in range(0, 100, 25):
        url = f'https://movie.douban.com/top250?start={start}'
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        items = soup.select('.item')
        for item in items:
            title = item.select_one('.title').text.strip()
            info = item.select_one('.info')

            # 影片介绍是三行文本，可能包含导演、主演、上映年份等信息
            # 这里只取导演和上映年份,分别在第二行和第三行
                
            info_text = info.select_one('.bd p').text.splitlines()
            director = info_text[1].strip().replace('导演: ', '').split(' ')[0]  # 取第一行的导演信息
            year = info_text[2].split('/')[0].strip()  # 取第二行的年份信息
            if not year.isdigit():
                logger.warning(f'获取到非数字年份: {year},将其设为0')
                year = '0'

            rating = item.select_one('.rating_num').text.strip()
            quote = item.select_one('.quote span')
            quote = quote.text.strip() if quote else ''  # 有些电影没有短评 # strip() 去掉前后空格
            movies.append({
                'title': title,
                'director': director,
                'year': int(year),
                'rating': float(rating),
                'quote': quote
            })
            logger.info(f'获取到top100数据: {title}-{director}-{year}-{rating}-{quote}')
    return movies


def save_to_db(movies):
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root',  # 替换为你的密码
        'database': 'crawler_db',
        'port': 3306
    }
    insert_sql = """
        INSERT INTO douban_top100 (title, director, year, rating, quote)
        VALUES (%s, %s, %s, %s, %s)
    """
    params_list = [
        (m['title'], m['director'], m['year'], m['rating'], m['quote'])
        for m in movies
    ]

    db_helper = MySQLHelper(**db_config)
    affected = db_helper.batch_execute(insert_sql, params_list)
    print(f"成功插入 {affected} 条记录")
    logger.info(f'成功插入 {affected} 条记录到数据库')
    db_helper.close()


import matplotlib.pyplot as plt
import seaborn as sns  # Seaborn是一个建立在Matplotlib之上的Python数据可视化库
# 设置字体为FangSong（仿宋）
plt.rcParams['font.sans-serif'] = ['FangSong']

def visualize(movies):
    # 评分分布
    ratings = [m['rating'] for m in movies]
    plt.figure(figsize=(8, 4))
    sns.histplot(ratings, bins=10, kde=True)
    plt.title('豆瓣Top100 评分分布')
    plt.xlabel('评分')
    plt.ylabel('电影数量')
    plt.show()

    # 年份分布
    years = [m['year'] for m in movies]
    plt.figure(figsize=(10, 4))
    sns.countplot(x=years, order=sorted(set(years)))
    plt.title('豆瓣Top100 上映年份分布')
    plt.xlabel('年份')
    plt.ylabel('电影数量')
    plt.xticks(rotation=45)
    plt.show()

    # 导演出现次数
    # 使用字典统计每个导演的出现次数
    # 然后按次数排序，取前10
    # 最后用Seaborn绘制柱状图
    # 下方代码中 sns 是问的AI 不知道是个啥

    directors = [m['director'] for m in movies]
    plt.figure(figsize=(10, 4))
    top_directors = sns.countplot(x=directors, order=[d for d, _ in sorted({d: directors.count(d) for d in set(directors)}.items(), key=lambda x: x[1], reverse=True)[:10]])
    plt.title('豆瓣Top100 导演出现次数Top10')
    plt.xlabel('导演')
    plt.ylabel('电影数量')
    plt.xticks(rotation=45)
    plt.show()

if __name__ == '__main__':
    movies = douban_top100()
    # save_to_db(movies)
    visualize(movies)  # 可视化数据
    logger.info('程序执行完毕') 
