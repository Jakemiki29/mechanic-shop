import os


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 120


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///users.db"
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    DEBUG = True


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URI")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DEBUG = False
