"""Group Members: Matt Moore, Adrian Abeyta, Ahmad Moltafet
"""

import re
import pika
import json
import pika.exceptions
import logging
from users import *
from constants import *
from datetime import date, datetime
from pymongo import MongoClient, ReturnDocument, ASCENDING
from collections import deque

logging.basicConfig(filename='chatroom.log', level=logging.DEBUG, filemode='w')

class MessageProperties():
    """ Class for holding the properties of a message: type, sent_to, sent_from, rec_time, send_time
    """
    def __init__(self, room_name: str, to_user: str, from_user: str, mess_type: int, sequence_num: int = -1, sent_time: datetime = datetime.now(), rec_time: datetime = datetime.now()) -> None:
        logging.info(f'Initializing MessageProperties')
        self.__mess_type = mess_type
        self.__room_name = room_name
        self.__to_user = to_user
        self.__from_user = from_user
        self.__sent_time = sent_time
        self.__rec_time = rec_time     
        self.__sequence_num = sequence_num

    def to_dict(self):
        return {'room_name': self.__room_name, 
            'mess_type': self.__mess_type,
            'to_user': self.__to_user, 
            'from_user': self.__from_user,
            'sent_time': self.__sent_time,
            'rec_time': self.__rec_time, 
            'sequence_num': self.__sequence_num,
        } 

    def __str__(self):
        return str(self.to_dict())

class ChatMessage():
    """ Class for holding individual messages in a chat thread/queue. Each message a message, rabbitmq properties, sequence number, timestamp and type
    """
    def __init__(self, message: str, mess_id = None, mess_props: MessageProperties = None) -> None:
        logging.info(f'Initializing ChatMessage')
        self.__message = message
        self.__mess_props = mess_props
        self.__rmq_props = None
        self.__dirty = True
        self.__mess_id = mess_id

    def to_dict(self):
        mess_props_dict = self.__mess_props.to_dict()
        return {'message': self.__message, 'mess_props': mess_props_dict}

    def __str__(self):
        return f'Chat Message: {self.__message} - message props: {self.__mess_props}'

class ChatRoom(deque):
    """ Docstring
        We reuse the constructor for creating new or grabbing an existing instance. If owner_alias is empty and user_alias is not, 
            this is assuming an existing instance. The opposite (owner_alias set and user_alias empty) means we're creating new
            members is always optional, and room_type is only relevant if we're creating new.
    """
    def __init__(self, room_name: str, member_list: list = None, owner_alias: str = "", room_type: int = ROOM_TYPE_PRIVATE, create_new: bool = False) -> None:
        super(ChatRoom, self).__init__()
        logging.info(f'Initializing ChatRoom')
        self.__room_name = room_name
        self.__user_list = UserList()
        self.__room_type = room_type
        self.__owner_alias = owner_alias
        self.__member_list = member_list
        # Set up mongo - client, db, collection, sequence_collection
        self.__mongo_client = MongoClient(host=MONGODB_HOST, port=MONGODB_PORT, username=MONGODB_USER, password=MONGODB_PASS, authSource=MONGO_DB, authMechanism=MONGODB_AUTH_MECH)
        self.__mongo_db = self.__mongo_client.detest
        self.__mongo_collection = self.__mongo_db.get_collection(self.__room_name) 
        self.__mongo_seq_collection = self.__mongo_db.get_collection("sequence")
        if self.__mongo_collection is None:
            self.__mongo_collection = self.__mongo_db.create_collection(self.__room_name)
        if create_new is True:
            self.__mongo_collection.insert_one({'_id': 'userid', 'seq': 0})
        # restore from mongo if possible, if not create new
        

    def __get_next_sequence_num(self):
        """ This is the method that you need for managing the sequence. Note that there is a separate collection for just this one document
        """
        sequence_num = self.__mongo_seq_collection.find_one_and_update(
                                                        {'_id': 'userid'},
                                                        {'$inc': {'seq': 1}},
                                                        projection={'seq': True, '_id': False},
                                                        upsert=True,
                                                        return_document=ReturnDocument.AFTER)
        return sequence_num

    # Overriding the queue type put and get operations to add type hints for the ChatMessage type
    def put(self, message: ChatMessage = None) -> None:
        logging.info(f'Entrered put')
        self.append(message)

    # overriding parent and setting block to false so we don't wait for messages if there are none
    def get(self) -> ChatMessage:
        logging.info(f'Entrered get')
        self.popleft()
        
    def find_message(self, message_text: str) -> ChatMessage:
        """ This method is called by the server to find a message in the chatroom. It is called by the server when the chatroom is closed."""
        logging.info(f'Entrered find_message')
        self.__mongo_collection.find_one({'message': message_text})
        
    def restore(self) -> bool:
        """ This method is called by the server to restore the chatroom from mongo. It is called by the server when the chatroom is closed.
        """
        logging.info(f'Entrered restore')
        self.__mongo_collection.find_one_and_update(
                                                {'_id': 'userid'},
                                                {'$inc': {'seq': 1}},
                                                projection={'seq': True, '_id': False},
                                                upsert=True,
                                                return_document=ReturnDocument.AFTER)
        return True
        
    def clear(self,this_user_alias):
        """ Remove all documents from MongoDB
        """
        logging.info(f'Entrered clear')
        self.__mongo_collection.delete_many(self.get_messages(user_alias=this_user_alias))

    def persist(self):
        """ This method is called by the server to persist the chatroom to mongo. It is called by the server when the chatroom is closed.
        """
        logging.info(f'Entrered persist')
        self.__mongo_collection.insert_one(self.to_dict())

    # CHECK HERE
    def get_messages(self, user_alias: str, num_messages:int=GET_ALL_MESSAGES, return_objects: bool = True):
        """return message texts, full message objects, and total # of messages
        """
        logging.info(f'Entrered get_messages')
        self.__mongo_collection.find({'mess_props.room_name': self.__room_name, 'mess_props.to_user': user_alias}).sort('mess_props.sequence_num', ASCENDING).limit(num_messages)
        if return_objects is True:
            try:
                return self.__mongo_collection.find({'mess_props.room_name': self.__room_name, 'mess_props.to_user': user_alias}).sort('mess_props.sequence_num', ASCENDING).limit(num_messages)
            except:
                return [] # Unable to find any messages
    def send_message(self, message: str, from_alias: str, mess_props: MessageProperties) -> bool:
        """ This is the method that you need for sending messages. Note that there is a separate collection for just this one document
        """
        logging.info(f'Entrered send_message')
        try:
            self.put(ChatMessage(message, mess_props=mess_props))
            # Persist the message to mongo
            self.__mongo_collection.insert_one(mess_props.to_dict())
        except:
            return False
        return True

class RoomList():
    """ Note, I chose to use an explicit private list instead of inheriting the list class
    """
    def __init__(self, name: str = DEFAULT_ROOM_LIST_NAME) -> None:
        """ Try to restore from mongo 
        """
        logging.info(f'Initializing RoomList')
        self.__name = name
        self.__mongo_client = MongoClient(host=MONGODB_URL, port=MONGODB_PORT, username=MONGODB_USER, password=MONGODB_PASS, authSource=MONGO_DB, authMechanism=MONGODB_AUTH_SOURCE_CLASS)
        self.__mongo_db = self.__mongo_client.detest
        self.__mongo_collection = self.__mongo_db.get_collection(self.__name)
        if self.__mongo_collection is None:
            self.__mongo_collection = self.__mongo_db.create_collection(self.__name)
        self.__room_list = []
        self.__room_list_dict = {}
        self.__dirty = True    


    def create(self, room_name: str, owner_alias: str, member_list: list = None, room_type: int = ROOM_TYPE_PRIVATE) -> ChatRoom:
        """ Create a new room
        """
        logging.info(f'Entrered create in RoomList')
        self.__room_list.append(ChatRoom(room_name, member_list, owner_alias, room_type))
        return self.__room_list[-1]

    def add(self, new_room: ChatRoom):
        """ Add a new room to the list
        """
        logging.info(f'Entrered add in RoomList')
        self.__room_list.append(new_room)

    def find_room_in_metadata(self, room_name: str) -> dict:
        """ Find a room in the list by name
        """
        logging.info(f'Entrered find_room_in_metadata in RoomList')
        return self.__room_list[room_name]

    def get_rooms(self):
        """ Get all rooms
        """
        logging.info(f'Entrered get_rooms in RoomList')
        return self.__room_list

    def get(self, room_name: str) -> ChatRoom:
        """ Get a room by name
        """
        logging.info(f'Entrered get in RoomList')
        return self.__room_list[room_name]

    def __find_pos(self, room_name: str) -> int:
        """ Find the position of a room in the list
        """
        logging.info(f'Entrered __find_pos in RoomList')
        return self.__room_list.index(room_name)
    
    def find_by_member(self, member_alias: str) -> list:
        """ Find rooms by member
        """
        logging.info(f'Entrered find_by_member in RoomList')
        return self.__room_list.find_one({'member_list': member_alias})

    def find_by_owner(self, owner_alias: str) -> list:
        """ Find rooms by owner
        """
        logging.info(f'Entrered find_by_owner in RoomList')
        return self.__room_list.find_one({'owner_alias': owner_alias})

    def remove(self, room_name: str):
        """ Remove a room from the list
        """
        logging.info(f'Entrered remove in RoomList')
        self.__room_list.remove(room_name)

    def __persist(self):
        """ Persist the list to mongo
        """
        logging.info(f'Entrered __persist in RoomList')
        self.__mongo_collection.insert_one(self.__room_list)

    def __restore(self) -> bool:
        """ Restore the list from mongo
        """
        logging.info(f'Entrered __restore in RoomList')
        self.__room_list = self.__mongo_collection.find_one()
        if self.__room_list is None:
            return False
        else:
            return True