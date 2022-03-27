"""Group Members: Matt Moore, Adrian Abeyta, Ahmad Moltafet
"""
import queue
import logging
from datetime import date, datetime
from pymongo import MongoClient
from constants import *

logging.basicConfig(filename='chatroom.log', level=logging.DEBUG, filemode='w')

class ChatUser():
    """ Class for users of the chat system. Users must be registered 
    """
    def __init__(self, alias: str, user_id = None, create_time: datetime = datetime.now(), modify_time: datetime = datetime.now()) -> None:
        logging.info(f'Initializing ChatUser')
        self.__alias = alias
        self.__user_id = user_id 
        self.__create_time = create_time
        self.__modify_time = modify_time
        if self.__user_id is not None:
            self.__dirty = False
        else:
            self.__dirty = True

    def to_dict(self):
        return {
                'alias': self.__alias,
                'create_time': self.__create_time,
                'modify_time': self.__modify_time
        }
        
class UserList(list):
    """ List of users, inheriting list class
    """
    def __init__(self, list_name: str = DEFAULT_USER_LIST_NAME) -> None:
        logging.info(f'Initializing UserList')
        self.__user_list = list()
        self.__mongo_client = MongoClient('mongodb://34.94.157.136:27017/')
        self.__mongo_db = self.__mongo_client.detest
        self.__mongo_collection = self.__mongo_db.users    
        if self.__restore() is True:
            self.__dirty = False
        else:
            self.__name = list_name
            self.__create_time = datetime.now()
            self.__modify_time = datetime.now()
            self.__dirty = True
            
    
    def register(self, new_alias: str) -> ChatUser:
        """ Register a new user alias 
        """
        self.__user_list.append(ChatUser(new_alias))
        self.__dirty = True
        return self.__user_list[-1]

    def get(self, target_alias: str) -> ChatUser:
        """ Returns the user with the given alias
        """
        if len(self.__user_list) == 0:
            raise Exception('User not found')
        for user in self.__user_list:
            if user.__alias == target_alias:
                return user


    def get_all_users(self) -> list:
        """ Returns a list of all users in the list
        """
        return self.__user_list

    def append(self, new_user: ChatUser) -> None:
        """ Append a user to the list
        """
        self.__user_list.append(new_user)
        self.__dirty = True

    def __restore(self) -> bool:
        """ First get the document for the queue itself, then get all documents that are not the queue metadata
        """
        self.__user_list = list()
        self.__dirty = False
        return True


    def __persist(self):
        """ First save a document that describes the user list (name of list, create and modify times)
            Second, for each user in the list create and save a document for that user
        """
        self.__mongo_collection.insert_one({
            'name': self.__name,
            'create_time': self.__create_time,
            'modify_time': self.__modify_time
        })
        for user in self.__user_list:
            self.__mongo_collection.insert_one(user.to_dict())
        self.__dirty = False