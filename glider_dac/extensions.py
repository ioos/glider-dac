from redis import Redis
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

def get_redis_connection_other(host, port, db):
    return Redis(host, port, db)
