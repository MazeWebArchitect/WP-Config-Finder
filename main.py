import os
import random
import string
import subprocess
import argparse
import requests
import concurrent.futures

# Color codes for console output
ORANGE = "\033[93m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RED = "\033[91m"
SC = "\033[0m"

# Default names for files and folders
filefolder = "findings"
findingslist = "findings.txt"
wordlist = "wordlist.txt"


def execute_curl_command(*args):
    """
    Execute a curl command with the provided arguments.

    Args:
        *args: Arguments to be passed to the curl command.

    Returns:
        str: The output of the curl command.

    Raises:
        subprocess.CalledProcessError: If the curl command fails.

    """
    try:
        command = ["curl"] + list(args)
        output = subprocess.check_output(command, stderr=subprocess.STDOUT).decode("utf-8")
        return output.strip()

    except subprocess.CalledProcessError as e:
        # Handle the error gracefully
        print(f"An error occurred while executing the curl command: {e}")
        raise e


def generate_random_string(length):
    """
    Generate a random string of the specified length.

    Args:
        length (int): The length of the random string to generate.

    Returns:
        str: The randomly generated string.

    Raises:
        Exception: If an error occurs while generating the random string.

    """
    try:
        return ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=length))

    except Exception as e:
        # Handle the error gracefully
        print(f"An error occurred while generating a random string: {e}")
        raise e


def test_response_with_long_random_string(url):
    """
    Test the response of a URL by appending a long random string.
    If the response is 200, we can assume that this website always returns a 200 and therefore our tool is not feasible here.

    Args:
        url (str): The URL to test.

    Returns:
        str: "true" if the response code is 200, else "false".

    Raises:
        subprocess.CalledProcessError: If the curl command fails.

    """
    try:
        random_string = generate_random_string(50)
        response_code = execute_curl_command("-L", "-s", "-i", "-o", "/dev/null", "-w", "%{http_code}\\n",
                                             f"{url}/{random_string}")
        return "true" if response_code == "200" else "false"

    except subprocess.CalledProcessError as e:
        # Handle the error gracefully
        print(f"An error occurred while testing the response with a long random string: {e}")
        raise e
    except Exception as e:
        # Handle other exceptions
        print(f"An unexpected error occurred while testing the response with a long random string: {e}")
        raise e


def parse_arguments():
    """
    Parse command line arguments for the script.

    Returns:
        Namespace: The parsed command line arguments.

    Raises:
        argparse.ArgumentError: If the required arguments are not provided.

    """
    try:
        parser = argparse.ArgumentParser(description="URL Check Script")
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("-u", "--url", help="Single URL to check")
        group.add_argument("-l", "--list", help="File containing URLs to check")
        return parser.parse_args()

    except argparse.ArgumentError as e:
        # Handle the argument error gracefully
        print(f"An argument error occurred while parsing the command line arguments: {e}")
        raise e

    except Exception as e:
        # Handle other exceptions
        print(f"An unexpected error occurred while parsing the command line arguments: {e}")
        raise e


def request_page(full_url):
    """
    Make an HTTP GET request to a specific URL with an ending from our wordlist.

    Args:
        full_url: The full URL with the path and ending.

    Returns:
        str: The status code of the HTTP response.

    Raises:
        requests.RequestException: If an error occurs during the HTTP request.

    """
    try:
        response = requests.get(full_url)
        return str(response.status_code)

    except requests.RequestException as e:
        # Handle the request exception gracefully
        print(f"An error occurred while making the HTTP request: {e}")
        raise e

    except Exception as e:
        # Handle other exceptions
        print(f"An unexpected error occurred while making the HTTP request: {e}")
        raise e


def process_website(url):
    """
    Process a website for finding specific URLs.
    There is also a path list that will check the same endings from the wordlist.txt for all paths in there.

    Args:
        url (str): The URL to process.

    Raises:
        FileNotFoundError: If the wordlist file is not found.
        Exception: If an unexpected error occurs.

    """
    try:
        alive_check = execute_curl_command("-L", "-s", "-i", "-o", "/dev/null", "-w", "%{http_code}\\n", f"{url}")
        if alive_check == "200":
            print(BLUE + alive_check + f" | {url} is alive, let's scan it" + SC)

            path_list = ['',
                         'backup/',
                         'bu/',
                         'wp-content/',
                         'wp-content/backup/']

            found_fake_response = False
            with open(wordlist, "r") as wordfile:
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    for ending in wordfile:
                        ending = ending.strip()  # Remove leading/trailing whitespace
                        for path in path_list:
                            full_url = f"{url}/{path}wp-config.php{ending}"
                            future = executor.submit(request_page, full_url.strip())
                            check = future.result()

                            if not found_fake_response:
                                if check == "200":
                                    print(
                                        BLUE + check + f" | {full_url} <<<< | Found something - running fakecheck" + SC)
                                    future_fake = executor.submit(test_response_with_long_random_string, url.strip())
                                    fakecheck = future_fake.result()
                                    if fakecheck == "true":
                                        found_fake_response = True
                                        print(ORANGE + f">>>> ❌ Fakecheck failed")
                                        print(
                                        RED + f">>>> {url} responds to every request with a 200, maybe because of a plugin: >> ignoring it" + SC)
                                    else:
                                        print(ORANGE + f">>>> ✅ Fakecheck passed")
                            if not found_fake_response and check == "200":
                                print(GREEN + check + f" | {full_url} <<<< | Found something" + SC)
                                if not os.path.exists(filefolder):
                                    os.mkdir(filefolder)
                                with open(filefolder + "/" + findingslist, 'a') as findings:
                                    findings.write(f"{full_url}\n")
                            elif check != "":
                                print(check + f" | {full_url} | Nothing here")
        else:
            print(RED + alive_check + f" | {url} is not reachable or blocking our IP" + SC)

    except FileNotFoundError as e:
        # Handle the file not found error gracefully
        print(f"Wordlist file not found: {e}")
        raise e

    except Exception as e:
        # Handle other exceptions
        print(f"An unexpected error occurred while processing the website: {e}")
        raise e


def process_urls(urls):
    """
    Process a list of URLs or a single URL.

    Args:
        urls (list): List of URLs to process (can also be 1).

    Raises:
        Exception: If an unexpected error occurs.

    """
    try:
        url_amount = len(urls)
        print(f"Starting, there are {url_amount} URLs to scan")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for url in urls:
                executor.submit(process_website, url)

        print("\n----------------------------------------")
        if os.path.exists(filefolder + "/" + findingslist):
            print(">>>> Findings <<<<")
            with open(filefolder + "/" + findingslist, 'r') as findings:
                print(findings.read(), end="")
        else:
            print(RED + "nothing found ;(" + SC)
        print("----------------------------------------")

    except Exception as e:
        # Handle other exceptions
        print(f"An unexpected error occurred while processing the URLs: {e}")
        raise e


def main():
    """
    Main function to run the WP Config Finder.

    Raises:
        FileNotFoundError: If the list file is not found.
        Exception: If an unexpected error occurs.

    """
    try:
        args = parse_arguments()
        if args.url:
            urls = [args.url]
        elif args.list:
            with open(args.list, "r") as file:
                urls = [line.strip() for line in file]

        process_urls(urls)

    except FileNotFoundError as e:
        # Handle the file not found error gracefully
        print(f"List file not found: {e}")
        raise e

    except Exception as e:
        # Handle other exceptions
        print(f"An unexpected error occurred: {e}")
        raise e


if __name__ == "__main__":
    main()
