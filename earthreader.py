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
            lastmodified datetime not null
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

def query_feed_info(conn, url):
    handle = urllib2.urlopen(url)
    last_modified = handle.headers.getheader('Last-Modified')

    tree = ElementTree.parse(handle)
    root = tree.getroot()

    parse_feed_tree(conn, url, tree)

    if root.tag == 'rss':
        title = tree.find('./channel/title').text
        link = tree.find('./channel/link').text
    elif root.tag == 'feed': #atom
        #FIXME: read ATOM spec document
        title = 'title'
        link = url

    return (title, link, last_modified)

def add_url(conn, url):
    try:
        handle = urllib2.urlopen(url)
        content_type = handle.headers.getheader('Content-Type')
    except urllib2.URLError, e:
        print >> stderr, "Failed to add feed"
        return

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
            #FIXME: join to one query
            (title, link, last_modified) = query_feed_info(conn, url)
            #escape
            title = title.replace("'", "''")
            link = link.replace("'", "''")
            last_modified = last_modified.replace('"', '""')
            conn.execute(
                "insert into feeds(feedurl, title, linkurl, lastmodified) values('%s', '%s', '%s', '%s')" %
                (url, title, link, last_modified)
            )
        except sqlite3.OperationalError, e:
            print >> stderr, "Failed to insert " + url
            print >> stderr, e.args
    conn.commit()

def parse_feed_tree(conn, feedurl, tree):
    root = tree.getroot()

    if root.tag == 'rss':
        for item in tree.findall('./channel/item'):
            title = item.find('title').text
            uid = item.find('guid').text
            link = item.find('link').text
            pubdate = item.find('pubDate').text
            content = item.find('description').text

            print "%s at (%s)" % (title, pubdate)
            add_item(conn, feedurl, uid, title, link, pubdate, content)
    elif root.tag == 'feed': #ATOM
        #TODO: parse atom feeds
        pass


def add_item(conn, feedurl, uid, title, link, pubdate, content):
    #escape doublequote in sqlite " -> ""
    feedurl = feedurl.replace("'", "''")
    uid = uid.replace("'", "''")
    title = title.replace("'", "''")
    link = link.replace("'", "''")
    pubdate = pubdate.replace("'", "''")
    content = content.replace("'", "''")

    try:
        conn.execute(
            "insert into items(feedurl, uid, title, linkurl, pubdate, content) values('%s', '%s', '%s', '%s', '%s', '%s')" %
            (feedurl, uid, title, link, pubdate, content)
        )
    except sqlite3.IntegrityError, e:
        #not unique, already exist
        pass
    except sqlite3.OperationalError, e:
        print >> stderr, "Cannot add item"
        print >> stderr, e.args

def crawl_feed(conn, url):
    cur = conn.execute("select lastmodified from feeds where feedurl='%s'" % (url))
    last_modified = cur.fetchone()[0]
    req = urllib2.Request(url)
    req.add_header('If-Modified-Since', last_modified)

    try:
        content = urllib2.urlopen(req).read()
        #TODO: add items to DB
    except urllib2.URLError, e:
        if e.getcode() == 304: #Not modified
            print "%s is not modifed since last crawling" % (url)
        else:
            print >> stderr, "Failed to get items"

if __name__ == '__main__':
    conn = open_database()

    line = raw_input("Input command: ")
    while len(line) > 0:
        if line == 'add':
            url = raw_input("Input url: ")
            add_url(conn, url)
        elif line == 'crawl':
            cur = conn.execute("select feedurl from feeds")
            for row in cur.fetchall():
                crawl_feed(conn, row[0])
        elif line == 'show':
            cur = conn.execute("select feedurl, title, linkurl, pubdate from items order by feedurl asc, pubdate asc")
            for row in cur.fetchall():
                feedurl = row[0]
                title = row[1]
                linkurl = row[2]
                pubdate = row[3]

                print "%s - %s (at %s): %s" % (feedurl, title, pubdate, linkurl)

        line = raw_input("Input command: ")

    conn.commit()
    conn.close()
