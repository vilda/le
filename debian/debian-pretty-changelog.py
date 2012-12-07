#!/usr/bin/env python

import string
import re
import os


def load_tags():
    def xxx(file):
        h = dict()
        tag, commit = None, None
        for line in file:
            m = re.search('^tag\s+(.+)$', line)
            if m:
                tag = m.group(1)
                continue
            m = re.search('^commit\s+(.+)$', line)
            if m:
                commit = m.group(1)
                h[commit] = tag
                tag, commit = None, None
                continue
        return h
    fin = os.popen('git show --tags')
    h = xxx(fin)
    fin.close()
    return h


def load_log():
    def xxx(file):
        l = list()
        h = None
        for line in file:
            m = re.search('^commit\s+(.+)$', line)
            if m:
                if h:
                    l.append(h)
                h = dict()
                h['commit'] = m.group(1)
                continue
            m = re.search('^Author:\s+([^<]+\S+)\s+<([^>]+)>', line)
            if m:
                h['author'] = m.group(1)
                h['email'] = m.group(2)
                continue
            m = re.search('^Date:\s+(.+)\s*$', line)
            if m:
                h['date'] = m.group(1)
                continue
            m = re.search('^\s{4,}(\S.+\S)\s*$', line)
            if m:
                h['msg'] = m.group(1)
                continue
        if h:
            l.append(h)
        return l
    fin = os.popen('git log --summary --no-merges --date=rfc')
    l = xxx(fin)
    fin.close()
    return l


def tag_to_version(tag):
    m = re.search('(\d+(:?[.]\d+)+)', tag)
    if m:
        return m.group(1)
    return tag


def main():
    h = load_tags()
    l = load_log()
    h_msgs = dict()
    tag = None
    for x in l:
        h_msgs.setdefault(x['author'], list()).append(x['msg'])
        if x['commit'] in h:
            tag = h[ x['commit'] ]
            print 'logentries (%s) xxx; urgency=low' % tag_to_version(tag)
            print
            for (k, v) in h_msgs.iteritems():
                print '    [%s]' % k
                for m in v:
                    print '    * %s' % m
            print '\n -- %s <%s>  %s\n\n' % (x['author'], x['email'], x['date'])
            h_msgs = dict()


if __name__ == '__main__':
    main()
