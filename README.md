# News-Spider
[Tencent](http://news.qq.com) [NetEase](http://www.163.com) [SouHu](http://news.sohu.com/1/0903/62/subject212846206.shtml) etc. news spider. Including date, title, body and comments of the news. 

### Prerequisites
```
sudo apt-get install python3
sudo pip3 install configparser # or pip3 install configparser --user
sudo pip3 install bs4 
sudo pip3 install datetime
sudo pip3 install requests
```

### How to use ?
```
mkdir ./data
mkdir ./data/tencent
mkdir ./data/souhu
mkdir ./data/netease
mkdir ./data/cankao
cd code
python3 xxx_spider.py # python3 is required !!!
```

### Data Structure
```
<doc>
<source>CanKao News<source>
<id>995</id>
<url>http://www.cankaoxiaoxi.com/china/20170531/2061442.shtml</url>
<title>庆祝香港回归20周年外交部驻港公署举办开放日</title>
<datetime>2017-5-31 8:39</datetime>
<body>图为香港市民在活动现场观摩书法家挥毫泼墨。图为不少香港市民在留言板上签名并写下祝福词句。近日，外交部驻香港特别行政区特派员公署举行主题为“庆祝香港回归20周年”的公众开放日活动，约2500余名香港社会各界人士应邀参加。5月的香港骄阳似火，却挡不住人们高涨的热情。在活动开始前半小时，已有百余名市民在公署门外排队等候进场。家住将军澳的市民郑小姐告诉记者，她与先生及两个孩子早上8点就已出门，“参观公署机会难得，可不能错过开场呀”。</body>
<comments>NULL</comments>
</doc>
```

