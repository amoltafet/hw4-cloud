import pika
import pika.exceptions
import logging
from constants import *
from datetime import datetime
from pymongo import MongoClient
from collections import deque

class MessProperties():
    """ Class for holding the properties of a message: type, sent_to, sent_from, rec_time, send_time
    """
    def __init__(self, mess_type: int, to_user: str, from_user: str, sent_time: datetime = datetime.now(), rec_time: datetime = datetime.now()) -> None:
        self.__mess_type = mess_type
        self.__to_user = to_user
        self.__from_user = from_user
        self.__sent_time = sent_time
        self.__rec_time = rec_time      

    def to_dict(self):
        return {'mess_type': self.__mess_type, 
            'to_user': self.__to_user, 
            'from_user': self.__from_user,
            'sent_time': self.__sent_time,
            'rec_time': self.__rec_time
        } 

    def __str__(self):
        return str(self.to_dict())


class RMQProperties():
    """ Class for holding details of rabbitMQ messages. Not using at the moment, perhaps in later versions some of this data will be useful
    """
    def __init__(self, index: int, name: str, consumer_tag: str, delivery_tag: int, exchange: str, redelivered: bool, routing_key: str, \
                synchronous: bool, app_id, cluster_id, content_encoding, content_type, correlation_id, delivery_mode, expiration, headers, \
                message_id, priority, reply_to, timestamp, ptype, user_id) -> None:
        self.index = index
        self.consumer_tag = consumer_tag
        self.delivery_tag = delivery_tag
        self.exchange = exchange
        self.redelivered = redelivered
        self.routing_key = routing_key
        self.synchronous = synchronous
        self.name = name
        self.app_id = app_id
        self.cluster_id = cluster_id
        self.content_encoding = content_encoding
        self.content_type = content_type
        self.correlation_id = correlation_id
        self.delivery_mode = delivery_mode
        self.expiration = expiration
        self.headers = headers
        self.message_id = message_id
        self.priority = priority
        self.reply_to = reply_to
        self.timestamp = timestamp
        self.type = ptype
        self.user_id = user_id


class ChatMessage():
    """ Class for holding individual messages in a chat thread/queue. 
        Each message a message, Message properties, later a sequence number, timestamp
    """
    def __init__(self, message: str = "", mess_props: MessProperties = None, rmq_props = None) -> None:
        self.__message = message
        self.__mess_props = mess_props
        self.__rmq_props = rmq_props
        self.__dirty = True

    @property
    def dirty(self):
        return self.__dirty

    @dirty.setter
    def dirty(self, new_value):
        if type(new_value) is bool:
            self.__dirty = new_value       

    @property
    def message(self):
        return self.__message

    @property
    def rmq_props(self):
        return self.__rmq_props

    @property
    def mess_props(self):
        return self.__mess_props

    def to_dict(self):
        """ Controlling getting data from the class in a dictionary. Yes, I know there is a built in __dict__ but I wanted to retain control
        """
        mess_props_dict = self.mess_props.to_dict()
        return {'message': self.message, 'mess_props': mess_props_dict, 'rmq_props': {}}

    def __str__(self):
        return f'Chat Message: {self.message} - message props: {self.mess_props}'

class ChatRoom(deque):
    """ This is main chat queue class. We're building on top of deque from the collections library.
        First, set up Mongo with the defaults, we have a collection per queue. In that collection is a metadata document
            that describes the queue, and then a bunch of message documents.
        Second, setup rabbitMQ wiht constants - NOTE: each fanout queue has multiple consumers, so need unique queue names
            We only set up the fanout group queue if the type of queue is public
        Third, restore data from Mongo to get back all metadata and messages from the DB that we sent or received previously 
            If we can't restore (__restore returns False) then we're setting up a new queue
    """
    def __init__(self, queue_name: str = DEFAULT_QUEUE_NAME, member_list: list = [], owner_alias: str = "", room_type: int = ROOM_TYPE_PRIVATE, create_new: bool = True) -> None:
        super(ChatRoom, self).__init__()
        self.__member_list = member_list
        self.__owner = owner_alias
        self.add_room_member(self.__owner)
        self.__mongo_client = MongoClient(MONGODB_URL)
        self.__mongo_db = self.__mongo_client.gueshner
        self.__mongo_collection = self.__mongo_db.get_collection(queue_name)

        if self.__mongo_collection is None:
            self.__mongo_collection = self.__mongo_db.create_collection(
                queue_name)       

    def __str__(self):
        return f'Chat Queue. Name: {self.name}'

    @property
    def queue_type(self):
        return self.__queue_type

    @property
    def name(self) -> str: 
        return self.__name     

    @property
    def rmq_channel(self):
        return self.__rmq_channel
    
    @property
    def rmq_queue_name(self):
        return self.__rmq_queue_name

    @property
    def rmq_exchange_name(self):
        return self.__rmq_exchange_name

    @property
    def total_messages(self):
        return self.length()

    
    def put(self, message: ChatMessage = None) -> None:
        """ Overriding the queue type put and get operations to add type hints for the ChatMessage type
            Also, since we can insert messages at either end, we're choosing (arbitrarily) to put on left, read from right
        """
        logging.info(f'Calling Queue put method. message is {message}')
        if message is not None:
            super().appendleft(message)
            self.__persist()

    def length(self) -> int:
        return len(self)

     
    def get(self) -> ChatMessage:
        """ overriding parent and setting block to false so we don't wait for messages if there are none
            Return the last message in the deque (indexing at -1 gets you the last element)
        """
        try:
            new_message = super()[-1]
        except:
            logging.debug("No message in chatqueue.get!!")
            return None
        else:
            return new_message

    def find_message(self, message_text: str) -> ChatMessage:
        """ Go through the deque to find a message object that matches the text. Will return the first such message
            TODO: this should ultimately be done by ID 
        """
        for chat_message in deque:
            if chat_message.message == message_text:
                return chat_message

    def __restore(self) -> bool:
        """ We're restoring data from Mongo. 
            First get the metadata record, but looking for a name key with find_one. If it exists, then we have the doc. If not, bail
                Fill in the metadata (name, create, modify times - we'll do more later)
            Second, we're getting the actual messages. Now we look for the key "message". Note that we're using find so we'll get all that 
                match (every document with a key called 'message')
                For each dictionary we get back (the documents), create a message properties instance and a message instance and
                    put them in the deque by calling the put method
        """
        queue_metadata = self.__mongo_collection.find_one( { 'name': { '$exists': 'true'}})
        if queue_metadata is None:
            return False
        self.__name = queue_metadata["name"]
        self.__create_time = queue_metadata["create_time"]
        self.__modify_time = queue_metadata["modify_time"]
        for mess_dict in self.__mongo_collection.find({ 'message': { '$exists': 'true'}}):
            new_mess_props = MessProperties(
                mess_dict['mess_props']['mess_type'],
                mess_dict['mess_props']['to_user'],
                mess_dict['mess_props']['from_user'],
                mess_dict['mess_props']['sent_time'],
                mess_dict['mess_props']['rec_time']
            )
            new_message = ChatMessage(mess_dict['message'], new_mess_props, None)
            new_message.dirty = False
            self.put(new_message)
        return True

    def __persist(self):
        """ First save a document that describes the user list (metadata: name of list, create and modify times) if it isn't already there
            Second, for each message in the list create and save a document for that user
                NOTE: We're using our custom to_dict so we give Mongo what it wants
        """
        if self.__mongo_collection.find_one({ 'name': { '$exists': 'false'}}) is None:
            self.__mongo_collection.insert_one({"name": self.name, "create_time": self.__create_time, "modify_time": self.__modify_time})
        for message in list(self):
            if message.dirty is True:
                serialized = {'message': message.message,
                            'mess_props': message.mess_props.to_dict(),
                            'rmq_props': message.rmq_props.__dict__ if message.rmq_props is not None else dict(),
                            }
                serialized2 = message.to_dict()
                self.__mongo_collection.insert_one(serialized2)
                message.dirty = False

    def receive_messages(self, message_list):
        """ This is getting messages from Rabbit with a callback. Not use currently, but want it as we may use it later
            Declare the queue and give it a simple callback that we define here. 
            Setup the basic_consume on the channel and start consuming. As messages come in the callback function will be called with the message
        """
        self.rmq_channel.queue_declare(queue='messages')
        def callback(ch, method, properties, body):
            message_list.append(body)
            logging.info(" [x] Received %r" % body)
        self.rmq_channel.basic_consume(queue='messages', on_message_callback=callback, auto_ack=True)
        logging.info(' [*] Waiting for messages. To exit press CTRL+C')
        self.rmq_channel.start_consuming()

    def __retreive_messages(self, num_messages: int = GET_ALL_MESSAGES):
        """ Basic retrieve message function from Rabbit.
            If the channel is closed, we're in bad shape. Issue a warning in logs and bail
            Use consume that will get all messages in the queue. The return is three things:
                1) deliver metadata, what I'm calling m_f - short for message_facts. 
                    NOTE: rare use of short variable name 'm_f' Done because we use that prefix so many times in the constructor call
                2) main message properties - mostly this is what we're using to pass our own properties to rabbit and get them back
                3) the message text
                First, create the RMQ properties instance. Again, we're not using it right now but may come in handy later
                Second, Create a message properties instance with data we absolutely want. For now, it's to_user, from_user, and times
                Finally, create a new message instance with a message properties instance and add it to our queue with the put method
        """
        logging.info("Starting retreive_messages")
        if self.rmq_channel.is_closed:
            logging.warning(f'Inside __retrieve messages, the channel is CLOSED!!')
        logging.info(f'Inside retreive_messages, queue is {self.rmq_queue_name}, exchange: {self.rmq_exchange_name}, cache: {self}, channel: {self.rmq_channel}')
        num_mess_received = 0
        for m_f, props, body in self.rmq_channel.consume(self.rmq_queue_name, auto_ack=True, inactivity_timeout=2):
            num_mess_received += 1
            logging.info(f"inside retreive messages, processing a messsage. body = {body}")
            if body != None:
                new_rmq_props = RMQProperties(m_f.INDEX, m_f.NAME, m_f.consumer_tag, m_f.delivery_tag, m_f.exchange, m_f.redelivered, m_f.routing_key, \
                                                m_f.synchronous, props.app_id, props.cluster_id, props.content_encoding, props.content_type, \
                                                props.correlation_id, props.delivery_mode, props.expiration, props.headers, props.message_id, \
                                                props.priority, props.reply_to, props.timestamp, props.type, props.user_id)
                new_mess_props = MessProperties(
                    MESSAGE_TYPE_RECEIVED, # this is now received, the original will be sent
                    props.headers['_MessProperties__to_user'],
                    props.headers['_MessProperties__from_user'],
                    props.headers['_MessProperties__sent_time'],
                    props.headers['_MessProperties__rec_time']
                )
                new_message = ChatMessage(body.decode('ascii'), new_mess_props, new_rmq_props)
                logging.info(f'Inside retrieve, here is the new chatmessage: {new_message}')
                logging.info(f'Inside retrieve, chatmessage body: {body}\n mess_props: {new_mess_props}\n rmq props: {new_rmq_props}')
                self.put(new_message)
                if num_mess_received >= num_messages:
                    break
            else:
                break
        requeued_messages = self.rmq_channel.cancel()
        logging.info(f'Called cancel after retreive messages, result of that call is {requeued_messages}')
        
    def get_message_objects(self, num_messages: int = GET_ALL_MESSAGES) -> list:
        """ We're returning message instances from our internal queue of messages
            Call __retrieve messages to get any new messages from rabbit
            we loop through the deque by converting the data to a list. Easy way to get an iterator for the internal list
                Stop if we reach the desired number of messages
        """
        logging.info(f'Inside queue get messages. desired messages is (-1 == all): {num_messages}')
        self.__retreive_messages()
        logging.info(f'Inside get_messages, after retreiving messages. num messages: {self.length()} ')
        if num_messages == GET_ALL_MESSAGES:
            return list(self), self.length()
        messages = list()
        cur_num_messages = 0
        for cur_message in list(self):
            if cur_num_messages < num_messages:
                messages.append(cur_message)
                cur_num_messages += 1
            else:
                return messages, cur_num_messages

    def get_message_bodies(self, num_messages:int=GET_ALL_MESSAGES, return_objects: bool = False):
        """ This method returns only the message strings, not the instances of the message class
            Call the method to get the instances, then just iterate through them getting the message text and putting in our list of messages
                Return everything, the messages, the instances, and the number of messages
        """
        logging.info('starting get_messages')
        message_list = list()
        logging.info(f'inside get_messages, target cache is {self.name}')
        messages, total_messages = self.get_message_objects()
        if self.total_messages > 0:
            for message in messages:
                message_list.append(message.to_dict())
                logging.info(f'inside get_messages, adding message to list. Message is {message.message} total messages: {self.total_messages}')
        logging.info(f'Done with get_messages. Total messages: {self.total_messages} -- message list is {message_list}, first element in list: {message_list[0] if len(message_list) > 0 else "no messages"}')
        if return_objects is True:
            return message_list, messages, total_messages
        else:
            return message_list, total_messages

    def send_message(self, message: str, mess_props: MessProperties) -> bool:
        """ Send a message through rabbit, but also create the message instance and add it to our internal queue by calling the internal put method
        """
        try:

            self.rmq_channel.basic_publish(self.rmq_exchange_name, 
                                        routing_key=self.rmq_queue_name, 
                                        properties=pika.BasicProperties(headers=mess_props.__dict__),
                                        body=message, mandatory=True)
            logging.info(f'Publish to messaging server succeeded. Message: {message}')
            self.put(ChatMessage(message=message, mess_props=mess_props))
            return(True)
        except pika.exceptions.UnroutableError:
            logging.debug(f'Message was returned undeliverable. Message: {message} and target queue: {self.rmq_queue}')
            return(False)        

class UserList(list):

    def __init__(self, name: str = 'user_list'):
        self.name = name

    def register(self, client_alias: str, group_alias: bool):
        # adds new ChatRoom to list
        list.append(client_alias)

    def remove(self, user_name: str):
        # removes ChatRoom from list
        list.remove(user_name)

    def get_all_users(self):
        return list

    def get_by_alias(self, user_name: str):
        # see if a user is in the userlist
        for user in list:
            if user == user_name:
                return True
        return None


class RoomList(list):

    def __init__(self, name: str = 'room_list'):
        self.name = name

    def add(self, room_name: str, member_list: list):
        # adds new ChatRoom to list
        new_room = ChatRoom(queue_name=room_name, member_list=member_list,
                            owner_alias="", room_type=ROOM_TYPE_PRIVATE, create_new=True)
        list.append(new_room)

    def remove(self, room_name: str):
        # removes ChatRoom from list
        list.remove(room_name)

    def find(self, room_name: str):
        # find a RoomChat instance by name
        for room in list:
            if room.name() == room_name:
                return room
        return None

    def find_by_member(self, member: str):
        # return all chatrooms that have the alias as a member
        return [room for room in list if member in room.get_member_list()]

    def find_by_owner(self, owner: str) -> list:
        # return all chatrooms that have the alias as the owner
        return [room for room in list if owner == room.get_owner()]

    def persist(self):
        # saving the list metadata

        # After saving or restoring the metadata, iterate through all rooms in the list calling their persist or restore methods
        for room in list:
            room.__persist

    def restore(self):
        # restoring the list metadata

        # After saving or restoring the metadata, iterate through all rooms in the list calling their persist or restore methods
        for room in list:
            room.__restore
