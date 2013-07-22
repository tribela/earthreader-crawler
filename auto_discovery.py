#!/usr/bin/env python

from bs4 import BeautifulSoup
import urllib2
import re

def auto_discovery(url):
    try:
        html_source = urllib2.urlopen(url).read()
        soup = BeautifulSoup(html_source)

        link_tag = soup('link', {'type': re.compile(r'application/(rss|atom)\+xml')})
        rss_urls = map(lambda x: (x['type'], x['href']), link_tag)

        return rss_urls
    except urllib2.URLError, e:
        print >> stderr, dir(e)
        return None

if __name__ == '__main__':
    url = raw_input('Input url: ')
    for obj in auto_discovery(url):
        print "type: %s, href: %s" % (obj[0], obj[1])
