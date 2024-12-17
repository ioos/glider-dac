#!/usr/bin/env python

import os
import redis
from rq import Worker, Queue
from flask import current_app
from glider_qc import glider_qc
from simplekv.memory.redisstore import RedisStore


def main():
    worker = Worker("default", connection=glider_qc.get_redis_connection())
    worker.work(with_scheduler=True)

if __name__ == '__main__':
    main()
