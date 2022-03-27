"""Group Members: Matt Moore, Adrian Abeyta, Ahmad Moltafet
"""
import json
import requests
import unittest
import logging
from users import *
from constants import *
from fastapi import FastAPI
from fastapi.testclient import TestClient

MESSAGES = ["first"]
NUM_MESSAGES = 4
logging.basicConfig(filename='chat.log', level=logging.INFO)

app = FastAPI()
client = TestClient(app)

class ChatTest(unittest.TestCase):
    def test_send(self):
        """ Testing the send api
        """
        client.post("/messages", json={"message": "test message"})

    def test_get(self):
        """ Testing the get messages api
        """
        response = client.get("/messages")
        assert len(response.json()) > 0

    def test_register(self):
        """ Testing the user and room registration apis
        """
        # register with Fast API
        client.post("/users", json={"alias": "test_user"})
        client.post("/rooms", json={"room_name": "test_room"})
        user_list = client.get("/users")
        rooms = client.get("/rooms")
        assert len(user_list.json()) == 1
        assert len(rooms.json()) == 1
        

    def test_get_users(self):
        """ Testing the get users api
        """
        client.post("/users", json={"alias": "test_user"})
        users_list = client.get("/users")
        print("he")
        assert len(users_list.json()) == 1

    def test_get_rooms(self):
        """ Testing the get rooms api
        """
        client.post("/rooms", json={"room_name": "test_room"})
        rooms_list = client.get("/rooms")
        assert  len(rooms_list.json()) == 1
    
    def test_response_content(self):
        """ Testing the response content
        """
        client.post("/users", json={"alias": "test_user"})
        client.post("/rooms", json={"room_name": "test_room"})
        users_list = client.get("/users")
        rooms_list = client.get("/rooms")
        assert len(users_list.json()) > 0  
        assert len(rooms_list.json()) > 0
        client.post("/messages", json={"message": "first"})
        client.post("/messages", json={"message": "second"})
        client.post("/messages", json={"message": "third"})
        client.post("/messages", json={"message": "fourth"})
        response = client.get("/messages")
        assert len(response.json()) > 0
        assert response.json()["message"][0]== "first"
        assert response.json()[1]["message"] == "second"
        assert response.json()[2]["message"] == "third"
        assert response.json()[3]["message"] == "fourth"
        
        



            

        

