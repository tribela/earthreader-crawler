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
            lastaccess datetime not null
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

    for url in urls:
        try:
            print url
            #TODO: join to one query
            #TODO: add title, linkurl
            conn.execute("insert into feeds(feedurl, lastaccess) values('%s', datetime('now'))" % (url))
        except sqlite3.OperationalError, e:
            print >> stderr, "Failed to insert " + url
            print dir(e)
            pass
    conn.commit()


if __name__ == '__main__':
    conn = open_database()

    line = raw_input("Input command: ")
    while len(line) > 0:
        if line == 'add':
            url = raw_input("Input url: ")
            add_url(conn, url)
        elif line == 'crawl':
            cur = conn.execute("select feedurl, lastaccess from feeds")
            for row in cur.fetchall():
                #TODO: crawl
                print row[0], row[1]

        line = raw_input("Input command: ")

    conn.commit()
    conn.close()
