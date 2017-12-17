from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import requests
import re
import json
import os
import configparser
import urllib 
from goose import Goose
from goose.text import StopWordsChinese

#global values
headers = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/\
            537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'}
offset = 0 #
limit = 30 #
max_iter = 30 #

def getCommentsNum(cmt_id):
    s1 = 'http://coral.qq.com/article/'
    u = s1 + str(cmt_id)
    res = requests.get(url=u,headers=headers,timeout=10).content
    data = json.loads(res.decode())
    return data["commentnum"]

def createUrl(cmt_id, number):
    s1 = 'http://coral.qq.com/article/'
    s2 = '/comment?reqnum='
    u = s1 + str(cmt_id) + s2 + str(number)
    return u

def getItemsList(data):
    setComment = set([])
    for key in range(len(data['data']['commentid'])):
        setComment.add(data['data']['commentid'][key]['content'])
    return setComment

def getComments(cmt_id, number):
    comments = []#set([])
    res = requests.get(url=createUrl(cmt_id, number),headers=headers,timeout=10).content
    data = json.loads(res.decode())
    if 'data' in data.keys() and len(data['data']['commentid']) != 0:
        raw_comments = getItemsList(data)
        comments.extend(raw_comments) #=  | comments
    else:
        print("Comment List NULL")
        return set("NULL")
    return set(comments)

def GetNewsLink(newsurl):
    urllist = []
    rightUrlList = ["news.qq.com","finance.qq.com","sports.qq.com","mil.qq.com",\
                        "ent.qq.com","tech.qq.com","auto.qq.com","house.qq.com",\
                            "fashion.qq.com","cul.qq.com","gy.qq.com","stock.qq.com",\
                                "view.inews.qq.com","inews.gtimg.com","view.news.qq.com",\
                                    "gongyi.qq.com","city.qq.com","kuaibao.qq.com"]
    res = requests.get(url=newsurl,headers=headers,timeout=10)
    print("Processing : " + newsurl)
    try:
        tag = BeautifulSoup(res.content.decode('gb18030'), 'lxml')
    except:
        try:
            tag = BeautifulSoup(res.content.decode('gb2312'), 'lxml')
        except:
            try:
                tag = BeautifulSoup(res.content.decode('utf-8'), 'lxml')
            except:
                print("Unknown Link : " + newsurl)
                return ""
    tag = tag.find_all(name='a',limit=10000)
    for aTag in tag:
        if 'href' in aTag.attrs.keys():
            if aTag['href'].split('.')[-1] == 'html' and aTag['href'].split('/')[2] in rightUrlList:
                urllist.append(aTag['href'])
            elif aTag['href'].split(':')[0] == 'http' and aTag['href'].split('.')[-1] == 'htm' and aTag['href'].split('/')[2] in rightUrlList:
                    urllist.append(aTag['href'])
            else:
                pass
    print("Get Link : " + str(len(urllist)))
    return urllist

def GetNewsUrlList(NEWSLimits):
    commentUrlList = []
    urlpool = ['http://mil.qq.com/', 'http://news.qq.com', 'http://society.qq.com', \
                    'http://history.news.qq.com', 'http://cul.qq.com', 'http://tech.qq.com', \
                        'http://auto.qq.com', 'http://mil.qq.com', 'http://sports.qq.com', \
                            'http://finance.qq.com', 'http://view.news.qq.com']
    for newsurl in urlpool:
        try:
            commentUrlList.extend(GetNewsLink(newsurl))
        except:
            continue
    commentUrlList = list(set(commentUrlList))
    tmplist = commentUrlList
    while len(commentUrlList) < NEWSLimits:
        newlist = []
        for newsurl in tmplist:
            try:
                newlist.extend(GetNewsLink(newsurl))
            except:
                continue
            if len(commentUrlList)+len(newlist) > NEWSLimits:
                break
        tmplist = list(set(newlist))
        commentUrlList.extend(tmplist)
    return commentUrlList

def getNumFromTxt(filename):
    c = 0
    fr = open(filename,'rb+')
    for line in fr.readlines():
        c += 1
    return c

def crawl_news(news_pool, min_body_len, doc_dir_path, doc_encoding):
    i = 1
    for newslink in news_pool:
        try:
            response = urllib.request.urlopen(newslink, timeout=10)
            html = response.read()
        except Exception as e:
            print("URL-Request-----%s: %s"%(type(e), newslink))
            continue
        try:
            soup = BeautifulSoup(html, 'lxml') # http://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/
            div1 = soup.find('div',class_='qq_mainArea')
            if repr(div1) != "None":
                cmt_id_start = div1.text.find('cmt_id')
                cmt_id_end = div1.text.find('cmt_is_group')
                cmt_id = div1.text[cmt_id_start+9:cmt_id_end]
                cmt_id_end = cmt_id.find(';')
                cmt_id = cmt_id[0:cmt_id_end]
                title = div1.find('h1').text
                time = div1.find('span',class_='a_time').text
                body = div1.find('div',class_='Cnt-Main-Article-QQ').text
            else:
                continue
            try:
                commentlist = getComments(cmt_id, limit*max_iter)
            except:
                commentlist = ["NULL"]        
            try:
                commentnum = getCommentsNum(cmt_id)    
            except:
                commentnum = str(len(commentlist))
        except:
            print("Crawl URL " + newslink + " failed.")
            commentlist = ["NULL"]
            continue
        doc = ET.Element("doc")
        ET.SubElement(doc, "source").text = "Tencent"
        ET.SubElement(doc, "id").text = "%d"%(i)
        ET.SubElement(doc, "url").text = newslink
        ET.SubElement(doc, "title").text = title
        ET.SubElement(doc, "datetime").text = time#time[0:16]
        body_cleaned = re.sub("[A-Za-z0-9\[\`\~\!\@\#\$\^\&\*\(\)\=\|\{\}\'\:\;\'\,\[\]\.\<\>\/\?\~\！\@\#\\\&\*\%]", "", body)
        if len(body_cleaned)/len(body) <= 0.85:
            try:
                g = Goose({'stopwords_class': StopWordsChinese})
                article = g.extract(url=newslink)
                body = article.cleaned_text
                ET.SubElement(doc, "body").text = body
                #title_cleaned = article.title
            except:
                ET.SubElement(doc, "body").text = body_cleaned
                if len(body_cleaned)/len(body) <= 0.5:
                    ET.SubElement(doc, "body").text = "Potential video or image news."
        else:
            print(len(body_cleaned)/len(body))
            ET.SubElement(doc, "body").text = body
        comment = '\r\n'.join(list(commentlist))
        #comment_cleaned = re.sub("[A-Za-z0-9\[\`\~\!\@\#\$\^\&\*\(\)\=\|\{\}\'\:\;\'\,\[\]\.\<\>\/\?\~\！\@\#\\\&\*\%]", "", comment)
        ET.SubElement(doc, "comments").text = comment
        ET.SubElement(doc, "comments_num").text = commentnum
        tree = ET.ElementTree(doc)
        tree.write(doc_dir_path + time.replace(' ','-').replace(':','-') + "_%d.xml"%(i), encoding = doc_encoding, xml_declaration = True)
        i += 1

def getTodayNews(doc_dir_path, doc_encoding, NEWSLimits):
    NewsUrlList = GetNewsUrlList(NEWSLimits)
    NewsUrlList = list(set(NewsUrlList))
    print("Get "+str(len(NewsUrlList))+" news links")
    crawl_news(NewsUrlList, 10, doc_dir_path, doc_encoding)

if __name__ == '__main__':
    NEWSLimits = 5000;
    config = configparser.ConfigParser()
    config.read('../config.ini', 'utf-8')
    getTodayNews(config['DEFAULT']['doc_dir_path']+'tencent/', config['DEFAULT']['doc_encoding'], NEWSLimits)
