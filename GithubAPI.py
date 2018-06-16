import requests
import json
import time
from pymongo import MongoClient
from os import getenv
from GithubTrendScrape import client,parse_general_repo_information
from multiprocessing import Process

def get_top_contributor_list(url):
  headers = {'Authorization': 'token %s' % getenv('GITDATAEXTKEY')}
  working = False
  
  while working is False:
    try:
      response = requests.get(url,headers=headers)
      working = True
    except:
      working = False
      time.sleep(5)

  contrib_json = json.loads(response.content)
  return contrib_json

def get_top_devs_segment1():
  client0 = MongoClient('localhost',27017)
  for topic in client0.topics_ref.topics_details.find()[0:28]:
    topic_repos = topic['repos']
    top_dev_list = list()
    
    topic_dict={
    "topic_name":topic['topic_name'],
    }
    
    for repo in topic_repos:
      repo_info = parse_general_repo_information("https://github.com"+str(repo['raw_link']))
      repo_devs_list = get_top_contributor_list("https://api.github.com/repos"+str(repo['raw_link'])+"/contributors?page=1&per_page=100")
      repo_info['top_contributors']= repo_devs_list
      top_dev_list.append(repo_info)
    
    topic_dict["top_developers"] = top_dev_list
    client.contrib_details.top_devs.insert(topic_dict)
    print "Dumped " + topic['topic_name']

def get_top_devs_segment2():
  client1 = MongoClient('localhost',27017)
  for topic in client1.topics_ref.topics_details.find()[28:56]:
    topic_repos = topic['repos']
    top_dev_list = list()
    
    topic_dict={
    "topic_name":topic['topic_name'],
    }
    
    for repo in topic_repos:
      repo_info = parse_general_repo_information("https://github.com"+str(repo['raw_link']))
      repo_devs_list = get_top_contributor_list("https://api.github.com/repos"+str(repo['raw_link'])+"/contributors?page=1&per_page=100")
      repo_info['top_contributors']= repo_devs_list
      top_dev_list.append(repo_info)
    
    topic_dict["top_developers"] = top_dev_list
    client.contrib_details.top_devs.insert(topic_dict)
    print "Dumped " + topic['topic_name']

def get_top_devs_segment3():
  client2 = MongoClient('localhost',27017)
  for topic in client2.topics_ref.topics_details.find()[56:84]:
    topic_repos = topic['repos']
    top_dev_list = list()
    
    topic_dict={
    "topic_name":topic['topic_name'],
    }
    
    for repo in topic_repos:
      repo_info = parse_general_repo_information("https://github.com"+str(repo['raw_link']))
      repo_devs_list = get_top_contributor_list("https://api.github.com/repos"+str(repo['raw_link'])+"/contributors?page=1&per_page=100")
      repo_info['top_contributors']= repo_devs_list
      top_dev_list.append(repo_info)
    
    topic_dict["top_developers"] = top_dev_list
    client.contrib_details.top_devs.insert(topic_dict)
    print "Dumped " + topic['topic_name']

def get_top_devs_segment4():
  client3 = MongoClient('localhost',27017)
  for topic in client3.topics_ref.topics_details.find()[84:115]:
    topic_repos = topic['repos']
    top_dev_list = list()
    
    topic_dict={
    "topic_name":topic['topic_name'],
    }
    
    for repo in topic_repos:
      repo_info = parse_general_repo_information("https://github.com"+str(repo['raw_link']))
      repo_devs_list = get_top_contributor_list("https://api.github.com/repos"+str(repo['raw_link'])+"/contributors?page=1&per_page=100")
      repo_info['top_contributors']= repo_devs_list
      top_dev_list.append(repo_info)
    
    topic_dict["top_developers"] = top_dev_list
    client.contrib_details.top_devs.insert(topic_dict)
    print "Dumped " + topic['topic_name']


def refresh_top_devs():
  client.contrib_details.top_devs.delete_many({})
  p0= Process(target=get_top_devs_segment1)
  p0.start()
  p1= Process(target=get_top_devs_segment2)
  p1.start()
  p2= Process(target=get_top_devs_segment3)
  p2.start()
  p3= Process(target=get_top_devs_segment4)
  p3.start()
  print "\nAll Process started. Gathering all the top Developers info. This may take a while ."  
  