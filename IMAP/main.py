import socket
import ssl

HOST = 'imap.gmail.com' 
PORT = 993

# imap_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# imap_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


# ''' Wrap socket in SSL To make connection by initial handshake '''
# context = ssl.create_default_context()
# imap_socket = context.wrap_socket(imap_socket, server_hostname=HOST)

# imap_socket.connect((HOST, PORT))

# msg = imap_socket.recv(1024).decode()
# print(f'msg: {msg}')

# ''' Login '''
# # email = ''
# # password = ''

# # login_command = f'a01 LOGIN {email} {password} \r\n'
# # imap_socket.send(login_command.encode('ascii'))

# # msg = imap_socket.recv(1024).decode()
# # print(f'msg: {msg}')

# imap_socket.close()
# print('Done Successfully!')



class IMAP:

    HOST = 'imap.gmail.com'
    PORT = 993

    def __init__(self, HOST = HOST, PORT = PORT):
        self.HOST = HOST
        self.PORT = PORT

        # TCP socket
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


        # SSL Wrapper required for security to communicate with smtp server of google
        self.SSL_Wrapper()

        # send connection request
        try:
            self.__socket.connect((self.HOST, self.PORT))
        except Exception as e:
            raise ConnectionError('__Check your internet connection once!')

        # verify confirmation from server
        connection_response = self.__socket.recv(1024).decode()
        print(f'connection response: {connection_response}')
        status = connection_response[2:4]
        if status != 'OK':
            raise ConnectionError(f'Fails to connect {self.HOST, self.PORT}')
        else:
            print(f'connected to {self.HOST, self.PORT} successfully!')

    
    def SSL_Wrapper(self):
        context = ssl.create_default_context()
        self.__socket = context.wrap_socket(self.__socket, server_hostname=self.HOST)


smpt_socket = IMAP()

        