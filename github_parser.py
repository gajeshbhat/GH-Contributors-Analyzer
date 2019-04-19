import requests
import logging
import json
import re
from os import getenv
from bs4 import BeautifulSoup
from db_handler import DBHandlers
from multiprocessing import Process

class GithubParser():
    """Fetches the data from Github"""
    SPAN_TAG_CLEANER = None
    GITHUB_SITE_URL = None
    MAX_TOPIC_ENTRIES = None
    EACH_SLICE_SIZE = None
    GITHUB_API_URL_PREFIX = None
    GITHUB_SITE_URL_POSTFIX = None
    TOTAL_AVAIL_REQUESTS = None
    MAX_HOUR_RATE_LIMIT = None
    github_crawl_details = None
    DATA_EXT_PART_ONE = None
    DATA_EXT_PART_TWO = None

    def __init__(self):
        logging.basicConfig(filename='github.log', level=logging.INFO)
        self.SPAN_TAG_CLEANER = re.compile(r'<[^>]+>')
        self.GITHUB_SITE_URL = "https://www.github.com"
        self.MAX_TOPIC_ENTRIES = 130
        self.EACH_SLICE_SIZE = 5
        self.GITHUB_API_URL_PREFIX = "https://api.github.com/repos"
        self.GITHUB_SITE_URL_POSTFIX = "/contributors?page=1&per_page=100"
        self.DATA_EXT_PART_ONE = "GITDATAEXTKEY_P1"
        self.DATA_EXT_PART_TWO = "GITDATAEXTKEY_P2"
        self.TOTAL_AVAIL_REQUESTS = 5000
        self.MAX_HOUR_RATE_LIMIT = 5000
        self.github_crawl_details = {
        "name": "Github",
        "url" : "https://www.github.com",
        "topics_fetch_urls" : ["https://github.com/topics","https://github.com/topics?after=Y3Vyc29yOnYyOpKmc2tldGNozTHp"],
        "page_layout" : {
        "all_elements_parse":{"tag":'p',"attribute_name":'class',"attribute_value":'py-4 border-bottom'},
        "each_element_parse": {"tag":'p',"attribute_name":'class',"attribute_value_topic_name":'f3 lh-condensed mb-0 mt-1 link-gray-dark',
        "attribute_value_topic_desc":"f5 text-gray mb-0 mt-1"}
        }}

    def log_message(self,message):
        logging.info(msg=message)

    def get_slice_list(self,max_value,each_slice):
        list_slices = list()
        for i in range(0,max_value,each_slice):
            list_slices.append(i)
        return list_slices

    def get_response(self,request_url,headers=None):
        response_value = None
        if headers == None:
            response_value = requests.get(request_url)
        else:
            response_value = requests.get(request_url,headers=headers)
        if response_value.status_code == requests.codes.ok:
            return response_value
        try:
            response_value.raise_for_status
        except Exception as e:
            self.log_message(str("Error for URL "+ request_url + response_value.reason + "\n" + str(traceback.format_exc())))
        return None

    def get_soup(self,request_response):
        return BeautifulSoup(request_response.content,"lxml")

    def find_all_elements(self,page_soup,tag,attribute_name,attribute_value):
        return page_soup.find_all(tag,{attribute_name:attribute_value})

    def find_next_element(self,page_soup,tag,attribute_name,attribute_value):
        return page_soup.find_next(tag,{attribute_name:attribute_value})

    def find_next_element_url(self,entry,tag):
        return  entry.find_next(tag)['href']

    def get_each_topic_detail(self,topic_entry):
        topic_dict = {
        'topic_name' : self.find_next_element(topic_entry,'p','class','f3 lh-condensed mb-0 mt-1 link-gray-dark').text,
        'topic_url' : str("https://www.github.com" + self.find_next_element_url(topic_entry,'a')).strip(),
        'description': str(self.find_next_element(topic_entry,'p','class','f5 text-gray mb-0 mt-1').text).strip()
        }
        return topic_dict

    def get_topics_details(self,page_soup):
        all_topics_details = self.find_all_elements(page_soup,'li','class','py-4 border-bottom')
        topic_desc_list = list()
        for entry in all_topics_details:
            topic_desc_list.append(self.get_each_topic_detail(entry))
        return topic_desc_list

    def is_summary_response_none(self,summary_response):
        return summary_response == None

    def get_topics(self):
        all_topics = list()
        for summary_page in self.github_crawl_details['topics_fetch_urls']:
            summary_response = self.get_response(summary_page)
            if self.is_summary_response_none(summary_response):
                self.log_message("Request failed!" + "for URL " + summary_page)
                return all_topics
            summary_soup = self.get_soup(summary_response)
            topics_list = self.get_topics_details(summary_soup)
            all_topics += topics_list
        return all_topics

    def is_topic_page_query_failed(self,topic_page):
        if topic_page == None:
            return False
        return True

    def get_repo_lang(self,raw_repo_soup):
        repo_lang = ''
        try:
            repo_lang = raw_repo_soup.find('span', {'itemprop':'programmingLanguage'}).text
        except:
            repo_lang = "N/A"
        return str(repo_lang).strip()

    def get_related_tag_list(self,raw_repo_soup):
        related_tag_column_soup = self.find_next_element(raw_repo_soup,'div','class','topics-row-container d-flex flex-wrap flex-items-center f6 mb-3')
        related_tag_list_soup = self.find_all_elements(related_tag_column_soup,'a','class','topic-tag topic-tag-link f6 my-1')
        related_tag_list = list()
        for tags in related_tag_list_soup:
            related_tag_list.append(str(tags.text).strip())
        return related_tag_list

    def process_star_count(self,number_of_stars):
        total_stars = 0
        if 'k' in number_of_stars:
            if len(number_of_stars) >= 1:
                total_stars = float(number_of_stars.replace('k', '')) * 1000
        elif 'M' in number_of_stars:
            if len(number_of_stars) > 1:
                total_stars = float(number_of_stars.replace('M', '')) * 1000000
        elif 'B' in number_of_stars:
            total_stars = float(number_of_stars.replace('B', '')) * 1000000000
        else:
            total_stars = int(number_of_stars) # Less than 1000
        return int(total_stars)

    def get_repo_star_count(self,raw_repo_soup):
        stargazer_soup = self.find_next_element(raw_repo_soup,'a','class','d-inline-block link-gray')
        stargazer_count = 0
        stargazer_link = ''
        if stargazer_soup == None:
            stargazer_count =int(0)
            stargazer_link = 'N/A'
        else:
            stargazer_count = self.process_star_count(str(stargazer_soup.text))
            stargazer_link = stargazer_soup['href']
        return str(stargazer_count).strip()

    def get_repo_basic_info(self,repo_page_soup):
        all_repo_soup = repo_page_soup.find('ul',{'class':'numbers-summary'}).find_all('li')
        all_basic_repo_info_list = list()
        for info in all_repo_soup:
            basic_info_span = self.find_next_element(info,'span','class','num text-emphasized')
            cleaned_span_tag = self.SPAN_TAG_CLEANER.sub('',str(basic_info_span)).strip()
            all_basic_repo_info_list.append(cleaned_span_tag)
        return all_basic_repo_info_list

    def get_repo_basic_desc(self,repo_page_soup):
        desc_data = ''
        if repo_page_soup.find('span',{'itemprop':'about'}) == None:
            desc_data = 'N/A'
        else:
            desc_data = str(repo_page_soup.find('span',{'itemprop':'about'}).text).strip()
        return desc_data

    def get_clean_repo_details(self,repo_page_soup,repo_url):
        all_basic_repo_info = self.get_repo_basic_info(repo_page_soup)
        repo_basic_desc = self.get_repo_basic_desc(repo_page_soup)
        repo_info_dict={
            "repo_name":str(repo_page_soup.find('strong',{'itemprop':'name'}).find('a').text),
            "repo_link":repo_url,
            "description":repo_basic_desc,
            "total_commits":all_basic_repo_info[0],
            "total_branches":all_basic_repo_info[1],
            "total_releases":all_basic_repo_info[2],
            "total_contributors":all_basic_repo_info[3]
        }
        return repo_info_dict

    def get_gen_repo_info(self,repo_url):
        repo_url = self.GITHUB_SITE_URL + repo_url
        repo_basic_details_response = self.get_response(repo_url)
        repo_basic_page_working = self.is_topic_page_query_failed(repo_basic_details_response)
        while repo_basic_page_working is False:
            repo_basic_details_response = self.get_response(repo_url)
            repo_basic_page_working = self.is_topic_page_query_failed(repo_basic_details_response)
        repo_page_soup = self.get_soup(repo_basic_details_response)
        clean_repo_detail = self.get_clean_repo_details(repo_page_soup,repo_url)
        return clean_repo_detail

    def get_api_response_default(self):
        return {"message" : "Not found!"}

    def get_top_contributor_list(self,url):
        if self.MAX_HOUR_RATE_LIMIT == 0:
            self.DATA_EXT_PART_ONE = self.DATA_EXT_PART_TWO
            self.MAX_HOUR_RATE_LIMIT = self.TOTAL_AVAIL_REQUESTS
        headers = {'Authorization': 'token %s' % getenv(str(self.DATA_EXT_PART_ONE))}
        api_response = self.get_response(str(self.GITHUB_API_URL_PREFIX + url + self.GITHUB_SITE_URL_POSTFIX),headers)
        self.MAX_HOUR_RATE_LIMIT-=1
        if api_response == None:
            return json.loads(self.get_api_response_default())
        return json.loads(api_response.content)

    def get_clean_repo_info(self,raw_repo_soup):
        repo_clean_info = {
        'raw_repo_link' : self.find_next_element_url(raw_repo_soup,'a'),
        'repo_description' : str(self.find_next_element(raw_repo_soup,'div','class','text-gray mb-3 ws-normal').text).strip(),
        'repo_dominant_language':self.get_repo_lang(raw_repo_soup),
        'related_tag_list' : self.get_related_tag_list(raw_repo_soup),
        'number_of_stars' : self.get_repo_star_count(raw_repo_soup),
        'general_repo_info' : self.get_gen_repo_info(str(self.find_next_element_url(raw_repo_soup,'a'))),
        'repo_contributors' : self.get_top_contributor_list(str(self.find_next_element_url(raw_repo_soup,'a'))),
        }
        return repo_clean_info

    def get_all_repo_info(self,topic_page_soup):
        repo_list_soup = self.find_all_elements(topic_page_soup,'article','class','border-bottom border-gray-light py-4')
        all_repos_in_topics = list()
        for repo in repo_list_soup:
            formatted_repo_info = self.get_clean_repo_info(repo)
            all_repos_in_topics.append(formatted_repo_info)
        return all_repos_in_topics

    def get_topic_detail_formatted(self,topic,repo_list):
        topic_info = {
        'topic' : topic['topic_name'],
        'repositories' : repo_list
        }
        return topic_info

    def get_repos_of_topic(self,start_set,end_set):
        all_topics_details = self.get_topics()
        db_obj = DBHandlers()
        for topic in all_topics_details[start_set:end_set]:
            topic_page_response = self.get_response(str(topic['topic_url']))
            topic_page_working = self.is_topic_page_query_failed(topic_page_response)
            while topic_page_working is False:
                topic_page_response = self.get_response(str(topic['topic_url']))
                topic_page_working = self.is_topic_page_query_failed(topic_page_response)
            topics_page_soup = self.get_soup(topic_page_response)
            topic_details_formatted = self.get_topic_detail_formatted(topic,self.get_all_repo_info(topics_page_soup))
            db_obj.insert_item_github(topic_details_formatted)

    def parse_full_data(self):
        slice_list = self.get_slice_list(self.MAX_TOPIC_ENTRIES,self.EACH_SLICE_SIZE)
        for i in range(1,len(slice_list)):
            current_process = Process(target=self.get_repos_of_topic,args=(slice_list[i-1],slice_list[i]))
            current_process.start()

    def hard_refresh(self):
        db_obj = DBHandlers()
        db_obj.delete_github_collection()
        self.parse_full_data()
