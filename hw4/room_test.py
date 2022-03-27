"""Group Members: Matt Moore, Adrian Abeyta, Ahmad Moltafet
"""

from operator import contains
from datetime import datetime
from unittest import TestCase
import unittest
import logging
from constants import *
from room import ChatRoom, MessageProperties, RoomList

logging.basicConfig(filename='chat.log', level=logging.INFO)

class RoomTest(TestCase):
    """ Docstring
    """
    def setUp(self) -> None:
        """ Setup the test environment
        """
        self.__init__(methodName = 'test_send')
        self.__cur_room = ChatRoom('test-room')
        self.__cur_message = MessageProperties('Adrian sent this message!!!!!!','test-user-to','test_user-from',mess_type=1)

    def test_send(self, private_message: str = DEFAULT_PRIVATE_TEST_MESS, public_message: str = DEFAULT_PUBLIC_TEST_MESS) -> bool:
        """ Testing the send message functionality
        """
        logging.info(f'Starting test_send')
        for test_instance in range(3):
            assert self.__cur_room.send_message(private_message, SENDER_NAME, self.__cur_message) == True
            assert self.__cur_room.send_message(public_message, SENDER_NAME, self.__cur_message) == True
        logging.info(f'Exiting test_send')

    def test_get(self) -> list:
        """ Testing the get messages functionality
        """
        logging.info(f'Starting test_get')
        # No messages so we should
        print(self.__cur_room.get_messages(GET_ALL_MESSAGES))
    
        self.__cur_room.send_message("private_message", SENDER_NAME, self.__cur_message)
        self.__cur_room.send_message("public_message", SENDER_NAME, self.__cur_message)
        assert self.__cur_room.get_messages(GET_ALL_MESSAGES) != []
        logging.info(f'Exiting test_get')
        

    def test_full(self):
        """ Doing both and make sure that what we sent is in what we get back
        """
        logging.info(f'Starting test_full')
        message_solutions = [DEFAULT_PRIVATE_TEST_MESS,DEFAULT_PUBLIC_TEST_MESS]
        self.__cur_room.send_message(DEFAULT_PRIVATE_TEST_MESS, SENDER_NAME, self.__cur_message) == True
        self.__cur_room.send_message(DEFAULT_PUBLIC_TEST_MESS, SENDER_NAME,self.__cur_message) == True
        # Check mongoDB for messages
        for test_index, message in enumerate(self.__cur_room.get_messages(GET_ALL_MESSAGES)):
            assert self.__cur_room.get_messages(GET_ALL_MESSAGES) == message_solutions[test_index]
        logging.info(f'Exiting test_full')
        
if __name__ == "__main__":
    unittest.main()