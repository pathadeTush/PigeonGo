import socket
import ssl
import os
import base64
import time
from app import app

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
    def __init__(self, server, port):
        self.server = server
        self.port = port

smtp_servers = {}
smtp_servers['gmail.com'] = MAIL_SERVER('smtp.gmail.com', 587)
smtp_servers['outlook.com'] = MAIL_SERVER('smtp.office365.com', 587)
smtp_servers['hotmail.com'] = MAIL_SERVER('smtp.office365.com', 587)
smtp_servers['coep.ac.in'] = MAIL_SERVER('smtp.office365.com', 587)



class SMTP:

    # Timeouts as per RFC 5321  section 4.5.3.2 https://datatracker.ietf.org/doc/html/rfc5321#section-4.5.3.2
    CONN_TOUT = 300 # 5 min
    MAIL_TOUT = 300 # 5 min
    RCPT_TOUT = 300 # 5 min
    DATA_INITIATION_TOUT = 120 # 2 min
    DATA_BLOCK_TOUT = 180 # 3 min
    DATA_TERMINATION_TOUT = 600 # 10 min

    # CONN_TOUT = None # 5 min
    # MAIL_TOUT = None # 5 min
    # RCPT_TOUT = None # 5 min
    # DATA_INITIATION_TOUT = None # 2 min
    # DATA_BLOCK_TOUT = None # 3 min
    # DATA_TERMINATION_TOUT = None # 10 min


    # Commands as per RFC 5321 https://datatracker.ietf.org/doc/html/rfc5321
    HELLO_CMD = 'EHLO Greetings'
    STARTTLS_CMD = 'STARTTLS'
    AUTH_CMD = 'AUTH LOGIN'
    MAIL_FROM_CMD = 'MAIL FROM: '
    RCPT_TO_CMD = 'RCPT TO: '
    DATA_CMD = 'DATA'
    CRLF = '\r\n'
    END_MSG_CMD = CRLF + '.' + CRLF
    QUIT_CMD = 'QUIT'

    # email_id = os.environ.get('EMAIL_USER')
    # email_pwd = os.environ.get('EMAIL_PASS')

    def __init__(self, email, password):
        # print("\tin __init__ SMTP")

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
        domain = email.strip().split('@')[1].lower()
        if domain not in smtp_servers:
            raise Exception('Invalid login credientials!')

        self.pending = False

        self.email_id = email
        self.email_pwd = password
        self.HOST = smtp_servers[domain].server
        self.PORT = smtp_servers[domain].port

        # TCP socket
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.connect()
        self.say_hello()
        self.start_TLS()
        self.SSL_Wrapper()
        self.say_hello() # One more time hello require for outlook
        self.login()

    def connect(self):
        # print("\tin connect SMTP")
        # send connection request
        self.__socket.settimeout(self.CONN_TOUT)
        try:
            self.__socket.connect((self.HOST, self.PORT))
        except Exception as e:
            raise Exception('Check your internet connection once!')
        self.__socket.settimeout(None)

        connection_response = self.__socket.recv(1024).decode(errors='ignore').rstrip('\r\t\n')
        # print(f'connection response: {connection_response}')
        code = connection_response[:3]

        # verify confirmation from server
        if code != '220':
            raise Exception(f'Fails to connect {self.HOST, self.PORT}')
        # print(f'connected to {self.HOST, self.PORT} successfully!')

    def say_hello(self):
        # print("\tin say_hello SMTP")
        cmd = self.HELLO_CMD
        code, response = self.send_cmd(cmd)
        if code != '250':
            # print('No acknowledgement for hello')
            raise Exception('No acknowledgement for hello')
        # print(f'hello response: {response}')

    def start_TLS(self):
        # print("\tin start_TLS SMTP")
        code, response = self.send_cmd(self.STARTTLS_CMD)
        # print(f'STARTTLS response: {response}')
        if code == '501':
            # print('Syntax error (no parameteres allowed)')
            raise Exception('Syntax error (no parameteres allowed)')
        elif code == '454':
            raise Exception('TLS not available due to temporary reason')

    def send_cmd(self, cmd):
        # print("\tin send_cmd SMTP")
        self.pending = True
        self.__socket.settimeout(60)
        cmd = cmd + self.CRLF
        try:
            self.__socket.send(cmd.encode('ascii'))
            response = self.__socket.recv(1024).decode(errors='ignore').rstrip('\r\t\n')
        except socket.timeout:
            self.__socket.settimeout(None)
            self.pending = False
            raise Exception('Looks like u have bad network! Try again...')
        self.__socket.settimeout(None)
        self.pending = False
        return response[:3], response

     # SSL Wrapper required for security to communicate with smtp server of google
    #  Reference: https://docs.python.org/3/library/ssl.html
    def SSL_Wrapper(self):
        # print("\tin SSL_Wrapper SMTP")
        context = ssl.create_default_context()
        self.__socket = context.wrap_socket(self.__socket, server_hostname=self.HOST)
    
    def login(self):
        # print("\tin login SMTP")

        '''
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
            pass
            # print('Server is ready for authentication')
        else:
            raise Exception('Server isn\'t ready for authentication')
        # print(f'code: {code}\nAUTH response: {response}')

        try:
            email_id = self.email_id
            base64_email_id = base64.b64encode(email_id.encode('ascii')).decode() 
            code, response = self.send_cmd(base64_email_id)
            # print(f'email response: {response}')
            if code != '334':
                raise Exception()

            email_pwd = self.email_pwd
            base64_email_pwd = base64.b64encode(email_pwd.encode('ascii')).decode() 
            code, response = self.send_cmd(base64_email_pwd)
            # print(f'password response: {response}')

            code = response[:3]

            if code != '235':
                raise Exception()
        except Exception:
            raise Exception('Authentication Failed! Invalid Mail ID OR Password')
        
        # print(f'Authenticated Successfully!')
    
    def send_email(self, TO_email, Subject, Body, Attachment = False):
        # print("\tin send_email SMTP")
        if Attachment:
            # print("=====Sending Mail With Attachments======")
            self.send_email_with_attachment(TO_email, Subject, Body, Attachment)
            return

        self.email = ''
        self.add_email_header(TO_email, Subject)
        self.add_blank_line()
        body = Body
        self.add_email_body_text(body)

        # Send Data
        self.send_DATA(self.email)
        self.terminate_DATA()

    def add_email_header(self, TO_email, Subject):
        # print("\tin add_email_header SMTP")
        FROM_email = self.email_id
        header = ''
        header += f'From: {FROM_email}' + self.CRLF
        header += f'To: {TO_email}' + self.CRLF
        header += f'Subject: {Subject}' + self.CRLF
        self.email += header

        self.config_MAIL_FROM(FROM_email)
        # print(f'to_email - {TO_email}')
        self.config_RCPT_TO(TO_email)
        self.initiate_DATA()

    def add_blank_line(self):
        # print("\tin add_blank_line SMTP")
        self.email += self.CRLF

    def add_email_body_text(self, body_text):
        # print("\tin add_email_body_text SMTP")
        self.email += body_text + self.CRLF

    def config_MAIL_FROM(self, email):
        # print("\tin config_MAIL_FROM SMTP")
        self.__socket.settimeout(self.MAIL_TOUT)
        try:
            cmd = self.MAIL_FROM_CMD + '<' + email + '>'
            code, response = self.send_cmd(cmd)
        except socket.timeout:
            raise Exception('__MAIL Timeout Crossed!__')
        self.__socket.settimeout(None)
        # print(cmd)
        # print(f'MAIL FROM response: {response}')
        if code != '250':
            raise Exception('Invalid sender email')
    
    def config_RCPT_TO(self, email):
        # print("\tin config_RCPT_TO SMTP")
        self.__socket.settimeout(self.RCPT_TOUT)
        try:
            cmd = self.RCPT_TO_CMD + '<' + email + '>'
            code, response = self.send_cmd(cmd)
        except socket.timeout:
            raise Exception('__RCPT Timeout crossed!__')
        self.__socket.settimeout(None)
        # print(f'RCPT TO response: {response}')

        if code == '551':
            email = response.split('>')[0].split('<')[1]
            self.config_RCPT_TO(email)

        if code not in ('250', '251'):
            raise Exception('Invalid reciever email')

    def initiate_DATA(self):
        # print("\tin initiate_DATA SMTP")
        self.__socket.settimeout(self.DATA_INITIATION_TOUT)
        try:
            code, response = self.send_cmd(self.DATA_CMD)
        except socket.timeout():
            raise Exception('__DATA Intiation Timeout Crossed!__')
        self.__socket.settimeout(None)
        if code != '354':
            raise Exception('SytaxError. Error occured in DATA cmd')

    def send_DATA(self, data):
        # print("\tin send_DATA SMTP")
        self.__socket.settimeout(self.DATA_BLOCK_TOUT)
        try: 
            self.__socket.send(data.encode('ascii'))
        except socket.timeout():
            raise Exception('__DATA BLOCK Timeout Crossed!__')
        self.__socket.settimeout(None)

    def terminate_DATA(self):
        # print("\tin terminate_DATA SMTP")
        self.__socket.settimeout(self.DATA_TERMINATION_TOUT)
        try: 
            code, response = self.send_cmd(self.END_MSG_CMD)
        except socket.timeout():
            raise Exception('__DATA BLOCK Timeout Crossed!__')
        self.__socket.settimeout(None)

        # print(f'END MSG response: {response}')

        if code != '250':
            raise Exception('Error occured! Mail not sent successfully! Try again!')
        # print('Mail sent successfully ^_^')

    def send_email_with_attachment(self, TO_email, Subject, Body, attachments):
        # print("\tin send_email_with_attachment_DATA SMTP")
        self.email = ''
        boundary = '===============0331756459957505656=='
        
        # Main Header 
        self.add_email_header(TO_email, Subject)
        self.add_contentType_MIMEVersion_to_header(boundary)

        # Blank Line
        self.add_blank_line()

        # Body (Body Part1 + Body Part2 + Body Part3 + .....)

        # Body Part
        # Boundary
        self.add_start_boundary(boundary)
        # Blank Line After Header
        # self.add_blank_line()
        # Body Part
        body = Body
        self.email += body + self.CRLF

        for attachment in attachments:
            self.add_start_boundary(boundary)
            encoding = self.add_body_part_header(attachment)
            self.add_body_content(attachment, encoding)

        self.add_closing_boundary(boundary)

        # Send data
        self.send_DATA(self.email)
        self.terminate_DATA()

    def add_contentType_MIMEVersion_to_header(self, boundary, type = 'multipart', subtype = 'mixed'):
        # print("\tin add_contentType_MIMEVersion_to_header SMTP")
        self.email += f'Content-Type: {type}/{subtype}; boundary="{boundary}"' + self.CRLF
        self.email += 'MIME-Version: 1.0' + self.CRLF

    def add_start_boundary(self, boundary):
        # print("\tin add_start_boundary SMTP")
        self.email += self.CRLF + '--' + f'{boundary}' + self.CRLF
    
    def add_closing_boundary(self, boundary):
        # print("\tin add_closing_boundary SMTP")
        self.email += self.CRLF + '--' f'{boundary}' + '--' + self.CRLF

    def add_body_part_header(self, attachment):
        # print("\tin add_body_part_header SMTP")
        # print(attachment)
        filename = attachment['filename'].strip()
        mimetype = attachment['mimetype']
        if not mimetype:
            mimetype = self.get_MIMEType(filename)
        # print(mimetype)
        _ = mimetype.split('/')
        type, subtype = _[0].strip(), _[1].strip()
        if type == 'text':
            encoding = '7bit'
        else:
            encoding = 'base64'
        self.email += f'Content-Type: {type}/{subtype};' + self.CRLF
        self.email += 'Content-Transfer-Encoding: ' + f'{encoding}' + self.CRLF
        self.email += 'Content-Disposition: attachment; filename=' + f'{filename}' + self.CRLF
        return encoding

    def add_body_content(self, attachment, encoding = 'base64'):
        # print("\tin add_body_content SMTP")
        file_path = os.path.join(app.config['ATTACHMENT_DIR'], attachment['filename'])
        if encoding.lower().strip() in ['7bit', '8bit']:
            try:
                file = open(file_path, 'r')
            except Exception:
                # print(f'Invalid filepath: {file_path}')
                raise Exception(f'Invalid filepath: {file_path}')
            content = file.read()
            file.close()
            self.email += f'{content}' + self.CRLF
            return
        else:
            try:
                file = open(file_path, 'rb')
            except Exception:
                raise Exception(f'Invalid filepath: {file_path}')
            content = file.read()
            file.close()
            encode_content = base64.b64encode(content).decode(errors='ignore')
            self.email += f'{encode_content}' + self.CRLF
            return

    def get_MIMEType(self, file):
        # print("\tin get_MIMEType SMTP")
        extension = file.split('.')[-1].lower().strip()
        # print(f'file = {file} extension: {extension}')
        mimefile_path = os.path.abspath('.') + '/SMTP/google_MIME_Types.txt'
        mimefile = open(mimefile_path, 'r')
        # print('mime file opened')
        data = mimefile.read()
        mimefile.close()
        # print('mime file read')
        lines = data.splitlines()

        for line in lines:
            _ = line.split('|')
            mimetype, extensions = _[0].strip(), _[1].strip().split(',')
            if extension in extensions:
                return mimetype
        # print('mimetype not found')
        return 'application/octet-stream'

    def quit(self):
        # print("\tin quit SMTP")
        code, response =  self.send_cmd(self.QUIT_CMD)
        # print(f'QUIT response: {response}')
        if code != '221':
            raise Exception('Error occured while QUIT')
        # print('Quit transmission channel successfully!')
    
    def close_connection(self):
        # print("\tin close_connection SMTP")
        self.__socket.close()
        # print('\nDisconnected...')
    

if __name__ == '__main__':
    smtp_socket = SMTP(os.environ.get('EMAIL_USER'), os.environ.get('EMAIL_PASS'))
    smtp_socket.send_email('tusharpathade475@gmail.com', 'Mail from imap-smtp client', 'This is Body of mail!')
    # smtp_socket.send_email_with_attachment('tusharpathade475@gmail.com', 'Mailing from imap-smtp client With Attachments', ['attachment.txt', 'img.png'])
    smtp_socket.quit()
    smtp_socket.close_connection()


'''
    Reference:
        Mime Types List: https://cloud.google.com/appengine/docs/standard/php/mail/mail-with-headers-attachments ,
                         https://www.iana.org/assignments/media-types/media-types.xhtml#multipart

        Mime Types: https://www.w3.org/Protocols/rfc1341/7_2_Multipart.html
                    https://www.w3.org/Protocols/rfc1341/0_TableOfContents.html



   Reference: https://partners-intl.aliyun.com/help/doc-detail/51584.htm
    Content type is in the form of: Content-Type: [type]/[subtype].
    The type is in the form of:

        Text: for standard representation of a text message, which may consist of various character sets or formats.
        Image: for transfer of static image data.
        Audio: for transfer of audio or sound data.
        Video: for transfer of dynamic image data, which may be a video data format that includes audio.
        Application: for transfer of application data or binary data.
        Message: for packing an email message.
        Multipart: for connecting multiple content parts to form a message, the parts can be different types of data.

    The subtype form can be:

        text/plain (plain text)
        text/html (HTML document)
        application/xhtml+xml (XHTML document)
        image/gif (GIF image)
        image/jpeg (JPEG image)
        image/png (PNG image)
        video/mpeg (MPEG video)
        application/octet-stream (Any binary data)
        message/rfc822 (RFC 822 form)
        multipart/alternative (HTML form and plain text form of HTML mail, the same content is expressed in different forms.)

    Content Transfer Encoding specifies the character encoding method used in the content area. Typical methods include 7bit, 8bit, binary, quoted-printable, and base64.

'''