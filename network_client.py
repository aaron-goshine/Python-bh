
import sys
import socket
import getopt
import threading
import subprocess


# define some globals variables
listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0

def usage ():
    print("Net work client")
    print("Usage: network_client.py -t target_host - port")
    print("-l  --listen  - listen on [host]:[port] for incoming connection")
    print("-e  --execute=file_to_run - execute the given file upon receive a")
    print("connection")
    print("-c  --commnd - upon receiving a connection upload a file and write to")
    print("[destination]")
    print("Example:")
    print("network_client -t 192.168.0.1 -p 5555 -l -c")
    print("network_client -t 192.168.0.1 -p 5555 -l -u=[path to executable]")
    print("network_client -t 192.168.0.1 -p 5555 -l -e=[path to executable]")
    print("echo  'ABCDEFGHI' | ./network_client.py -t 0.0.0.0 -p 123")

def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    # read the commandline options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu", ["help", "listen", "execute", "target", "port", "command", "upload"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    for o,a  in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = True
        elif o in ("-c", "--commandshell"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "Unhandled Option"


    # are e going to listen or just send data
    # from stdin?
    if not listen and len(target) and port > 0:
        # read in the buffer from the commandline
        # this will block, so send CTRL-D if not sending input
        # to stdin
        buffer = sys.stdin.read()

        # send data off
        client_sender(buffer)

    # We are going to listen and potentially
    # upload things, execute commands, and drop and shell
    # back depending on our command line options above
    if listen:
        sever_loop()

main()
