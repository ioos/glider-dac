#!/usr/bin/env python

import os
import redis
from rq import Worker, Queue, Connection
from flask import current_app
from glider_qc import glider_qc
from simplekv.memory.redisstore import RedisStore

listen = ['default']

def main():
    with Connection(glider_qc.get_redis_connection()):
        worker = Worker(list(map(Queue, listen)))
        worker.work(with_scheduler=True)

if __name__ == '__main__':
    main()
