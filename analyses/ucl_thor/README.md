# UCL Thor

## Description

> Password-protected note storage service for the web.

This services is provided by the team *THOR - Talented Hacking Oblivious
Robots* and is a website which provide a secure secret storage.

The website is actually composed of 4 main pages.
- `index.php` which provides forms to store a new secret or to retrieve an old
one.
- `read.php` which checks the note password and redirects to `read2.php` with a 
token, if the password matches.
- `read2.php` which checks the token and displays the note if the token is
valid.
- `write.php` which generates a secret token and an note id and saves the note.

Each note is stored in the `rw` directory in a file named after the note id. It
contains 4 fields formatted as a csv file:
```
note,hashed_password,date,token
```

### Flag

Flag Description:

> Flags are identified by the note name.

The *flag_id* corresponds to the *note_id* which is the filename of the note.


## Vulnerabilities

In `write.php`:
```php
# In this example, we create a new (randomly-named) file for each flag.
$somerand = openssl_random_pseudo_bytes(8) or die("random");
$note_id = bin2hex($somerand);

$date = date("m/d/Y H:i:s");
$noteid_dateseconds = $note_id . strtotime($date);

$f = fopen($mydir.$note_id, 'x') or die("fopen");
fputcsv($f, array($content, password_hash($password, PASSWORD_DEFAULT), $date, bin2hex($noteid_dateseconds))) or die("fputcsv");
```

We can see that the *note_id* is generated using a 8-bytes pseudo-random
generator. The *note_id* is then used to generate `$noteid_dateseconds`.
Finally, `$noteid_dateseconds` is encoded in hexadecimal to be stored as token.

However, as the *note_id* corresponds to the *flag_id* which is known, the
entropy of the token only relies on the date which has a very low entropy.

## Proof of Concept

Because the flag is resetted every few minutes (lets say 5 minutes even if it
was less than that), the bruteforce of the date can be limited to this time
range. This means only `5 * 60 = 300` different dates may be tested what is
few.

With [poc.py][poc], it's also possible to try to bruteforce every possible
timestamp from the start of the iCTF to its end. However, its a bit more
time-consuming.

```bash
$ ./poc.py 192.168.56.101 20071 01cad01b53faa6d9 12/04/15 20:20:00
Tested: 295 / 300 
found for 2015-12-04 20:15:05
FLGC1xmozH8WHuEq
```

```bash
$ ./poc.py 192.168.56.101 20071 01cad01b53faa6d9
Tested: 20695 / 28800 
found for 2015-12-04 20:15:05
FLGC1xmozH8WHuEq
```

During the iCTF, the date obviously would have been generated from the current
date.


[poc]: poc.py
