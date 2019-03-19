from github_trend_scrape import refresh_topic_list, refresh_topic_details
from github_api import refresh_top_devs
refresh_topic_list()
print("Refreshed topic list")
refresh_topic_details()
print("Refreshed Topic details")
#refresh_top_devs()
#print("Refreshed Top developers\t---ALL GOOD---")
