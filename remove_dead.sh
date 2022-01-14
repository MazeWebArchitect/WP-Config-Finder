#!/bin/bash

urllist="url.txt"

while IFS= read -r url
do
  res=$(curl -L -s -i -o /dev/null -w "%{http_code}\n" --connect-timeout 10 "http://"$url".myraidbox.de")
  if [[ "$res" = 200 ]] ; then
      echo "Works" $url
      echo $url >> url_working.txt
  fi
done < "$urllist"