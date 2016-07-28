
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


def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # connect to our target host
        client.connect((target, port))

        if len(buffer):
            client.send(buffer)

        while True:
            # now wait for data back
            recv_len = 1
            response = ""
            while recv_len:
                data = client.recv(4096)
                response += data

                if recv_len < 4096:
                    break

            print(response, end="")
            # wait for more input
            buffer = raw_input("")
            print(buffer)

            # send it off
            client.send(buffer)

    except:
        print("[*] Exception! Exiting")
        # Tear down the connection
        client.close()

def sever_loop ():
    global target
    # if no target is defined, we listen on all interfaces
    if not len(target):
        target = "0.0.0.0"
    server = socket.socket(socket.AF_INET, socket.socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)

    while True:
        client_socket, addr = server.accept()
        # spin off a thread to handle our new client
        client_thread = threading.Thread(target=client_handler,
                args=(client_socket,))
        client_thread.start()

def run_command(command):
    # trim the newline
    command = command.rstrip()

    # run the command and get the output back
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT,
                 shell = True)
    except:
        output = "Fail to execute command. \r\n"

    # send the output back to the client
    return output

def client_handler (client_socket):
    global upload
    global execute
    global command

    # check for upload
    if len(upload_destination):
        # read in all of the bytes and write to our destination
        file_buffer = ""

        # keep reading data until non is available
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            else:
                file_buffer += data
        # now we take these bytes and try to write them out
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            # acknowledge that we wrote the file out
            client_socket.send("Succesfully save file to %s\r\n" % upload_destination)
        except:
            client_socket.send("Fail to save file to %s\r\n" % upload_destination)

    # check for command execution
    if len(execute):

        # run the command
        output = run_command(execute)
        client_socket.send(output)

    if commnad:
        while True:
            # show a simple prompt
            client_socket.send("<IAM:#>")

            # now we receive until we see  a linefeed (enter key)
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)

            # send back the command output
            response = run_command(cmd_buffer)

            # send back the response
            client_socket.send(response)
main()
