import socket
import ssl
import os
import base64

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


'''
    TLS is successor to SSL
    TLS more secure and performant, most modern web browsers no longer support SSL 2.0 and SSL 3.0

        smtp.gmail.com 
        Requires SSL: Yes 
        Requires TLS: Yes (if available) 
        Requires Authentication: Yes 
        Port for SSL: 465 
        Port for TLS/STARTTLS: 587

'''
'''
Email Provider    IMAP Settings            POP Settings             SMTP Settings

Microsoft 365,    Server:                  Server:                  Server:
Outlook,          outlook.office365.com    outlook.office365.com    smtp.office365.com
Hotmail,          Port: 993                Port: 995                Port: 587
Live.com          Encryption: SSL/TLS      Encryption: SSL/TLS      Encryption: STARTTLS
'''

class MAIL_SERVER:
    def __init__(self, smtp_server, port, is_STARTTLS = True):
        self.smtp_server = smtp_server
        self.port = port
        self.is_STARTTLS = is_STARTTLS

mail_servers = {}
mail_servers['gmail'] = MAIL_SERVER('smtp.gmail.com', 587)
mail_servers['outlook'] = MAIL_SERVER('smtp.office365.com', 587)


class SMTP:

    HELLO_CMD = 'EHLO Tushar'
    STARTTLS_CMD = 'STARTTLS'
    AUTH_CMD = 'AUTH LOGIN'
    MAIL_FROM_CMD = 'MAIL FROM: '
    RCPT_TO_CMD = 'RCPT TO: '
    DATA_CMD = 'DATA'
    CRLF = '\r\n'
    END_MSG_CMD =  '.'
    QUIT_CMD = 'QUIT'

    email_id = os.environ.get('EMAIL_USER')
    email_pwd = os.environ.get('EMAIL_PASS')

    def __init__(self, service_provider = 'gmail'):

        '''
            The following dialog illustrates how a client and server can start a TLS session:
            
            S: <waits for connection on TCP port 25>
            C: <opens connection>
            S: 220 mail.imc.org SMTP service ready
            C: EHLO mail.ietf.org
            S: 250-mail.imc.org offers a warm hug of welcome
            S: 250 STARTTLS
            C: STARTTLS
            S: 220 Go ahead
            C: <starts TLS negotiation>
        '''
        self.service_provider = service_provider
        self.HOST = mail_servers[service_provider].smtp_server
        self.PORT = mail_servers[service_provider].port

        # TCP socket
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # send connection request
        try:
            self.__socket.connect((self.HOST, self.PORT))
        except Exception as e:
            raise Exception('Check your internet connection once!')

        connection_response = self.__socket.recv(1024).decode().rstrip('\r\t\n')
        print(f'connection response: {connection_response}')
        code = connection_response[:3]

        # verify confirmation from server
        if code != '220':
            raise ConnectionError(f'Fails to connect {self.HOST, self.PORT}')
        else:
            print(f'connected to {self.HOST, self.PORT} successfully!')

        self.say_hello()
        self.start_TLS()
        self.SSL_Wrapper()
        self.say_hello() # One more time hello require for outlook

    def say_hello(self):
        code, response = self.send_cmd(self.HELLO_CMD)
        if code != '250':
            print('No acknowledgement for hello')
        # print(f'hello response: {response}')

    def start_TLS(self):
        code, response = self.send_cmd(self.STARTTLS_CMD)
        print(f'STARTTLS response: {response}')
        if code == '501':
            print('Syntax error (no parameteres allowed)')
        elif code == '454':
            print('TLS not available due to temporary reason')

    def send_cmd(self, cmd):
        cmd = cmd + self.CRLF
        self.__socket.send(cmd.encode('ascii'))
        response = self.__socket.recv(1024).decode().rstrip('\r\t\n')
        return response[:3], response

     # SSL Wrapper required for security to communicate with smtp server of google
    def SSL_Wrapper(self):
        context = ssl.create_default_context()
        self.__socket = context.wrap_socket(self.__socket, server_hostname=self.HOST)

    
    def login(self):

        '''
            AUTH cmd
            A server challenge, otherwise known as a ready response, is a 334 reply with the text part containing a BASE64 encoded string. The client answer consists of a line containing a BASE64 encoded string. If the client wishes to cancel an authentication exchange, it issues a line with a single "*". If the server receives such an answer, it MUST reject the AUTH command by sending a 501 reply.

            334 : ready
            501 : rejected
            235 : On successfully completion of Authentication of client
            432 : A password transition is needed
            534 : Authentication mechanism is too weak
            538 : Encryption required for requested authentication mechanism
            454 : Temporary authentication failure
            530 : Authentication required

        Examples:
            S: 220 smtp.example.com ESMTP server ready
            C: EHLO jgm.example.com
            S: 250-smtp.example.com
            S: 250 AUTH CRAM-MD5 DIGEST-MD5
            C: AUTH FOOBAR
            S: 504 Unrecognized authentication type.
            C: AUTH CRAM-MD5
            S: 334
            PENCeUxFREJoU0NnbmhNWitOMjNGNndAZWx3b29kLmlubm9zb2Z0LmNvbT4=
            C: ZnJlZCA5ZTk1YWVlMDljNDBhZjJiODRhMGMyYjNiYmFlNzg2ZQ==
            S: 235 Authentication successful.  
        '''

        '''
            Reference: https://www.ndchost.com/wiki/mail/test-smtp-auth-telnet

            334 VXNlcm5hbWU6; this is a base64 encoded string asking you for your username

            334 UGFzc3dvcmQ6;. Again this is a base64 encoded string now asking for your password
        '''

        code, response = self.send_cmd(self.AUTH_CMD)
        if code == '334':
            print('Server is ready for authentication')
        else:
            raise Exception('Server isn\'t ready for authentication')
        # print(f'code: {code}\nAUTH response: {response}')

        try:
            email_id = self.email_id
            base64_email_id = base64.b64encode(email_id.encode('ascii')).decode() 
            code, response = self.send_cmd(base64_email_id)
            print(f'email response: {response}')
            if code != '334':
                raise Exception()

            email_pwd = self.email_pwd
            base64_email_pwd = base64.b64encode(email_pwd.encode('ascii')).decode() 
            code, response = self.send_cmd(base64_email_pwd)
            print(f'password response: {response}')

            code = response[:3]

            if code != '235':
                raise Exception()
        except Exception:
            raise Exception('Authentication Failed! Invalid Mail ID OR Password')
        
        print(f'Authenticated Successfully!')
    
    def send_email(self, FROM_email, TO_emails):
        self.config_MAIL_FROM(FROM_email)
        for TO_email in TO_emails:
            self.config_RCPT_TO(TO_email)
        self.send_DATA()


    def config_MAIL_FROM(self, email):
        cmd = self.MAIL_FROM_CMD + '<' + email + '>'
        code, response = self.send_cmd(cmd)
        print(f'MAIL FROM response: {response}')
        if code != '250':
            raise Exception('Invalid sender email')
    
    def config_RCPT_TO(self, email):
        cmd = self.RCPT_TO_CMD + '<' + email + '>'
        code, response = self.send_cmd(cmd)
        print(f'RCPT TO response: {response}')
        if code != '250':
            raise Exception('Invalid reciever email')

    def send_DATA(self):
        code, response = self.send_cmd(self.DATA_CMD)
        if code != '354':
            raise Exception('SytaxError. Error occured in DATA cmd')
        
        data = input('Type your message here...\n') + self.CRLF

        self.__socket.send(data.encode('ascii'))

        code, response = self.send_cmd(self.END_MSG_CMD)
        print(f'END MSG response: {response}')

        if code != '250':
            raise Exception('Error occured! Mail not sent successfully! Try again!')
        print('Mail sent successfully <^_^>')
    
    def quit(self):
        code, response =  self.send_cmd(self.QUIT_CMD)
        print(f'QUIT response: {response}')
        if code != '221':
            raise Exception('Error occured while QUIT')
        print('Quit transmission channel successfully!')
    
    def close_connection(self):
        self.__socket.close()
        print('\nDisconnected...')
    


smtp_socket = SMTP()
smtp_socket.login()
smtp_socket.send_email('pathadetushar2@gmail.com', ['tusharpathade475@gmail.com'])
smtp_socket.quit()
smtp_socket.close_connection()

        