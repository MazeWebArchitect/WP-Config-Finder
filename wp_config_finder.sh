#!/bin/bash

### Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
ORANGE='\033[0;33m'
SC='\033[0m' # Stop Color

### Files and globals
urllist="urllist.txt"
urlamount=$(grep -c "" $urllist)
testiteration=0
wordlist="wordlist.txt"
findingslist="findings.txt"
timefolder=$(date +"%Y-%m-%d_%H-%M-%S")
filefolder="findings/"$timefolder
if [ ! -d "findings" ]; then
  mkdir "findings"
fi


### FUNCTIONS
# Requesting the page with the desired ending
function check_ending {
  url=$1
  ending=$2
  req=$(curl -L -s -i -o /dev/null -w "%{http_code}\n" $url"/wp-config.php"$ending)
  echo $req
}

# Generating  a 50-character random string and adding it
# to the url parameter and checks if the response is still a 200
# if so it declares the website as "fake", meaning it will always return a 200
# even on 404 pages, for example by using a plugin (404 to frontpage or similar)
function test_response_with_long_random_string {
  url=$1
  randomstring=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c50)
  req=$(curl -L -s -i -o /dev/null -w "%{http_code}\n" $url"/"$randomstring)
  if [[ "$req" = 200 ]] ; then
    fakeresponse="true"
  else
    fakeresponse="false"
  fi 
  echo "$fakeresponse"
}

echo "Starting, there are $urlamount urls to scan"
### MAIN
# As long as their is a url in the url list, run this
while read url
do
  (( testiteration++ ))
  echo
  echo "---------------------"
  echo "Testing $url | $testiteration out of $urlamount"
  echo "---------------------"
  alivecheck=$(curl -L -s -i -o /dev/null -w "%{http_code}\n" --connect-timeout 10 $url)
  fake=""
  if [[ "$alivecheck" = 200 ]] ; then
    echo -e ${BLUE}$alivecheck " | " $url "is alive, let's scan it${SC}"
    
    # Go through the wordlists
    while read ending
    do
      if [ -z "$fake" ] ; then
	check=$(check_ending $url $ending)
	if [[ "$check" = 200 ]] ; then
	  # This is the first test and we already found a 200, checking for fake responses
	  echo -e ${BLUE}$check " | " $url"/wp-config.php"$ending "<<<< | Found something - running fakecheck${SC}"
	  fakecheck=$(test_response_with_long_random_string $url)
	  if [[ $fakecheck = "true" ]] ; then
	    fake="true"
	    echo -e ">>>> \u274c Fakecheck failed"
	    echo -e ${ORANGE}">>>> $url responds to every 404/403 with a 200, maybe because of a plugin: >> ignoring it${SC}"
	  else
	    echo -e ">>>> \u2705 Fakecheck passed"
	    fake="false"
	  fi
	else
	  echo $check " | " $url"/wp-config.php"$ending " | Nothing here"
	  # Because there was now a non 200 response we can assume that the site 
	  # is not redirecting all non 200 responses, so set the fake to false
	  fake="false"
	fi
      fi
      if [[ "$fake" = "false" ]] ; then
        check=$(check_ending $url $ending)
	if [[ "$check" = 200 ]]; then
	  echo -e ${GREEN}$check " | " $url"/wp-config.php"$ending "<<<< | Found something${SC}"
	  if [ ! -d "$filefolder" ]; then
            mkdir $filefolder
	  fi
	  echo $url"/wp-config.php"$ending >> $filefolder/$findingslist
	else
	  echo $check " | " $url"/wp-config.php"$ending " | Nothing here"
	fi
      fi
    done < <(grep . "${wordlist}")
  else 
    echo "No response from remote host, $url seems to be dead, is password protected or might be blocking our IP"
  fi
done <  <(grep . "${urllist}")

echo
echo "----------------------------------------"
if [[ -f "$filefolder/$findingslist" ]]; then
  echo
  echo -e ${ORANGE}">>>> Findings <<<<"
  cat $filefolder/$findingslist
  echo -e ${SC}
else
    echo ${RED}"nothing found ;(${SC}"
fi
echo "----------------------------------------"
