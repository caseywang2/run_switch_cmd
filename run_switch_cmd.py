
import requests
# import paramiko
# from paramiko import SSHClient
# from scp import SCPClient
# import os
# import sys
# import tarfile
# import argparse
import re
import argparse
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


DEBUG = False
rate = 5

def authenticate(session, ip, user, password, http):

    # data = json.dumps({'username':user, 'password':password})
    data = {'username':user, 'password':password}
    url = http + '://' + ip + '/admin/launch?script=rh&template=json-request&action=json-login'
    if DEBUG:
        print("function: authenticate - Get Session Cookie - HTTP")
        print("data: ", data)
        print("url: ", url)
    try:
        r = session.post(url, json=data,verify=False)
        #print(r)
        r.raise_for_status()

    except requests.exceptions.RequestException as err:
        if DEBUG:
            print("Request Exception:", err)
    except requests.exceptions.HTTPError as errh:
        if DEBUG:
            print("HTTP Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        if DEBUG:
            print("Error Connecting:", errc)
        raise SystemExit(errc)
    except requests.exceptions.Timeout as errt:
        if DEBUG:
            print("Timeout Error:", errt)
        raise SystemExit(errt)


    if not session.cookies:
        data = {'f_user_id':user, 'f_password':password}
        url = http + '://' + ip + '/admin/launch?script=rh&template=login&action=login'

        if DEBUG:
            print("function: authenticate - Get Session Cookie - HTTP")
            print("data: ", data)
            print("url: ", url)
        try:
            r = session.post(url, data=data,verify=False)
        except requests.exceptions.RequestException as err:
            if DEBUG:
                print("Failed to Connect over HTTP")
            return None
        except requests.exceptions.HTTPError as errh:
            if DEBUG:
                print("HTTP Error:", errh)
        except requests.exceptions.ConnectionError as errc:
            if DEBUG:
                print("Error Connecting:", errc)
            raise SystemExit(errc)
        except requests.exceptions.Timeout as errt:
            if DEBUG:
                print("Timeout Error:", errt)
            raise SystemExit(errt)

    if DEBUG:
        print("session cookie: ", session.cookies)
    if not session.cookies:
        return None
    else:
        return session.cookies


def async_cmd(session, ip, cmd):
    data = {"execution_type": "async", "cmd": cmd}
    url = 'http://'+ip+'/admin/launch?script=json'

    if DEBUG:
        print("function: async_cmd")
        print("session cookie: ", session.cookies)
        print("data: ", data)
        print("url: ", url)

    try:
        r = session.post(url, json=data,verify=False)
    except:
        url = 'https://'+ip+'/admin/launch?script=json'
        r = session.post(url, json=data,verify=False)
    x = r.json()

    if DEBUG:
        print(r.text)
        print("function: async_cmd")
        print("job_id: ", x['job_id'])
    return x['job_id']


def wait_for_async(session, ip, job_id):
    import time
    url = 'http://'+ip+'/admin/launch?script=json&job_id='+str(job_id)

    countTime = 0
    while True:
        if DEBUG:
            print(url)
            print("function: wait_for_async")

        try:
            r = session.get(url)
        except:
            url = 'https://'+ip+'/admin/launch?script=json&job_id='+str(job_id)
            r = session.get(url)

        x = r.json()

        if DEBUG:
            print(r.text)
            print(x)

        if "results" in x:
            status = x["results"][0]["status"]
        else:
            status = x["status"]

        if status == 'OK':
            return x["results"][0]
            break
        elif status == 'Error':
            return x["results"][0]
            break
        else:
            countTime = countTime + rate
            if countTime > 600:
                print("waited over 10 minutes for the sysdump to be generated, break")
                return x
                break
        time.sleep(rate)
        # if DEBUG:
        print("waiting for "+x["executed_command"] + " to complete, ", countTime, " seconds")


def checkip(ip):

    ipSplitDot = re.split('\.', ip)
    if DEBUG:
        print("function: checkip")
        print(ipSplitDot)
    if len(ipSplitDot) != 4:
        return False
    for x in ipSplitDot:
        if not x.isdigit():
            return None
        i = int(x)
        if i < 0 or i > 255:
            return None
    return ip


def main():
    DEBUG = False

    parser = argparse.ArgumentParser(description="Creates a session and executes a command")
    parser.add_argument('-u', help='username', required=False, default='admin')
    parser.add_argument('-p', help='password', required=False, default='admin')
    parser.add_argument("-ip", type=str, help='IP address ex: 192.168.1.100')
    parser.add_argument("-rate", type=int, required=False, default=5)
    parser.add_argument('cmd', type=str, default='show version')


    args = vars(parser.parse_args())

    ip = args["ip"]
    username = args["u"]
    password = args["p"]
    rate = args["rate"]
    cmd = args["cmd"]

    s = requests.Session()
    validIp = checkip(ip)
    if validIp is None:
        print("ip is invalid: ", ip)
        exit()

    cookie = authenticate(s, validIp, username, password, 'http')

    if not cookie:
        cookie = authenticate(s, validIp, username, password, 'https')

    job = async_cmd(s, ip, cmd)
    jsonOut = wait_for_async(s, ip, job)
    return jsonOut


if __name__ == "__main__":
    DEBUG = False
    Output = main()
    print(json.dumps(Output, indent=4, sort_keys=True))
