#!/usr/bin/env python

import os
import redis
from rq import Worker, Queue, Connection
from flask import current_app
#from glider_dac import redis_connection
from flask_kvsession import KVSessionExtension
from simplekv.memory.redisstore import RedisStore

listen = ['default']

#global queue

#def main():
#    redis_pool = redis.ConnectionPool(host=current_app.config.get('REDIS_HOST'),
#                                      port=current_app.config.get('REDIS_PORT'),
#                                      db=current_app.config.get('REDIS_DB'))
#    redis_connection = redis.Redis(connection_pool=redis_pool)
#    strict_redis = redis.StrictRedis(connection_pool=redis_pool)
#
#    store = RedisStore(strict_redis)
#
#    KVSessionExtension(store, current_app)
#
#    queue = Queue('default', connection=redis_connection)
#    with Connection(redis_connection):
#        worker = Worker(list(map(Queue, listen)))
#        worker.work()
#
#if __name__ == '__main__':
#    main()

