# -*- coding: utf-8 -*-

import contextlib

import os

import sqlite3

from .core import logger, fail_with_error
from .conf import config


__all__ = ['db', 'dict_factory']


def dict_factory(cursor, row):
    """Dictionary row factory function.
    """

    ret = {}
    for index, column in enumerate(cursor.description):
        ret[column[0]] = row[index]
    return ret


class DB(object):
    """Simple database wrapper class.
    """

    connection = None

    def connect(self):
        """Opens a database connection and loads default SQL schema
        into the DB.
        """

        try:
            self.connection = sqlite3.connect(config['db'])
        except sqlite3.Error as e:
            fail_with_error("Unable to connect to DB, the message was: `{0}`"
                            .format(e.message))

        # Loading the SQL schema

        schema_path = os.path.join(os.path.dirname(__file__), 'misc/vlcc.sql')

        with contextlib.nested(open(schema_path, 'r'),
                               self.connection) as (schema_file, connection):
            try:
                connection.executescript(schema_file.read())
            except sqlite3.Error as e:
                fail_with_error("Unable to load the SQL schema, "
                                "the message was: `{0}`".format(e.message))
        self.commit()

    def row_factory(self, factory=None):
        """Sets row factory, i. e., vlcc.db.dict_factory

        @param factory: factory function
        """
        self.connection.row_factory = factory

    def execute(self, query, params=None, use_cursor=False, commit=True):
        """Executes an SQL statement.

        @param query: query string
        @param params: params dict
        @param use_cursor: if True, call `execute()` on cursor
            instead of connection
        """

        if use_cursor:
            processor = self.connection.cursor()
        else:
            processor = self.connection

        params_str = unicode(params or "no params")

        logger.debug("Executing an SQL statement `{0}` with {1}"
                     .format(query, params_str))

        try:
            cursor = processor.execute(query, params)
        except sqlite3.Error as e:
            fail_with_error("Unable to execute the query {0} with {1}, "
                            "the message was: `{2}`"
                            .format(query, params_str, e.message))
        if commit:
            self.commit()
        return cursor

    def query(self, query, params=None):
        """Queries the database.

        @param query: query string
        @param params: params object

        @return: sqlite3.Cursor object
        """

        return self.execute(query, params, use_cursor=True, commit=False)

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
        if self.connection is not None:
            self.connection.commit()
            self.connection.close()


db = DB()
