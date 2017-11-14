from GithubTrendScrape import get_contributors_details, refresh_topic_list, refresh_topic_details
refresh_topic_list()
print "Topic list refreshed"
refresh_topic_details()
print "Topic details refreshed"
print "Starting Contributors list fetch. This may take a while..."
get_contributors_details()
print "DONE!------ ALL GOOD ------"