import os
import datetime
from bs4 import BeautifulSoup
import urllib.request
import xml.etree.ElementTree as ET
import configparser

def get_news_pool(root, start, end):
    news_pool = []
    for i in range(start,end,1):
        page_url = root +'%d.shtml'%(i)
        print(page_url)
        try:
            response = urllib.request.urlopen(page_url)
        except Exception as e:
            print("-----%s: %s-----"%(type(e), page_url))
            continue
        html = response.read()
        soup = BeautifulSoup(html,"lxml") # http://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/
        td = soup.find('ul', class_ = "txt-list-a fz-14")
        a = td.find_all('a')
        span = td.find_all('span')
        for i in range(len(a)):
            date_time = span[i].string
            url = a[i].get('href')
            title = a[i].string
            news_info = [date_time, url, title]
            news_pool.append(news_info)
    return(news_pool)


def crawl_news(news_pool, min_body_len, doc_dir_path, doc_encoding):
    i = 1
    for news in news_pool:
        try:
            response = urllib.request.urlopen(news[1])
        except Exception as e:
            print("URL-Request-----%s: %s-----"%(type(e), news[1]))
            continue
        html = response.read()
        soup = BeautifulSoup(html,"lxml") # http://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/
        try:
            body = soup.find('div', class_ = "inner").find('div').get_text()
        except Exception as e:
            print("Content-----%s: %s-----"%(type(e), news[1]))
            continue
        if '//' in body:
            body = body[:body.index('//')]
        body = body.replace(" ", "")
        if len(body) <= min_body_len:
            continue
        doc = ET.Element("doc")
        ET.SubElement(doc, "source").text = "CanKao News"
        ET.SubElement(doc, "id").text = "%d"%(i)
        ET.SubElement(doc, "url").text = news[1]
        ET.SubElement(doc, "title").text = news[2]
        ET.SubElement(doc, "datetime").text = news[0]
        ET.SubElement(doc, "body").text = body
        tree = ET.ElementTree(doc)
        tree.write(doc_dir_path + news[0].replace(' ','-').replace(':','-') + "_%d.xml"%(i), encoding = doc_encoding, xml_declaration = True)
        i += 1
    
if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('./config.ini', 'utf-8')
    urlpool = ['http://www.cankaoxiaoxi.com/china/szyw/', 'http://www.cankaoxiaoxi.com/china/zgwj/', 'http://www.cankaoxiaoxi.com/china/shwx/',\
                    'http://www.cankaoxiaoxi.com/china/gacz/', 'http://www.cankaoxiaoxi.com/china/zggd/', 'http://www.cankaoxiaoxi.com/world/ytxw/',\
                        'http://www.cankaoxiaoxi.com/world/omxw/','http://www.cankaoxiaoxi.com/world/omxw/','http://www.cankaoxiaoxi.com/world/qtdq/',\
                            'http://www.cankaoxiaoxi.com/world/hqbl/','http://www.cankaoxiaoxi.com/world/gjgd/', 'http://www.cankaoxiaoxi.com/mil/gjjq/',\
                                'http://www.cankaoxiaoxi.com/mil/zgjq/','http://www.cankaoxiaoxi.com/mil/gjjq/','http://www.cankaoxiaoxi.com/mil/wqzb/',\
                                    'http://www.cankaoxiaoxi.com/finance/zgcj/','http://www.cankaoxiaoxi.com/finance/gjcj/','http://www.cankaoxiaoxi.com/finance/sygs/',\
                                        'http://www.cankaoxiaoxi.com/finance/jrsc/','http://www.cankaoxiaoxi.com/science/tsfx/','http://www.cankaoxiaoxi.com/science/jksh/',\
                                            'http://www.cankaoxiaoxi.com/science/ITyj/','http://www.cankaoxiaoxi.com/science/hjbh/','http://www.cankaoxiaoxi.com/science/kjtt/']
    news_pool = []
    for topic in urlpool:
        news_pool.extend(get_news_pool(topic, 1, 40))
    crawl_news(news_pool, 10, config['DEFAULT']['doc_dir_path']+'cankao/', config['DEFAULT']['doc_encoding'])
    print('Get ' + str(len(news_pool)) + ' URLs.')
