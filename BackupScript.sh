rm -rf MongoDump
mkdir MongoDump
mongodump --host localhost:27017 --db topics_ref -o MongoDump
