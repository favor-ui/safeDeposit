import os

basedir = os.path.abspath(os.path.dirname(__file__))


# creating a configuration class
class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-dont-guess'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb+srv://favor:ddFuQ4UY0mrkmWKe@cluster0-aet1e.mongodb.net/safeDepo?retryWrites=true&w=majority'
