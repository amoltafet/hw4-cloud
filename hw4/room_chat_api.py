"""Group Members: Matt Moore, Adrian Abeyta, Ahmad Moltafet
"""
import socket
import logging
import json
from fastapi import FastAPI, Request, status, Form
from fastapi.responses import JSONResponse, ORJSONResponse, Response
from fastapi.templating import Jinja2Templates
from rmq import *
from room import *
from constants import *
from users import *

MY_IPADDRESS = ""

# This is an extremely rare case where I have global variables. The first is the documented way to deal with running the app in uvicorn, the second is the 
# instance of the rmq class that is necessary across all handlers that behave essentially as callbacks. 

app = FastAPI()
room_list = RoomList()
users = UserList()
templates = Jinja2Templates(directory="")
logging.basicConfig(filename='chat.log', level=logging.INFO)

@app.get("/")
async def index():
    """ Default page
    """
    return templates.TemplateResponse("index.html", {"request": Request})

@app.get("/page/send", status_code=200)
async def send_form(request: Request):
    """ HTML GET page form sending a message
    """
    return templates.TemplateResponse("send_message.html", {"request": request})

@app.post("/page/send", status_code=201)
async def get_form(request: Request, room_choice: str = Form(...), message: str = Form(...), alias: str = Form(...)):
    """ HTML POST page for sending a message
    """
    logging.info(f'inside send message handler, room choice is {room_choice}')
    if room_choice not in room_list.get_rooms():
        logging.info(f'room choice is {room_choice}')
        return JSONResponse(status_code=415, content=f'Chat room {room_choice} does not exist.')
    if users.get(alias) is None:
        logging.info(f'Trying to send, have an invalid alias: {alias}')
        return JSONResponse(status_code=410, content="Invalid alias")
    logging.info(f'inside send message handler, room choice is {room_choice}')
    room = room_list.get(room_choice)
    logging.info(f'inside send message handler, room choice is {room_choice}')
    room.send_message(message, alias)
    logging.info(f'inside send message handler, room choice is {room_choice}')
    return JSONResponse(status_code=201, content=f'Message sent to room {room_choice}')

@app.get("/page/messages", status_code=200)
async def form_messages(request: Request, room_name: str = DEFAULT_PUBLIC_ROOM):
    """ HTML GET page for seeing messages
    """
    logging.info(f'inside messages handler, room name is {room_name}')
    if room_name not in room_list.get_rooms():
        logging.info(f'room name is {room_name}')
        return JSONResponse(status_code=415, content=f'Chat room {room_name} does not exist.')
    room = room_list.get(room_name)
    logging.info(f'inside messages handler, room name is {room_name}')
    return JSONResponse(status_code=200, content=room.get_messages())
    
@app.post("/page/messages", status_code=201)
async def form_messages(request: Request, room_name: str = Form(...)):
    """ HTML POST page for seeing messages in a different room or different quantities
    """
    logging.info(f'inside messages handler, room name is {room_name}')
    if room_name not in room_list.get_rooms():
        logging.info(f'room name is {room_name}')
        return JSONResponse(status_code=415, content=f'Chat room {room_name} does not exist.')
    room = room_list.get(room_name)
    logging.info(f'inside messages handler, room name is {room_name}')
    return JSONResponse(status_code=200, content=room.get_messages())

@app.get("/messages/", status_code=200)
async def get_messages(request: Request, alias: str, room_name: str, messages_to_get: int = GET_ALL_MESSAGES):
    """ API for getting messages
    """
    logging.info("starting messages method")
    if (queue_instance := ChatRoom(room_name=room_name, queue_name=alias)) is None:
        return JSONResponse(status_code=415, content=f'Chat queue {room_name} does not exist.')
    messages, message_objects, total_mess = queue_instance.get_message_bodies(num_messages=messages_to_get, return_objects=True)
    logging.info(f"messages: {messages}")
    logging.info(f"message_objects: {message_objects}")
    logging.info(f"total_mess: {total_mess}")
    return JSONResponse(status_code=200, content=messages)

@app.get("/users/", status_code=200)
async def get_users():
    """ API for getting users
    """
    logging.info("starting users method")
    users_list = users.get_all_users()
    logging.info(f"users_list: {users_list}")
    return JSONResponse(status_code=200, content=users_list)

@app.post("/alias", status_code=201)
async def register_client(client_alias: str, group_alias: bool = False):
    """ API for adding a user alias
    """
    logging.info("starting alias method")
    if (client_alias := users.register(client_alias, group_alias)) is None:
        return JSONResponse(status_code=415, content=f'Alias {client_alias} already exists.')
    logging.info(f"client_alias: {client_alias}")
    return JSONResponse(status_code=200, content=client_alias)

@app.post("/room")
async def create_room(room_name: str, owner_alias: str, room_type: int = ROOM_TYPE_PRIVATE):
    """ API for creating a room
    """
    logging.info("starting room method")
    if (room_name := room_list.add_room(room_name, owner_alias, room_type)) is None:
        return JSONResponse(status_code=415, content=f'Room {room_name} already exists.')
    logging.info(f"room_name: {room_name}")
    return JSONResponse(status_code=200, content=room_name)

@app.post("/message/", status_code=201)
async def send_message(room_name: str, message: str, from_alias: str, to_alias: str):
    """ API for sending a message
    """
    logging.info("starting message method")
    if (queue_instance := ChatRoom(room_name=room_name, queue_name=from_alias)) is None:
        return JSONResponse(status_code=415, content=f'Chat queue {room_name} does not exist.')
    if (message := queue_instance.send_message(message, to_alias)) is None:
        return JSONResponse(status_code=415, content=f'Message {message} could not be sent.')
    logging.info(f"message: {message}")
    return JSONResponse(status_code=200, content=message)

def main():
    logging.basicConfig(filename='chat.log', level=logging.INFO)
    MY_IPADDRESS = socket.gethostbyname(socket.gethostname())
    MY_NAME = input("Please enter your name: ")

if __name__ == "__main__":
    main()
