#!/bin/bash

urllist="url_working.txt"
wordlist="wordlist.txt"

while IFS= read -r url
do
  echo "---------------------"
  echo "Testing $url"
  echo "---------------------"
  
  while IFS= read -r ending
  do
    req=$(curl -L -s -i -o /dev/null -w "%{http_code}\n" "https://"$url".myraidbox.de/wp-config.php"$ending)
    if [[ "$req" = 200 ]] ; then
      echo $req " | " "https://"$url".myraidbox.de/wp-config.php"$ending "<<<< | WORKS"
      echo "https://"$url"/wp-config.php"$ending >> wp_found.txt
    else
      echo $req " | " "https://"$url".myraidbox.de/wp-config.php"$ending " | Dead"
    fi
  done < "$wordlist"
done < "$urllist"