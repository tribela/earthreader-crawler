#!/usr/bin/env python

from xml.etree import ElementTree
import urllib2
from dateutil import parser as DateTimeParser

def parse_rss(tree):
    title = tree.find('./channel/title').text
    link = tree.find('./channel/link').text
    lastmodified = DateTimeParser.parse(tree.find('./channel/lastBuildDate').text)

    print "%s(%s) at %s" % (title, link, str(lastmodified))

    for item in tree.findall('./channel/item'):
        title = item.find('title').text
        link = item.find('link').text
        uid = item.find('guid').text
        pubdate = DateTimeParser.parse(item.find('pubDate').text)
        #content = item.find('encoded').text

        print " %s(%s) at %s" % (title, link, str(pubdate))

def parse_atom(tree):
    pass

def parse_feed(url):
    try:
        handle = urllib2.urlopen(url)
        tree = ElementTree.parse(handle)

        root = tree.getroot()

        if root.tag == 'rss':
            parse_rss(tree)
        elif root.tag == 'feed':
            parse_atom(tree)
    except urllib2.URLError, e:
        return None

if __name__ == '__main__':
    url = raw_input('Input url: ')

    parse_feed(url)
