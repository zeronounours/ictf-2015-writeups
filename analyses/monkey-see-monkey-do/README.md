# Monkey See Monkey Do

## Description

> A little-known fact about the golden snub-nosed monkeys is that they are secretly rising out of their original habitat, deep in the jungle, into more populated areas. By exploiting their cuteness, the monkeys are slowly enslaving humans, and mainly target weaker-minded PhD students, as they are more susceptible to the monkey mind tricks. Under the reign of terror from the monkeys, some of the members of the HacknamStyle CTF team were forced to create a dating application for their monkey masters. The dating application will be used as a ploy to make monkeys find their soulmates more quickly and thus significantly increase the monkey population, a first step towards world domination!

This service was created by the team *HacknamStyle*. It's a PHP website with the flags stored as users' secret.

It's a website where you can register, login, browse other monkeys' profiles, message them and change your own settings.

The different pages are accessible from `index.php` using the request parameter
`page`. It can be among these 5 values: `list`, `viewprofile`, `inbox`,
`editprofile`, `logout`.

It uses a sqlite database to store the list of users, and their associated
secrets. The first thing we notice is that all data stored in the database is 
encrypted using a custom encryption function.

### Flag

Flag Description:

> Out of fear for a dictatorship of an evil monkey, for instance one of the bald uakaris, we require the monkeys that use our dating application to tell us their guilty pleasures. While we told our monkey masters that we keep this information secret and secure (they forced us to use encryption), we secretly inserted a backdoor. So in case of emergency, we will be able to retrieve the darkest secrets of all monkeys, who we identify by their username. Since street credibility and reputation is of great importance to monkeys, we will be able to strike down a dictatorship by simply leaking secrets of the evil monkey.


When you register, you must provide a username, a password, a name, a secret, and of course a gender and a photo to 
power the dating application. The username is the *flag_id* and the secret is the flag.


## Vulnerabilities



### Bad crypto

All values stored in the database are encrypted with these functions :

```php
public static function encrypt($value) {
	$td = mcrypt_module_open('rijndael-128', '', 'ecb', '');
	$blocksize = mcrypt_enc_get_iv_size($td);
	$padded = self::pad($value, $blocksize);
	$iv = self::getIV($blocksize); // IV is ignored in ECB mode, but PHP needs one
	mcrypt_generic_init($td, self::$key, $iv);
	$encrypted = mcrypt_generic($td, $padded);
	mcrypt_generic_deinit($td);
	mcrypt_module_close($td);
	return base64_encode($encrypted);
}

public static function decrypt($encrypted) {
	$td = mcrypt_module_open('rijndael-128', '', 'ecb', '');
	$blocksize = mcrypt_enc_get_iv_size($td);
	$iv = self::getIV($blocksize); // IV is ignored in ECB mode, but PHP needs one
	mcrypt_generic_init($td, self::$key, $iv);
	if (strlen(base64_decode($encrypted)) > 0) {
		$padded = mdecrypt_generic($td, base64_decode($encrypted));
	}
	else {
		$padded = '';
	}
	$value = self::unpad($padded);
	mcrypt_generic_deinit($td);
	mcrypt_module_close($td);
	return $value;
}
```

We notice that there is something fishy with the way values are padded and unpadded :

```php
private static function pad($value, $blocksize) {
	$padded = '';
	for ($i = 0; $i < strlen($value); $i+=$blocksize) {
		$padded .= str_pad(substr($value, $i, $blocksize), $blocksize, '%');
	}
	if (strlen($padded) < $blocksize) {
		$padded = str_repeat('%', $blocksize);
	}
	return $padded;
}

private static function unpad($value) {
	return rtrim($value, '%');
}
```

So, if we encrypt `aa` and `aa%`, we will have the same encrypted result and `decrypt(encrypt('aa')) == decrypt(encrypt('aa%'))`.

But, if we add more `%` characters to enter a new block, we won't have `encrypt('aa') == encrypt('aa%%%%%%%%%%%%%%%%')`. In our 
case, the blocksize is 16 bytes so we can add 16 characters to overflow the current block.

Let's see how we can exploit this.

### Edit profile

When a monkey is connected, a `$current_monkey` object is created and this object contains all the unencrypted information of the monkey.
When a monkey edits his profile, all the attributes of the `$current_monkey` object are updated in the database :

```php
function handle_edit() {
	$required_fields = array('password', 'gender', 'secret');
	foreach ($required_fields as $field) {
		if (!isset($_POST[$field]) || strlen($_POST[$field]) === 0) {
			throw new Exception("Missing field: $field");
		}
	}

	$curMonkey = Monkey::getFromDb($_SESSION['id']);

	$password = getPOSTValue('password');
	$gender = getPOSTValue('gender', 'M');
	$secret = getPOSTValue('secret');
	$bio = getPOSTValue('bio');
	$dob = getPOSTValue('dob', NULL);
	$interests = array_filter(getPOSTValue('interests', array()), function($interest) {
		return strlen($interest) > 0;
	});
	$curMonkey->password = $password;
	$curMonkey->gender = $gender;
	$curMonkey->interests = $interests;
	$curMonkey->secret = $secret;
	$curMonkey->bio = $bio;
	$curMonkey->dob = $dob;

	...
	
	$curMonkey->save();
}
```

The `save()` method calls this `update()` function in DB.class.php

```php
private function update($table, $object) {
	$properties = array_map("trim_special", array_keys(get_object_vars($object)));
	$setClause = '';
	foreach ($properties as $property) {
		$setClause .= "$property = :$property ,";
	}
	$setClause = preg_replace('/,$/', '', $setClause);
	$className = get_class($object);
	$uniqueColumnName = $className::$uniqueColumnName; // requires PHP > 5.3.0
	$stmt = $this->db->prepare("UPDATE $table SET $setClause WHERE $uniqueColumnName = :uniqueValue");
	foreach ($properties as $property) {
		if ($property === $uniqueColumnName) {
			$stmt->bindValue(':' . $property, $object->$property);
		}
		else {
			$stmt->bindValue(':' . $property, encrypt($object->$property));
		}
	}
	$stmt->bindValue(':uniqueValue', $object->$uniqueColumnName);
	$stmt->execute();
}
```

So we see that we loop on all the object's attributes and we update them in the database.
The problem is that if a monkey's name on registration is `a%%`, his name in the `$current_monkey` object will be `a` and this value will be updated in the database.

### Login

The login function is coded in a way which supposes that each username is unique.

```php
function handle_login() {
	$username = $_POST['username'];
	$password = $_POST['password'];
	$db = DB::getInstance();
	if (isset($username) && isset($password)) {
		$loggedIn = $db->checkLogin($username, $password);
		if ($loggedIn) {
			$id = $db->getIdFromUsername($username);
			$_SESSION['id'] = $id;
			return TRUE;
		}
		else {
			// hacking attempt!
			throw new IllegalMonkeyBusiness();
			
		}
	}
	else {
		throw new Exception("Credentials are not given");
	}
}
```

If we have 2 monkeys, `monkey1;id=1` and `monkey2;id=2` with the same username and with different passwords, `monkey2` can connect to `monkey1`'s account by using 
his own password :
`checkLogin()` checks that there is at least one good (username, password) pair
`getIdFromUsername` will get the most recently registered monkey

## Proof of Concept

### Manual PoC

1. Create an account with the username `flag_id + %%%%%%%%%%%%%%%%` (16 '%' characters) to make sure that the encryted value of our monkey's username will be different 
from the flad id.
2. Once connected, edit this monkey's password with a custom password.
3. Logout, then login using the username `flag_id` and the password that we set in step 2.
4. ???
5. Profit

### Automated PoC

The script poc.py uses the same principle as previously to get
the flag, so it won't be explained once again.

>./poc.py host port flag_id path_to_image