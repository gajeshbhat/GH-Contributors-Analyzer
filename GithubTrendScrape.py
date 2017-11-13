import requests
import json
import sys
import re
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pprint import pprint
from subprocess import call
from os import getcwd
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from selenium import common
from multiprocessing import Process

client = MongoClient('localhost',27017) # Mongo access client
reload(sys)
sys.setdefaultencoding('utf8') # Prevent unicode error

segment_0_topics = list()
segment_1_topics = list()
segment_2_topics = list()
segment_3_topics = list()

def get_topic_slices():
    all_topics = client.topics_ref.topics_details.find({}).batch_size(16)
    idx = int(0)
    for topic in all_topics:
        if idx >= 0 and idx <=25:
            segment_0_topics.append(topic)
        elif idx > 25 and idx <= 50:
            segment_1_topics.append(topic)
        elif idx > 50 and idx <=75:
            segment_2_topics.append(topic)
        else:
            segment_3_topics.append(topic)
        idx+=1
    return True

def get_topics_details():
    summary_page = requests.get("https://github.com/topics")
    content_soup = BeautifulSoup(summary_page.content,"html.parser")
    div_soup = content_soup.findAll('li',{'class':'py-4 border-bottom'})

    if(summary_page.status_code != 200):
        print "Error downloading page." 
        return False
            
    topics_list = list()
    for entry in div_soup:
        topic_entry={
        'topic' : entry.findNext('p',{'class':'f3 lh-condensed mb-0 mt-1 link-gray-dark'}).text,
        'link' : "https://github.com" + entry.findNext('a')['href'],
        'description' : entry.findNext('p',{'class':'f5 text-gray mb-0 mt-1'}).text
        }
        topics_list.append(topic_entry)
        topics_dump = client.topics_ref
    topics_dump.topics_list.insert_many(topics_list)
    return True

def refresh_topic_list():
    topics_refresh = client.topics_ref
    topics_refresh.topics_list.delete_many({})
    get_topics_details()
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
    topic_dicts = client.topics_ref.topics_list.find({})
    
    if(topic_dicts == {}):
        return False

    topic_desc_list = list()

    for topic in topic_dicts:
        topic_parse_link = str(topic['link'])
        topics_page = requests.get(topic_parse_link)
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
                'link' : 'https://www.github.com' + repo_link,
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

def parse_contributors_data(raw_contrib_soup):
    all_contributors_soup = raw_contrib_soup.findAll('li',{'class':'contrib-person float-left col-6 pr-2 my-2'})
    all_contributors_list = list()
    for contributor in all_contributors_soup:
        contributor_dict={
        "user_id":contributor.findNext('a').text,
        "profile_link":"https://www.github.com" + contributor.findNext('a',{'class':'text-normal'})['href'],
        "rank":contributor.findNext('span',{'class':'f5 text-normal text-gray-light float-right'}).text,
        "total_contributions":contributor.findNext('a',{'class':'link-gray text-normal'}).text,
        "total_commits_url":contributor.findNext('a',{'class':'link-gray text-normal'})['href'],
        "total_additions":contributor.findNext('span',{'class':'text-green text-normal'}).text,
        "total_subtractions":contributor.findNext('span',{'class':'text-red text-normal'}).text
        }
        all_contributors_list.append(contributor_dict)
    return all_contributors_list

def get_loading_page_data(url=None):
    if(url == None):
        print "Please enter a valid url."
        return False         
    else:
        browser_options = Options() # Options Object from the Selenium driver.
        browser_options.add_argument('-headless') # No GUI. More references at : https://developer.mozilla.org/en-US/Firefox/Headless_mode#Selenium_in_python
        browser = webdriver.Firefox(executable_path='geckodriver', firefox_options=browser_options)         
        working = False
        while working is False:
            try:
                browser.get(str(url+"/graphs/contributors")) #Handle Webdriver Selenium Exception.
                working = True
            except common.exceptions.WebDriverException:
                working = False

        loaded_page_soup = BeautifulSoup(browser.page_source, "html.parser")
        browser.quit()
        return loaded_page_soup
        
def get_general_repo_information(url=None):
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

def get_top_contributor_info(topic,all_topic_repos):
    repo_contributor_list = list()
    
    for repo in all_topic_repos:
        repo_link = repo['link']
        repo_dict = get_general_repo_information(url=repo_link)
        contributor_page_soup = get_loading_page_data(url=repo_link)
        top_contributors_list = parse_contributors_data(contributor_page_soup)
        print top_contributors_list
        if top_contributors_list == None:
            top_contributors_list = []

        repo_dict['top_contributors'] = top_contributors_list
        repo_contributor_list.append(repo_dict)
    
    topic_contrib ={
    "topic_name":topic["topic_name"],
    "top_developers": repo_contributor_list
    }
    
    return topic_contrib

def get_contributors_details_segment_0():
    all_topics =  segment_0_topics 
            
    for topic in all_topics:
        all_topic_repos = topic['repos']
        topic_document = get_top_contributor_info(topic,topic['repos'])
        segment_0_MongoClnt = MongoClient('localhost',27017)
        segment_0_MongoClnt.contrib_details.top_contributors_segment_0.insert(topic_document)
        print topic['topic_name'] + " is dumped."

    return True

def get_contributors_details_segment_1():
    all_topics =  segment_1_topics 
            
    for topic in all_topics:
        all_topic_repos = topic['repos']
        topic_document = get_top_contributor_info(topic,topic['repos'])
        segment_1_MongoClnt = MongoClient('localhost',27017)
        segment_1_MongoClnt.contrib_details.top_contributors_segment_1.insert(topic_document)

        print topic['topic_name'] + " is dumped."
    return True
       
def get_contributors_details_segment_2():
    all_topics =  segment_2_topics 
         
    for topic in all_topics:
        all_topic_repos = topic['repos']
        topic_document = get_top_contributor_info(topic,topic['repos'])
        segment_2_MongoClnt = MongoClient('localhost',27017)
        segment_2_MongoClnt.contrib_details.top_contributors_segment_2.insert(topic_document)

        print topic['topic_name'] + " is dumped."
    return True

def get_contributors_details_segment_3():
    all_topics =  segment_3_topics 
            
    for topic in all_topics:
        all_topic_repos = topic['repos']
        topic_document = get_top_contributor_info(topic,topic['repos'])
        segment_3_MongoClnt = MongoClient('localhost',27017)
        segment_3_MongoClnt.contrib_details.top_contributors_segment_3.insert(topic_document)

        print topic['topic_name'] + " is dumped."
    return True

def refresh_contributor_details():
    get_topic_slices()

    p0= Process(target=get_contributors_details_segment_0)
    p0.start()
    print "Started 0th Process."

    p1= Process(target=get_contributors_details_segment_1)
    p1.start()
    print "Started 1st Process."

    p2= Process(target=get_contributors_details_segment_2)
    p2.start()
    print "Started 2nd Process."

    p3= Process(target=get_contributors_details_segment_3)
    p3.start()
    print "Started 3rd Process."  