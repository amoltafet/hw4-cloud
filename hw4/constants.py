"""Group Members: Matt Moore, Adrian Abeyta, Ahmad Moltafet
"""


ROOM_TYPE_PRIVATE = 0
MONGO_DB = 'detest'
GET_ALL_MESSAGES = -1

MONGODB_HOST = '34.94.157.136'
MONGODB_PORT = 27017
MONGODB_USER = 'class'
MONGODB_PASS = 'CPSC313'
MONGODB_AUTH_SOURCE = 'cpsc313'
MONGODB_CLASS_DB = 'cpsc313'
MONGODB_CLASS_ROOM_LIST = 'rooms'
MONGODB_CLASS_USERS = 'users'
DEFAULT_PUBLIC_ROOM = 'general'
DEFAULT_ROOM_LIST_NAME = 'main'
DEFAULT_USER_LIST_NAME = 'global'

MONGODB_AUTH_SOURCE_CLASS = 'cpsc313'
GET_ALL_MESSAGES = -1
MESSAGE_TYPE_SENT = 1
MESSAGE_TYPE_RECEIVED = 0
DEFAULT_QUEUE_NAME = 'general'
MONGODB_AUTH_MECH = 'SCRAM-SHA-1'
RMQ_DEFAULT_PUBLIC_EXCHANGE = 'general'
RMQ_DEFAULT_PRIVATE_QUEUE = 'private'
ROOM_TYPE_PUBLIC = 100
ROOM_TYPE_PRIVATE = 200
MONGODB_URL = "mongodb://" + MONGODB_HOST + ":" + str(MONGODB_PORT) + "/"
PRIVATE_ROOM_NAME = 'eshner'
PUBLIC_ROOM_NAME = 'general'
SENDER_NAME = 'testing'
DEFAULT_PRIVATE_TEST_MESS = 'DE: Test Private Queue at '
DEFAULT_PUBLIC_TEST_MESS = 'DE: Test Public Queue at '
USER_ALIAS = 'testing'


