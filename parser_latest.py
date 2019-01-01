#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
from bs4 import BeautifulSoup
import datetime
from time import sleep
from re import findall
from multiprocessing import Pool, cpu_count
from matplotlib import pyplot as plt
from wordcloud import WordCloud, STOPWORDS

query = "Russia"
region = "US"
lang = "en"
base_url = 'https://news.google.com'
search_url = base_url + '/search?q={q}&hl={l}&gl={r}'.format(q=query, l=lang, r=region)


# In[ ]:


def days_amount():
    today = datetime.date.today()
    if today.month in (1,3,5,7,8,10,12): return 31
    elif today.month == 2: return 28 if not today.year % 4 else 29
    else: return 30
    
#TODO: user-agents and proxy
def get_html(url):
    print ('connecting to ' + url)
    while True:
        response = requests.get(url)
        if response.status_code != 200:
            print ('retrying '+url)
            sleep(1)
            continue
        return response.text
   


def get_latest_articles_links(url):
    html = get_html(url)
    soup = BeautifulSoup(html, 'lxml')
    divs = soup.find_all('div',class_='xrnccd')
    links = list(map(lambda x: x.find('a', class_="VDXfz").get("href"), divs))
    dates = list(map(lambda x: int(findall('[0-9]+',x.find('time').get("datetime"))[0]), divs))
    return [base_url+links[i][1:] for i in range(len(links)) if (datetime.date.today() - datetime.date.fromtimestamp(dates[i])).days < days_amount()]

# TODO: smth like a 'smart' algo to extract useful data instead of cleaned DOM
def get_article(url):
    soup = BeautifulSoup(get_html(url), 'lxml')
    [i.extract() for i in soup('script')]
    [i.extract() for i in soup('style')]
    return soup.get_text()

def update_dict(ddict, new):
    for i in new:
        if i in ddict: ddict[i] += new[i]
        else: ddict[i] = new[i]
    return ddict

def word_counter(article):
    words = dict()
    for word in article.split():
        if word.isalnum():
            if word in words: words[word] += 1
            else: words[word] = 1
    return words

def exec_(url):
    article = get_article(url)
    #print (url)
    return word_counter(article)

def main():
    
    articles_urls = get_latest_articles_links(base_url)
    
    
    words = dict()
    with Pool(cpu_count()*2) as p:
        for res in list(p.imap_unordered(exec_, articles_urls)):
            words = update_dict(words,res)
    

    top_words = dict([(w, words[w]) for w in sorted(words, key=words.get, reverse=True) if w.lower() not in STOPWORDS][:50])
    
    
    wdcld = WordCloud(collocations=False, background_color="white", stopwords=STOPWORDS).generate(' '.join(top_words.keys()))
    wdcld.to_file("static/WordCloud.png")
    
    plt.imshow(wdcld, interpolation='bilinear')
    plt.axis("off")
    plt.show()


# In[ ]:


if __name__ == "__main__":
    main()

