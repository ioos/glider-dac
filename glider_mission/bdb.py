import os.path
from bsddb3 import db
from contextlib import contextmanager

class UserDB(object):
    """
    A helper class representing a user authorization database.

    In the GliderDAC this is used to control access to ftp by vsftpd as well as perform
    user authorization for the website frontend.

    It is a wrapper on top of Berkeley DB which is supported by vsftpd.
    """
    def __init__(self, db_file):
        self._db_file = db_file

    @classmethod
    def init_db(cls, db_file):
        if os.path.exists(db_file):
            raise ValueError("File %s already exists" % db_file)

        bdb = db.DB()
        bdb.open(db_file, None, db.DB_HASH, db.DB_CREATE|db.DB_NOMMAP)
        bdb.close()

    @contextmanager
    def _use_db(self):
        bdb = db.DB()
        try:
            bdb.open(self._db_file, None, db.DB_HASH, db.DB_DIRTY_READ|db.DB_NOMMAP)
            yield bdb
        finally:
            bdb.close()

    def get(self, username):
        with self._use_db() as bdb:
            return bdb.get(username, None, flags=0)

    def set(self, username, password):
        with self._use_db() as bdb:
            bdb.put(username, password)

    def check(self, username, password):
        dbp = self.get(username)
        return dbp == password

    def list_users(self):
        with self._use_db() as bdb:
            c = bdb.cursor()
            r = c.first()

            users = []
            while r:
                users.append(r[0])
                r = c.next()

            return users

