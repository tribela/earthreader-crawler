#!/usr/bin/env python

import urllib2
from xml.etree import ElementTree
from bs4 import BeautifulSoup
import re
import sqlite3
from os import path
import sys
from sys import stderr

DB_FILE_NAME = 'earth.db'

def open_database():
    try:
        conn = sqlite3.connect(DB_FILE_NAME)
    except sqlite3.OperationalError, e:
        print >> stderr, dir(e)
        sys.exit(-1)

    cur = conn.execute("select count(name) from sqlite_master where type='table' and name='feeds'")
    if cur.fetchone()[0] < 1:
        conn.execute(
            """\
            CREATE TABLE feeds(
            feedurl text unique not null primary key,
            title text,
            linkurl text,
            lastaccess timestamp not null
            );"""
        )

    cur = conn.execute("select count(name) from sqlite_master where type='table' and name='items'")
    if cur.fetchone()[0] < 1:
        conn.execute(
            """\
            CREATE TABLE items(
            uid text not null unique primary key,
            feedurl text not null,
            title text,
            linkurl text,
            pubdate datetime not null,
            content text not null
            );"""
        )

    return conn

def add_url(conn, url):
    handle = urllib2.urlopen(url)
    content_type = handle.headers.getheader('Content-Type')

    urls = []
    if content_type in ['application/rss+xml', 'application/atom+xml']:
        urls.append(url)
    elif content_type.startswith('text/html'):
        soup = BeautifulSoup(handle.read())
        link_tags = soup('link', {'type': re.compile(r'application/(rss|atom)\+xml')})
        urls += map(lambda x: x['href'], link_tags)

    #TODO: insert into DB here
