import socket
import logging
import json
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, ORJSONResponse, Response
from rmq import *
from constants import *
from users import *

MY_IPADDRESS = ""

# This is an extremely rare case where I have global variables. The first is the documented way to deal with running the app in uvicorn, the second is the 
# instance of the rmq class that is necessary across all handlers that behave essentially as callbacks. 


app = FastAPI()
logging.basicConfig(filename='chat.log', level=logging.INFO)

#rmq_private = ChatQueue(private_channel_name="eshner")
#rmq_public = ChatQueue(private_channel_name="eshner")

@app.get("/")
async def index():
    return {"message": {"from": "dan", "to": "you"}}

# 
@app.get("/messages/", status_code=200)
async def get_messages(request: Request, alias: str, exchange_name: str, group_queue: bool = False, messages_to_get: int = GET_ALL_MESSAGES):
    """ Get the messages from the appropriate queue instance. 
        Create the queue instance with what we get from the api
            If we can't find the queue, return the error
        get the messages through message bodies, which will return both messages and the instances. We can return either
        Loop through the messages just for logging

        TODO: the following code is there for when we add users.        
    try:
        users = UserList()
    except:
        users = UserList('chat_users')
    if users.get_by_alias(alias) is None:
        logging.debug(f'Trying to send, have an invalid alias: {alias}')
        return JSONResponse(status_code=410, content="Invalid alias")
    """
    logging.info("starting messages method")
    if (queue_instance := ChatRoom(exchange_name=exchange_name, queue_name=alias, group_queue=group_queue)) is None:
        return JSONResponse(status_code=415, content=f'Chat queue {exchange_name} does not exist.')
    messages, message_objects, total_mess = queue_instance.get_message_bodies(num_messages=messages_to_get, return_objects=True)
    logging.info(f'inside messages handler, after getting messages for queue: {alias}\n messages are {messages}')
    for message in message_objects:
        logging.info(f'Message: {message.message} == message props: {message.mess_props} host is {request.client.host}')
        logging.info(request.json())
    logging.info("End Messages")
    return messages
#    return JSONResponse(status_code=200, content=messages)

@app.get("/users/", status_code=200)
async def get_users():
    """ Code for the api handler to get the list of active users/aliases
    """
    try:
        users = UserList()
    except:
        users = UserList('chat_users')
    if len(users.get_all_users()) > 0:
        return users.get_all_users()
    else:
        return JSONResponse(status_code=405, content="No users have been registered")

@app.post("/register/alias", status_code=201)
async def register_client(client_alias: str, group_alias: bool = False):
    """ Code to register a user/alias. Simple method calls
    """
    try:
        users = UserList()
    except:
        users = UserList('chat_users')
    if users.get_by_alias(client_alias) is None:
        users.register(client_alias, group_alias)
        return "success"
    else:
        return Response(status_code=410, content="User exists already")

@app.post("/create/room")
async def create_room(room_name: str, owner_alias: str, room_type: int = ROOM_TYPE_PRIVATE):
    """ Creating a queue that doesn't exist.
    """
    return JSONResponse(status_code=510, content="Not implemented yet")
    try:
        users = UserList()
    except:
        users = UserList('chat_users')
    if users.get_by_alias(client_alias) is not None:
        users.register(client_alias, group_alias)
        return Response(status_code=201, content="success")
    else:
        return Response(status_code=410, content="User exists already")

@app.post("/send/", status_code=201)
async def send_message(queue_name: str, message: str, from_alias: str, to_alias: str):
    """ POST method for getting messages. We need the following data form the user:
        * room/queue name - for a public queue this is the exchange name
        * what message we're sending
        * to whom and from (the user) - we'll put these in message properties
        Create the ChatRoom instance, create a message properties instance and send the message through the method call
        TODO: the code below is for when we have users and need to check for valid user

    try:
        users = UserList()
    except:
        users = UserList('chat_users')
    if users.get_by_alias(from_alias) is None:
        logging.debug(f'Trying to send, have an invalid sender alias: {from_alias}')
        return JSONResponse(status_code=410, content="Invalid sender alias")
    if users.get_by_alias(to_alias) is None:
        logging.debug(f'Trying to send, have an invalid destination alias: {to_alias}')
        return JSONResponse(status_code=410, content="Invalid destination alias")
    """
    rmq_instance = ChatRoom(queue_name = queue_name, exchange_name=queue_name)
    mess_props = MessProperties(mess_type=MESSAGE_TYPE_SENT, mess_type=MESSAGE_TYPE_SENT, to_user=to_alias, from_user=from_alias)
    if rmq_instance.send_message(message=message, mess_props=mess_props) is True:
        return "Success"
    else:
        return JSONResponse(status_code=410, content="Problems")


def main():
    """ Set up things like logging and a couple of constants
        TODO: not using the constants at this point - remove them if not used
    """
    logging.basicConfig(filename='chat.log', level=logging.INFO)
    MY_IPADDRESS = socket.gethostbyname(socket.gethostname())
    MY_NAME = input("Please enter your name: ")

if __name__ == "__main__":
    main()
