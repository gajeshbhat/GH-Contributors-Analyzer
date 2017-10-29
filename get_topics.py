
import requests
import json
import sys
from BeautifulSoup import BeautifulSoup
from pprint import pprint
reload(sys)
sys.setdefaultencoding('utf8')

def get_reuters_global_feed():
    summary_page = requests.get("https://github.com/topics")
    content_soup = BeautifulSoup(summary_page.content)
    div_soup = content_soup.findAll('li',{'class':'py-4 border-bottom'})

    if(summary_page.status_code != 200):
        print "Error downloading page." 

    topic_json_list=list()
    topic_link_list = list()

    for entry in div_soup:
        topic_entry={
            'topic' : entry.findNext('p',{'class':'f3 lh-condensed mb-0 mt-1 link-gray-dark'}).text,
            'link' : "https://github.com" + entry.findNext('a')['href'],
            'description' : entry.findNext('p',{'class':'f5 text-gray mb-0 mt-1'}).text
        }
        topic_json = json.dumps(topic_entry)
        topic_json_list.append(topic_json)
        topic_link_list.append(str(topic_entry['link']))
    return topic_link_list

def parse_topics(data_topic_list):
    for topic in data_topic_list:
        topic_parse_link = str(topic)
        topics_page = requests.get(topic_parse_link)
        topics_page_soup = BeautifulSoup(topics_page.content)
        outer_div_soup = topics_page_soup.findAll('article',{'class':'border-bottom border-gray-light py-4'})
        for art in outer_div_soup:
            print art.findNext('a')['href']
            #print str(art.findNext('div',{'class':'text-gray mb-3 ws-normal'}).text)
            print "Related tags:\n"
            taglist = art.findNext('div',{'class':'topics-row-container d-flex flex-wrap flex-items-center f6 mb-3'})
            for tag in taglist:
                print tag.findNext('a').text +"\n"
                #print tag.findNext('a')['href'] + "\n"
        print "\n"
#get_reuters_global_feed()
parse_topics(get_reuters_global_feed())