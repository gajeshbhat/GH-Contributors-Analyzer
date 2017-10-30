import requests
import json
import sys
from BeautifulSoup import BeautifulSoup
from pymongo import MongoClient
from pprint import pprint

class Topic_Reference_Dump:
    client = MongoClient('localhost',27017)
    reload(sys)
    sys.setdefaultencoding('utf8') # Prevent unicode error
    
    try:
        def get_topics_details(self):
            summary_page = requests.get("https://github.com/topics")
            content_soup = BeautifulSoup(summary_page.content)
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

            topics_dump = self.client.topics_ref
            topics_dump.topics_list.insert_many(topics_list)
            return True

        def refresh_topic_list(self):
            topics_refresh = self.client.topics_ref
            topics_refresh.topics_list.delete_many({})
            self.get_topics_details()
            return True

        def process_star_count(self,x):
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

        def parse_topic_info(self):
            topic_dicts = self.client.topics_ref.topics_list.find({})
            
            if(topic_dicts == {}):
                return False

            topic_desc_list = list()
            
            for topic in topic_dicts:  
                topic_parse_link = str(topic['link'])
                topics_page = requests.get(topic_parse_link)
                topics_page_soup = BeautifulSoup(topics_page.content)
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
                    stargazer_count = self.process_star_count(str(stargazer.text))
                    stargazer_link = stargazer['href']

                    related_tags = list()
                    for tags in realted_tag_list:
                        related_tags.append(str(tags.text))
                    
                    repo_info={
                        'link' : 'https://github.com' + repo_link,
                        'description' : repo_desc,
                        'lang':repo_lang,
                        'stars':stargazer_count,
                        'related_tags' : related_tags
                    }
                    
                    repo_list.append(repo_info)

                topics_dict={
                'topic_name' : topic['topic'],
                'repos' : repo_list
                }

                topic_desc_list.append(topics_dict)
            
            self.client.topics_ref.topics_details.insert_many(topic_desc_list)
            return True
        
        def refresh_topic_details(self):
            self.client.topics_ref.topics_details.delete_many({})
            self.parse_topic_info()
            return True
    except:
        print Exception