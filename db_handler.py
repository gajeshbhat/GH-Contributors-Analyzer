import logging
import traceback

from pymongo import MongoClient


class DBHandlers():
    """Handles database methods for the crawler"""
    DB_URI_STRING = ""

    def __init__(self):
        self.DB_URI_STRING = "mongodb://localhost:27017/"
        logging.basicConfig(filename='db_logs.log', level=logging.INFO)

    @staticmethod
    def log_message(message):
        logging.info(msg=message)

    def get_db_new_instance(self):
        db_client = MongoClient(self.DB_URI_STRING)
        dev_info = db_client.dev_info
        return dev_info

    def insert_item(self, cursor, item):
        try:
            cursor.insert_one(item)
        except Exception as e:
            self.log_message("Error in insert_item()" + "\n" + str(traceback.format_exc()))

    def delete_collection(self, cursor):
        try:
            cursor.remove()
        except Exception as e:
            self.log_message("Error in remove() on a collection" + "\n" + str(traceback.format_exc()))

    def insert_item_github(self, item):
        db_client = self.get_db_new_instance()
        github_cursor = db_client.github_info
        self.insert_item(github_cursor, item)

    def delete_github_collection(self):
        db_client = self.get_db_new_instance()
        github_cursor = db_client.github_info
        self.delete_collection(github_cursor)
