# -*- coding: utf-8 -*-
import datetime
from bs4 import BeautifulSoup
import urllib.request
import xml.etree.ElementTree as ET
import configparser
import requests
import json
from selenium import webdriver
import time
import re

headers = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/\
            537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'}

def GetComments(commentID):
    comments = []
    driver = webdriver.PhantomJS()
    driver.set_page_load_timeout(5000)  
    driver.set_script_timeout(5000)
    driver.implicitly_wait(30)
    s1 = 'http://quan.sohu.com/pinglun/cyqemw6s1/'
    u = s1 + commentID
    driver.get(u)
    time.sleep(10)
    html = driver.page_source
    soup = BeautifulSoup(html,'lxml')
    td = soup.find('div', class_ = "title-name-gw title-name-bg")
    a = soup.find_all('span', class_ = "wrap-word-gw")
    for i in range(len(a)):
        comments.append(a[i].string)
    driver.close() 
    if comments is None:
        comments = ["NULL"]
    else:
        comments = ["NULL" if v is None else v for v in comments]
    return comments

def GetCommentsNum(commentUrl):
    s1 = 'http://changyan.sohu.com/api/3/topic/liteload?callback=jQuery1709683075909326675_1500009616671&client_id=cyqemw6s1&topic_url='
    name = commentUrl
    u = s1 + str(name)
    res = requests.get(url=u,headers=headers,timeout=10).content.decode('utf-8')
    res = res.split('(')[1][0:-2]
    #print(type(res.decode('utf-8')))
    data = json.loads(res)
    num = int(data["cmt_sum"])
    #print(num)
    return str(num)

def get_news_pool(root, start, end, news_url_set):
    news_pool = []
    for i in range(start,end,-1):
        page_url = ''
        if i != start:
            page_url = root +'_%d.shtml'%(i)
        else:
            page_url = root + '.shtml'
        print("Processing " + page_url)
        try:
            response = urllib.request.urlopen(page_url)
        except Exception as e:
            print("-----%s: %s-----"%(type(e), page_url))
            continue
        html = response.read()
        soup = BeautifulSoup(html,"lxml") # http://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/
        try:
            td = soup.find('div', class_ = "f14list")
            if td is None:
                td = soup.find('td', class_ = "newsblue1")
        except Exception as e:
            print("-----%s: %s-----"%(type(e), "old style"))
            try:
                td = soup.find('td', class_ = "newsblue1")
            except Exception as e:
                print("-----%s: %s-----"%(type(e), "unknown style"))
                continue
        try:
            a = td.find_all('a')
        except Exception as e:    
            print("-----%s: %s-----"%(type(e)), "find all a failed")
            continue
        span = td.find_all('span')
        for i in range(len(a)):
            try:
                date_time = span[i].string
                url = a[i].get('href')
                title = a[i].string
                d1 = datetime.datetime(2017,int(date_time[1:3]),int(date_time[4:6]))
                d2 = datetime.datetime.today()
                days = ( d2 - d1 ).days
                if days > 0:
                    news_info = ['2016-'+date_time[1:3]+'-'+date_time[4:-1],url,title]
                else:
                    news_info = ['2017-'+date_time[1:3]+'-'+date_time[4:-1],url,title]
                news_pool.append(news_info)
            except Exception as e:
                if ':' not in span[i].string:
                    continue
                date_time = span[i].string.split(' ')
                month = date_time[1][1:].replace('/','-')
                minute = date_time[2][0:-1]
                #print(month[0:2])
                #print(month[3:5])
                url = a[i].get('href')
                if url in news_url_set:
                    print("------------Duplicate-------------")
                    continue
                else:
                    news_url_set.extend(url)
                title = a[i].string
                try:
                    d1 = datetime.datetime(2017,int(month[0:2]),int(month[3:5]))
                    d2 = datetime.datetime.today()
                    days = ( d2 - d1 ).days
                    if days > 0:
                        news_info = ['2017-'+month+' '+minute,url,title]
                    else:
                        news_info = ['2016-'+month+' '+minute,url,title]
                except Exception as e:
                    news_info = ['2016-'+month+' '+minute,url,title]
                news_pool.append(news_info)
    return news_pool


def crawl_news(news_pool, min_body_len, doc_dir_path, doc_encoding):
    i = 0
    for news in news_pool:
        try:
            response = urllib.request.urlopen(news[1], timeout=1000)
        except Exception as e:
            try:
                response = urllib.request.urlopen(news[1]+'.shtml', timeout=1000)
            except:
                time.sleep(50)
                try:
                    response = urllib.request.urlopen(news[1], timeout=1000)
                except:
                    print("-----%s: %s-----"%("no response", news[1]))
                    continue
        html = response.read()
        soup = BeautifulSoup(html,"lxml") # http://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/
        try:
            body = soup.find('div', class_ = "text clear").find('div').get_text()
            if body is None:
                body = soup.find('div', class_ = "text").find('article').get_text()
        except Exception as e:
            try:
                body = soup.find('div', class_ = "text").find('article').get_text()
            except Exception as e:
                print("-----%s:body loss %s-----"%(type(e), news[1]))
                continue
        if '//' in body:
            body = body[:body.index('//')]
        body = body.replace(" ", "")
        if len(body) <= min_body_len:
            continue
        try:
            commentnum = GetCommentsNum(news[1])
        except:
            commentnum = "0"
        try:
            cms_id_start = html.decode().find('cms_id')
            cms_id_end = html.decode().find('media_id')
            cms_id = html.decode()[cms_id_start:cms_id_end]
            cms_id = re.search('"(.+)"', cms_id).group(1)
            print('--------' + cms_id + '---------')
            try:
                comments = GetComments(cms_id)
                #print(comments)
            except:
                comments = ["NULL"] 
        except:
            news_id = news[1].split('/')[-1].split('.')[0][1:]
            print('--------' + news_id + '---------')
            try:
                comments = GetComments(news_id)
                #print(comments)
            except:
                comments = ["NULL"] 
        doc = ET.Element("doc")
        ET.SubElement(doc, "source").text = "souhu"
        ET.SubElement(doc, "id").text = "%d"%(i)
        ET.SubElement(doc, "url").text = news[1]
        ET.SubElement(doc, "title").text = news[2]
        ET.SubElement(doc, "datetime").text = news[0]
        ET.SubElement(doc, "body").text = body
        ET.SubElement(doc, "comments").text = '\r\n'.join(comments)
        ET.SubElement(doc, "comments_num").text = commentnum
        tree = ET.ElementTree(doc)
        try:
            tree.write(doc_dir_path + "souhu/" + news[0].replace(' ','-').replace(':','-') + "_%d.xml"%(i), encoding = doc_encoding, xml_declaration = True)
            i += 1
            if i%100 == 0:
                time.sleep(50)
                print('------------' + str(i)+" st. done.-----------")
        except:
            print("--------write failed----------- %s", news[1])
            continue
    
if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('../config.ini', 'utf-8')
    d1 = datetime.datetime(2017,10,18)
    d2 = datetime.datetime.today()
    days = ( d2 - d1 ).days
    news_pool = []
    news_url_set = []
    news_pool = get_news_pool('http://news.sohu.com/1/0903/62/subject212846206', 280, 180, news_url_set);
    news_pool.extend(get_news_pool('http://news.sohu.com/1/0903/61/subject212846158', 1092, 993, news_url_set));
    news_pool.extend(get_news_pool('http://news.sohu.com/1/0903/63/subject212846373', 1161, 1062, news_url_set));
    news_pool.extend(get_news_pool('http://news.sohu.com/1/0903/62/subject212846267', 3771, 3672, news_url_set));
    news_pool.extend(get_news_pool('http://news.sohu.com/s2005/guojihuabian', 2368, 2269, news_url_set));
    news_pool.extend(get_news_pool('http://news.sohu.com/s2006/yuwaihuawen/index', 820, 709, news_url_set));
    crawl_news(news_pool, 5, config['DEFAULT']['doc_dir_path'], config['DEFAULT']['doc_encoding'])
