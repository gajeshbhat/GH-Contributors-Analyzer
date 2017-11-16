import requests
import json
import sys
import re
from bs4 import BeautifulSoup
from pymongo import MongoClient

client = MongoClient('localhost',27017) # Mongo access client
reload(sys)
sys.setdefaultencoding('utf8') # Prevent unicode error

def parse_and_insert_topic():
    summary_page_before_scroll = requests.get("https://github.com/topics")
    summary_page_after_scroll = requests.get("https://github.com/topics?after=Y3Vyc29yOnYyOpKmc2tldGNozTHp")
    content_soup_0 = BeautifulSoup(summary_page_before_scroll.content,"html.parser")
    content_soup_1 = BeautifulSoup(summary_page_after_scroll.content,"html.parser")
    get_topics_details(content_soup_0)
    get_topics_details(content_soup_1)

def get_topics_details(content_soup):
    div_soup = content_soup.findAll('li',{'class':'py-4 border-bottom'})

    topics_list = list()
    for entry in div_soup:
        topic_entry={
        'topic' : entry.findNext('p',{'class':'f3 lh-condensed mb-0 mt-1 link-gray-dark'}).text,
        'link' : str("https://www.github.com" + entry.findNext('a')['href']).strip(),
        'description' : str(entry.findNext('p',{'class':'f5 text-gray mb-0 mt-1'}).text).strip()
        }
        topics_list.append(topic_entry)
        topics_dump = client.topics_ref
    topics_dump.topics_list.insert_many(topics_list)
    return True

def refresh_topic_list():
    topics_refresh = client.topics_ref
    topics_refresh.topics_list.delete_many({})
    parse_and_insert_topic()
    return True

def process_star_count(x):
    total_stars = 0
    if 'k' in x:
        if len(x) >= 1:
            total_stars = float(x.replace('k', '')) * 1000 # convert K to a thousand
    elif 'M' in x:
        if len(x) > 1:
            total_stars = float(x.replace('M', '')) * 1000000 # convert M to a million
    elif 'B' in x:
            total_stars = float(x.replace('B', '')) * 1000000000 # convert B to a Billion
    else:
            total_stars = int(x) # Less than 1000
        
    return int(total_stars)

def parse_topic_info():
    topic_dicts = client.topics_ref.topics_list.find({}).batch_size(16)
    
    if(topic_dicts == {}):
        print "Topic List empty!"

    topic_desc_list = list()

    for topic in topic_dicts:
        topic_parse_link = str(topic['link'])
        working = False
        while working is False:
            try:
                topics_page = requests.get(topic_parse_link)
                working = True
            except:
                working = False
        topics_page_soup = BeautifulSoup(topics_page.content,"html.parser")
        outer_div_soup = topics_page_soup.findAll('article',{'class':'border-bottom border-gray-light py-4'})
                
        repo_list = list()

        for article in outer_div_soup:
            repo_link = article.findNext('a')['href']
            repo_desc = article.findNext('div',{'class':'text-gray mb-3 ws-normal'}).text
            try:
                repo_lang = article.find('span', {'itemprop':'programmingLanguage'}).text
            except:
                repo_lang = "N/A"
                    
            realted_tag_div = article.findNext('div',{'class':'topics-row-container d-flex flex-wrap flex-items-center f6 mb-3'})
            realted_tag_list = realted_tag_div.findAll('a',{'class':'topic-tag topic-tag-link f6 my-1'})
                    
            stargazer= article.findNext('a',{'class':'d-inline-block link-gray'})
            stargazer_count = process_star_count(str(stargazer.text))
            stargazer_link = stargazer['href']

            related_tags = list()
            
            for tags in realted_tag_list:
                related_tags.append(str(tags.text).strip())
                    
            repo_info={
                'raw_link' : repo_link,
                'description' : str(repo_desc).strip(),
                'lang':str(repo_lang).strip(),
                'stars':str(stargazer_count).strip(),
                'related_tags' : related_tags
                }    
            
            repo_list.append(repo_info)

        topics_dict={
        'topic_name' : topic['topic'],
        'repos' : repo_list
        }

        topic_desc_list.append(topics_dict)
            
    client.topics_ref.topics_details.insert_many(topic_desc_list) # write all the topics into db
    return True
        
def refresh_topic_details():
    client.topics_ref.topics_details.delete_many({})
    parse_topic_info()
    return True
        
def parse_general_repo_information(url=None):
    if(url == None):
        print "Enter a valid url"
        return False
    else:
        working = False
        while working is False:#Handling DNS address exceptions.
            try:
                repo_page = requests.get(url)
                working = True
            except requests.exceptions.ConnectionError:
                working = False

        repo_page_soup = BeautifulSoup(repo_page.content,"lxml")
        all_repo_info = repo_page_soup.find('ul',{'class':'numbers-summary'}).findAll('li')
        all_repo_list = list()
                
        for value in all_repo_info:
            all_repo_list.append(value.findNext('span',{'class':'num text-emphasized'}))
                
        TAG_RE = re.compile(r'<[^>]+>') #Regular exp to cleanup the span tag
                
        desc_data = ''
        
        if repo_page_soup.find('span',{'itemprop':'about'}) == None:
            desc_data = 'N/A'
        else:
            desc_data = str(repo_page_soup.find('span',{'itemprop':'about'}).text).strip()
        
        repo_info_dict={
                    "repo_name":str(repo_page_soup.find('strong',{'itemprop':'name'}).find('a').text),
                    "repo_link":url,
                    "description":desc_data,
                    "total_commits":TAG_RE.sub('',str(all_repo_list[0])).strip(),
                    "total_branches":TAG_RE.sub('',str(all_repo_list[1])).strip(),
                    "total_releases":TAG_RE.sub('',str(all_repo_list[2])).strip(),
                    "total_contributors":TAG_RE.sub('',str(all_repo_list[3])).strip()
                }
        return repo_info_dict