import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'footbot_secret_2026_xK9p')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///stade.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False
