# -*- coding: utf-8 -*-

import contextlib

import os

import sqlite3

from .core import fail_with_error
from .conf import config


__all__ = ['db']


class DB(object):
    """Simple database wrapper class.
    """

    connection = None
    cursor = None

    def connect(self):
        """Opens a database connection and loads default SQL schema
        into the DB.
        """

        try:
            self.connection = sqlite3.connect(config['db'])
        except sqlite3.Error as e:
            fail_with_error("Unable to connect to DB, the message was: `{0}`"
                            .format(e.message))

        # Loading SQL schema

        schema_path = os.path.join(os.path.dirname(__file__), 'misc/vlcc.sql')

        with contextlib.nested(open(schema_path, 'r'),
                               self.connection) as (schema_file, connection):
            try:
                connection.executescript(schema_file.read())
            except sqlite3.Error as e:
                fail_with_error("Unable to load the SQL schema, "
                                "the message was: `{0}`".format(e.message))
        self.cursor = self.connection.cursor()

    def execute(self, query, params=None, use_cursor=False):
        """Executes a query.

        @param query: query string
        @param params: params dict
        @param use_cursor: if True, call `execute()` on cursor
            instead of connection
        """

        if use_cursor:
            processor = self.cursor
        else:
            processor = self.connection

        try:
            processor.execute(query, params)
        except sqlite3.Error as e:
            fail_with_error("Unable to execute the query {0} with {1}, "
                            "the message was: `{2}`"
                            .format(query, params or "no params", e.message))

    def query(self, query, params=None):
        """Queries the database.

        @param query: query string
        @param params: params dict

        @return: sqlite3.Cursor object
        """

        self.execute(query, params, use_cursor=True)
        return self.cursor

    def commit(self):
        """Commits current DB transaction.
        """

        try:
            with self.connection as connection:
                connection.commit()
        except sqlite3.Error as e:
            fail_with_error("Unable to perform DB commit, "
                            "the message was: `{0}`".format(e.message))

    def __del__(self):
        self.connection.close()


db = DB()
