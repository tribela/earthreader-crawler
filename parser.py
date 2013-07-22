#!/usr/bin/env python

from bs4 import BeautifulSoup
import urllib2

def parse_rss(content):
    soup = BeautifulSoup(content, 'xml')

    title = soup.channel.title.text
    link = soup.channel('link', {'type': ''})[0].text

    print "%s(%s)" % (title, link)

    items = soup('item')
    for item in items:
        title = item.title.text
        link = item.link.text
        uid = item.guid.text

        print " %s(%s) - (%s)" % (title, link, uid)

def parse_atom(content):
    pass

def parse_feed(feed_type, url):
    try:
        content = urllib2.urlopen(url).read()
        if feed_type in ['rss', 'rss+xml']:
            parse_rss(content)
        elif feed_type in ['atom', 'atom+xml']:
            parse_atom(content)
    except urllib2.URLError, e:
        return None

if __name__ == '__main__':
    feed_type = raw_input('Input type: ')
    url = raw_input('Input url: ')

    parse_feed(feed_type, url)
