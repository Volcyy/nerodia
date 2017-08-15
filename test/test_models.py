"""
Tests the database models.
This sets a custom environment
variable for the database to
ensure that the actual database
is not changed through the run.
The environment variable is
reset when the tests are done.
"""

import datetime
import unittest

from nerodia import models as db


ONE_MINUTE_AGO = datetime.datetime.now() - datetime.timedelta(minutes=1)


class StreamModelTestCase(unittest.TestCase):
    """
    Contains tests for the Stream table
    which holds information about Twitch
    streams, namely their ID. This is
    cached since the ID is necessary for
    most API calls, despite only checking
    the stream status is necessary.
    """

    def setUp(self):
        """
        Creates a new Stream with the name
        "test-stream" and the id 1337.
        Exposes it via the attribute `test_stream`.
        """

        new_stream = db.Stream(name="test-stream", id=1337)
        db.session.add(new_stream)
        self.query = db.session.query(db.Stream)
        self.test_stream = self.query.first()

    def tearDown(self):
        """"
        Deletes the previously created
        test stream to ensure that the
        database does not grow infinitely.
        """

        self.query.delete()

    def test_columns(self):
        """
        Validates that the rows in the
        Stream table have the
        correct types and values.
        """

        self.assertIsInstance(self.test_stream.name, str)
        self.assertIsInstance(self.test_stream.id, int)
        self.assertIsInstance(self.test_stream.followed_by.all(), list)
        self.assertIsInstance(self.test_stream.added_on, datetime.datetime)

        self.assertEqual(self.test_stream.name, "test-stream")
        self.assertEqual(self.test_stream.id, 1337)
        self.assertListEqual(self.test_stream.followed_by.all(), [])
        self.assertGreater(self.test_stream.added_on, ONE_MINUTE_AGO)
        self.assertLess(self.test_stream.added_on, datetime.datetime.now())


class SubredditModelTestCase(unittest.TestCase):
    """
    Tests the Subreddit database model,
    which contains the name of a Subreddit
    along with a single stream that the
    Subreddit is following, resulting in
    a one-to-many relationship: one sub-
    reddit can follow many streams,
    which typically results in tables like
          name   |   follows
        ---------+-------------
        some-sub | first-stream
        some-sub | second-stream
        some-sub | third-stream
    The ID attribute is ommitted as it is
    generated automatically and not of
    interest in queries run.
    """

    def setUp(self):
        """
        Sets up the SubredditModelTestCase.
        This creates a new subreddit with
        the name "test-sub" following a
        stream "test-stream" and inserts
        it into the database. This is
        cleaned up in the `tearDown` method.
        """

        new_sub = db.Subreddit(name="test-sub", follows="test-stream")
        db.session.add(new_sub)
        self.query = db.session.query(db.Subreddit)
        self.test_sub = self.query.first()

    def tearDown(self):
        """
        Deletes the previously created
        `test-sub` subreddit from the
        table to ensure that it does
        not fill up infinitely over
        various test runs.
        """

        self.query.delete()

    def test_columns(self):
        """
        Validates that the columns of
        the Subreddit table have the
        correct type, and that the
        newly created subreddit from
        within the `setUp` method has
        the correct attributes.
        """

        self.assertIsInstance(self.test_sub.id, int)
        self.assertIsInstance(self.test_sub.name, str)
        self.assertIsInstance(self.test_sub.follows, str)
        self.assertIsInstance(self.test_sub.all_follows.all(), list)

        self.assertEqual(self.test_sub.name, "test-sub")
        self.assertEqual(self.test_sub.follows, "test-stream")
        self.assertListEqual(self.test_sub.all_follows.all(), [])


class DRConnectionModelTestCase(unittest.TestCase):
    """
    The test case for the DRConnection
    (short for DiscordRedditConnection)
    table and its rows.
    """

    def setUp(self):
        """
        Sets up the test case by
        creating a new DRConnection
        and inserting it into the
        database. This is cleaned
        up in the `tearDown` method.
        """

        new_conn = db.DRConnection(discord_id=1337, reddit_name="1337")
        db.session.add(new_conn)
        self.query = db.session.query(db.DRConnection)
        self.test_conn = self.query.first()

    def tearDown(self):
        """
        Removes the previously created
        `DRConnection` row from the
        table to ensure that the database
        does not fill up infinitely.
        """

        self.query.delete()

    def test_columns(self):
        """
        Validates that the columns of the
        `DRConnection` table have the correct
        types, and that the inserted (in `setUp`)
        row has the correct values as passed along.
        """

        self.assertIsInstance(self.test_conn.discord_id, int)
        self.assertIsInstance(self.test_conn.reddit_name, str)

        self.assertEqual(self.test_conn.discord_id, 1337)
        self.assertEqual(self.test_conn.reddit_name, "1337")
