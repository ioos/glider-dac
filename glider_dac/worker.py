#!/usr/bin/env python

import os
import redis
from rq import Worker, Queue, Connection
from glider_dac import redis_connection

listen = ['default']

def main():
    with Connection(redis_connection):
        worker = Worker(list(map(Queue, listen)))
        worker.work(with_scheduler=True)

if __name__ == '__main__':
    main()
