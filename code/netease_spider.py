from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import requests
import re
import json
import os
import configparser
import urllib 

#global values
headers = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/\
            537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'}
offset = 0 #
limit = 10 #
max_iter = 3 #


def createUrl(commentUrl,offset,limit):
    s1 = 'http://comment.news.163.com/api/v1/products/a2869674571f77b5a0867c3d71db5856/threads/'
    s2 = '/comments/newList?offset='
    name = commentUrl.split('/')[-1].split('.')[0]
    u = s1 + str(name) + s2 + str(offset) + '&limit=' + str(limit)
    return u

def getItemsList(data):
    setComment = set([])
    for key in data['comments'].keys():
        setComment.add(data['comments'][key]['content'])
    return setComment

def getComments(commentUrl):
    global limit
    global offset
    comments = []#set([])
    i = 0
    while(i<max_iter):
        res = requests.get(url=createUrl(commentUrl,offset,limit),headers=headers,timeout=10).content
        data = json.loads(res.decode())
        if 'comments' in data.keys() and len(data['comments'].keys()) != 0:
            raw_comments = str(getItemsList(data)).replace("<br>","")
            raw_comments = raw_comments[1:-2]
            raw_comments = raw_comments.split(',')
            comments.extend(raw_comments) #=  | comments
            offset += (limit+1)
        else:
            break
        i += 1
    offset = 0
    return set(comments)

def GetNewsLink(newsurl):
    urllist = []
    rightUrlList = ["news.163.com","view.163.com","ent.163.com","auto.163.com","tech.163.com","sports.163.com","war.163.com","money.163.com","lady.163.com"]
    print("Processing : " + newsurl)
    res = requests.get(url=newsurl,headers=headers)
    tag = BeautifulSoup(res.content.decode('gb18030'), 'lxml')
    tag = tag.find_all(name='a',limit=10000)
    for aTag in tag:
        if 'href' in aTag.attrs.keys():
            if aTag['href'].split('.')[-1] == 'html' and aTag['href'].split('/')[2] in rightUrlList:
                urllist.append(aTag['href'])
    print("Get Link : " + str(len(urllist)))
    return urllist

def GetNewsUrlList(NEWSLimits):
    commentUrlList = []
    urlpool = ['http://www.163.com', 'http://news.163.com/rank', 'http://news.163.com', 'http://news.163.com/domestic', 'http://news.163.com/world', 'http://news.163.com/shehui']
    for newsurl in urlpool:
        try:
            commentUrlList.extend(GetNewsLink(newsurl))
        except:
            continue
    tmplist = list(set(commentUrlList))
    while len(commentUrlList) < NEWSLimits:
        newlist = []
        for newsurl in tmplist:
            try:
                newlist.extend(GetNewsLink(newsurl))
            except:
                print("Error URL : " + newsurl)
                continue
        tmplist = list(set(newlist))
        print("Get candidate ULRs : " + str(len(tmplist)))
        if len(tmplist) == 0:
            break
        commentUrlList.extend(tmplist)
    return commentUrlList

def crawl_news(news_pool, min_body_len, doc_dir_path, doc_encoding):
    i = 1
    news_pool = set(news_pool)
    for newslink in news_pool:
        try:
            response = urllib.request.urlopen(newslink)
            html = response.read()
        except Exception as e:
            print("URL-Request-----%s: %s"%(type(e), newslink))
            continue
        try:
            soup = BeautifulSoup(html, 'lxml') # http://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/
            div1 = soup.find('div',class_='post_content_main')
            if repr(div1) != "None":
                title = div1.find('h1').text
                post_time_source = div1.find('div',class_='post_time_source').text
                time = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}\:\d{2}',post_time_source).group(0)
                body = div1.find('div',class_='post_text').text
                rindex = body.rfind("(NTES);")
                lindex = body.find("#endT")
                if lindex != -1 and rindex != -1:
                    body = body[0:lindex] + body[rindex+7:-1]
                elif lindex == -1 and rindex == -1:
                    pass
                else:
                    continue
            else:
                continue
            try:
                commentlist = getComments(newslink)
            except:
                commentlist = ["NULL"]
        except:
            print("Crawl News " + newslink + "failed.")
            commentlist = ["NULL"]
            continue
        doc = ET.Element("doc")
        ET.SubElement(doc, "source").text = "NetEase"
        ET.SubElement(doc, "id").text = "%d"%(i)
        ET.SubElement(doc, "url").text = newslink
        ET.SubElement(doc, "title").text = title
        ET.SubElement(doc, "datetime").text = time[0:16]
        ET.SubElement(doc, "body").text = body
        ET.SubElement(doc, "comments").text = '\r\n'.join(list(commentlist))
        tree = ET.ElementTree(doc)
        tree.write(doc_dir_path + time[0:16].replace(' ','-').replace(':','-') + "_%d.xml"%(i), encoding = doc_encoding, xml_declaration = True)
        i += 1

def getTodayNews(doc_dir_path, doc_encoding, NEWSLimits):
    NewsUrlList = GetNewsUrlList(NEWSLimits)
    NewsUrlList = list(set(NewsUrlList))
    print("Get " + str(len(NewsUrlList)) + " URLs.")
    crawl_news(NewsUrlList, 10, doc_dir_path, doc_encoding)

if __name__ == '__main__':
    NEWSLimits = 100000;
    config = configparser.ConfigParser()
    config.read('./config.ini', 'utf-8')
    getTodayNews(config['DEFAULT']['doc_dir_path']+'netease/', config['DEFAULT']['doc_encoding'], NEWSLimits)
