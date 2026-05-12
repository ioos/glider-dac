#!/usr/bin/env python

from rq import Worker
from glider_qc import glider_qc


def main():
    worker = Worker("default", connection=glider_qc.get_redis_connection())
    worker.work(with_scheduler=True)

if __name__ == '__main__':
    main()
