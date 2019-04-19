sudo rm -rf DataBackup
mkdir DataBackup
mongodump --host localhost:27017 --db dev_info -o DataBackup
tar -zcvf DataBackupCompressed.tar.gz DataBackup/
sudo rm -rf DataBackup
