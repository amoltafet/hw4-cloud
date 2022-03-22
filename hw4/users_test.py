"""Group Members: Matt Moore, Adrian Abeyta, Ahmad Moltafet
"""

import unittest
from unittest import TestCase
import logging
from constants import *
from users import *

logging.basicConfig(filename='chat.log', level=logging.INFO)

class UserTest(TestCase):
    """ Docstring
    """
    def setUp(self) -> None:
        logging.info(f'Starting UserTest setUp')
        super().__init__(methodName = 'test_adding')
        self.__cur_users = UserList('test_users')
        self.__cur_users.__init__('test_users')
        logging.info(f'Exiting UserTest setUp')

    @property
    def users(self):
        return self.__cur_users

    # test add user to user list
    def test_adding(self):
        logging.info(f'Starting test_adding')
        self.__cur_users.append(self.__cur_users.register('test_user1'))
        self.__cur_users.append(self.__cur_users.register('test_user2'))
        logging.info(f'Exiting test_adding')

    # test get user from user list
    def test_getting(self):
        logging.info(f'Starting test_getting')
        self.__cur_users.append(self.__cur_users.register('tahmad'))
        self.__cur_users.append(self.__cur_users.register('test_user2'))
        flag = False
        for user in self.__cur_users.get_all_users():
            name = user.to_dict()['alias']
            if name == 'tahmad':
                flag = True
        assert flag == True
        logging.info(f'Exiting test_getting')

    
    # test get all users
    def test_get_all(self):
        logging.info(f'Starting test_get_all')
        self.__cur_users.append(self.__cur_users.register('test_user1'))
        self.__cur_users.append(self.__cur_users.register('test_user2'))
        self.__cur_users.append(self.__cur_users.register('test_user3'))
        self.__cur_users.append(self.__cur_users.register('test_user4'))
        users_list = ['test_user1', 'test_user2', 'test_user3', 'test_user4']
        flag = False
        i = 0
        for user in self.__cur_users.get_all_users():
            name = user.to_dict()['alias']
            if name == users_list[i]:
                flag = True
            i += 1
            if(i == len(users_list)):
                break
        assert flag == True
        logging.info(f'Exiting test_get_all')
    
    # try to get an empty list
    def test_get_all_empty(self):
        logging.info(f'Starting test_get_all_empty')
        self.assertEqual(self.__cur_users.get_all_users(), [])
        logging.info(f'Exiting test_get_all_empty')

        
if __name__ == "__main__":
    unittest.main()