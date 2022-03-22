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
        # Send messages with API
        client.post("/messages", json={"message": "test message"})

    def test_get(self):
        """ Testing the get messages api
        """
        # Get messages using p2p API
        response = client.get("/messages")
        assert response.status_code == 200

    def test_register(self):
        """ Testing the user and room registration apis
        """
        # register user with Fast API
        client.post("/users", json={"alias": "test_user"})
        # register room with Fast API
        client.post("/rooms", json={"room_name": "test_room"})
        # get users with Fast API
        users = client.get("/users")
        # get rooms with Fast API
        rooms = client.get("/rooms")
        assert len(users) > 0
        assert len(rooms) > 0


    def test_get_users(self):
        """ Testing the get users api
        """
        client.post("/users", json={"alias": "test_user"})
        # Get users with API
        users = client.get("/users")
        assert users.status_code == 200
        assert len(users) > 0
        



            

        

