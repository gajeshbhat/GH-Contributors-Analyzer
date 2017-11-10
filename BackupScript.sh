sudo rm -rf MongoBackup
mkdir MongoBackup
mongodump --host localhost:27017 --db topics_ref -o MongoBackup
tar -zcvf MongoBackupCompressed.tar.gz MongoBackup/
