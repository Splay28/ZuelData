HOST = '127.0.0.1'
PORT = '3306'
DATABASE = 'zueldb'
USERNAME = 'root'
PASSWORD = '_'

DB_URL = "mysql://{username}:{password}@{host}:{port}/{db}?charset=utf8".format(username=USERNAME,password=PASSWORD, host=HOST,port=PORT, db=DATABASE)

SQLALCHEMY_DATABASE_URI = DB_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False
