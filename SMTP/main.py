import socket
import ssl


# smpt_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# smpt_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# smpt_socket.connect((HOST, PORT))

# ''' Wrap socket in SSL To make connection by initial handshake '''
# context = ssl.create_default_context()
# smpt_socket = context.wrap_socket(smpt_socket, server_hostname=HOST)

# msg = smpt_socket.recv(1024).decode()
# print(f'msg: {msg}')

# # Say Hello
# hello_msg = 'EHLO TUSHAR' + '\r\n.\r\n'
# smpt_socket.send(hello_msg.encode('ascii'))
# response = smpt_socket.recv(1024).decode()
# print(f'response for hello: {response}')

# # LOGIN
# hello_msg = 'AUTH LOGIN' + '\r\n.\r\n'
# smpt_socket.send(hello_msg.encode('ascii'))
# response = smpt_socket.recv(1024).decode()
# print(f'response for login: {response}')

# print('Done Successfully!')


class SMTP:
    HELLO_CMD = 'EHLO Tushar'
    AUTH_CMD = 'AUTH LOGIN'
    MAIL_FROM_CMD = 'MAIL FROM: '
    RCPT_TO_CMD = 'RCPT TO: '
    DATA_CMD = 'DATA'
    END_LINE_CMD = '\r\n' # CRLF
    END_MSG_CMD = END_LINE_CMD + '.'+ END_LINE_CMD

    HOST = 'smtp.gmail.com'
    PORT = 465

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
            raise Exception('Check your internet connection once!')

        # verify confirmation from server
        connection_response = self.__socket.recv(1024).decode()
        print(f'connection response: {connection_response}')
        code = connection_response[:3]
        if code != '220':
            raise ConnectionError(f'Fails to connect {self.HOST, self.PORT}')
        else:
            print(f'connected to {self.HOST, self.PORT} successfully!')

    
    def SSL_Wrapper(self):
        context = ssl.create_default_context()
        self.__socket = context.wrap_socket(self.__socket, server_hostname=self.HOST)


smpt_socket = SMTP()

        