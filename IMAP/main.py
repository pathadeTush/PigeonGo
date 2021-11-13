import socket
import ssl
import os
import time
import quopri as QP
import base64

'''
    imap.gmail.com
    Requires SSL: Yes 
    Port: 99
'''

'''
    In addition to the universal commands (CAPABILITY, NOOP, and LOGOUT),
    and the authenticated state commands (SELECT, EXAMINE, CREATE,
    DELETE, RENAME, SUBSCRIBE, UNSUBSCRIBE, LIST, LSUB, STATUS, and
    APPEND), the following commands are valid in the selected state:
    CHECK, CLOSE, EXPUNGE, SEARCH, FETCH, STORE, COPY, and UID.
'''

class MAIL_SERVER:
    def __init__(self, server, port):
        self.server = server
        self.port = port

imap_servers = {}
imap_servers['gmail.com'] = MAIL_SERVER('imap.gmail.com', 993)
imap_servers['outlook.com'] = MAIL_SERVER('outlook.office365.com', 993)
imap_servers['hotmail.com'] = MAIL_SERVER('outlook.office365.com', 993)
imap_servers['coep.ac.in'] = MAIL_SERVER('outlook.office365.com', 993)


class IMAP:

    # email_id = os.environ.get('EMAIL_USER')
    # email_pwd = os.environ.get('EMAIL_PASS')
    # email_id = os.environ.get('EMAIL_CLG_USER')
    # email_pwd = os.environ.get('EMAIL_CLG_PASS')

    # HOST = 'imap.gmail.com'
    # HOST = 'outlook.office365.com'
    # PORT = 993

    CRLF = '\r\n'

    # Any state's cmd's  
    LOGOUT_CMD = 'a023 LOGOUT'
    CAPABILITY_CMD = 'a444 CAPABILITY'
    NOOP_CMD = 'a155 NOOP'

    # Not Authenticated cmd's
    LOGIN_CMD = 'a001 LOGIN '

    # Authenticated cmd's
    LIST_CMD = 'a002 LIST "" "*"'
    SELECT_CMD = 'a003 SELECT INBOX'
    EXAMINE_CMD = 'a004 EXAMINE INBOX'
    STATUS_CMD = 'a005 STATUS INBOX (UIDNEXT MESSAGES UIDVALIDITY HIGHESTMODSEQ)'

    # Selected State cmd's
    CLOSE_CMD = 'a012 CLOSE'

    def __init__(self, email, password):
        domain = email.strip().split('@')[1].lower()
        # print(email, password
        # , domain)
        if domain not in imap_servers:
            raise Exception('Invalid login credientials!')

        self.email_id = email
        self.email_pwd = password
        self.HOST = imap_servers[domain].server
        self.PORT = imap_servers[domain].port 

        # TCP socket
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.SSL_Wrapper()
        self.Connect()
        self.Login()

    def Send_CMD(self, cmd):
        # self.__socket.settimeout(2)
        cmd = cmd + self.CRLF
        self.__socket.send(cmd.encode())

        status_code = ["OK", "NO", "BAD"]
        complete_response = ''
        while True:
            response = self.__socket.recv(1024).decode('ascii', errors='ignore').rstrip('\r\t\n')
            complete_response += response
            try:
                code = response.split('\n')[-1].split(' ')[1]
            except Exception as e:
                continue 
            if code in status_code:
                break
            continue
        
        return code, complete_response


    ''' Not Authenticated Functions '''

    #  Reference: https://docs.python.org/3/library/ssl.html
    def SSL_Wrapper(self):
        context = ssl.create_default_context()
        self.__socket = context.wrap_socket(self.__socket, server_hostname=self.HOST)

    def Connect(self):
        # send connection request
        try:
            self.__socket.connect((self.HOST, self.PORT))
        except Exception:
            raise Exception('__Check your internet connection once!')

        # verify confirmation from server
        connection_response = self.__socket.recv(1024).decode().rstrip('\r\t\n')
        print(f'connection response: {connection_response}')
        status = connection_response[2:4]
        if status != 'OK':
            print('connect error')
            raise Exception(f'Fails to connect {self.HOST, self.PORT}')
        else:
            print(f'connected to {self.HOST, self.PORT} successfully!')

    def Login(self):
        '''
            C: a001 CAPABILITY
            S: * CAPABILITY IMAP4rev1 STARTTLS LOGINDISABLED
            S: a001 OK CAPABILITY completed
            C: a002 STARTTLS
            S: a002 OK Begin TLS negotiation now
            <TLS negotiation, further commands are under [TLS] layer>
            C: a003 CAPABILITY
            S: * CAPABILITY IMAP4rev1 AUTH=PLAIN
            S: a003 OK CAPABILITY completed
            C: a004 LOGIN joe password
            S: a004 OK LOGIN completed
        '''
        cmd = self.LOGIN_CMD + self.email_id + ' ' + self.email_pwd
        code, response = self.Send_CMD(cmd)
        # print(f'Login response {response}')
        if code != 'OK':
            print('Login Failed!')
            raise Exception('__Invalid Email or Password. Try Again!__')
        print('Authenticated Successfully!')

    ''' Authenticated State Functions '''

    def Get_All_MailBoxes(self):
        code, response = self.Send_CMD(self.LIST_CMD)
        # print(f'List response: {response}')
        if code != 'OK':
            raise Exception('__LIST Error__')

        lines = response.splitlines()
        lines.pop(-1) # OK line

        self.mailboxes = []
        folders = []

        for line in lines:
            mailbox = line.split('"/"')[1][1:]
            self.mailboxes.append(mailbox)

        '''
            ['INBOX', 'All Mail', 'Drafts', 'Important', 'Sent Mail', 'Spam', 'Starred', 'Trash']
        '''
        
        r'''
                 List response: 
            * LIST (\HasNoChildren) "/" "INBOX"
            * LIST (\HasChildren \Noselect) "/" "[Gmail]"
            * LIST (\All \HasNoChildren) "/" "[Gmail]/All Mail"
            * LIST (\Drafts \HasNoChildren) "/" "[Gmail]/Drafts"
            * LIST (\HasNoChildren \Important) "/" "[Gmail]/Important"
            * LIST (\HasNoChildren \Sent) "/" "[Gmail]/Sent Mail"
            * LIST (\HasNoChildren \Junk) "/" "[Gmail]/Spam"
            * LIST (\Flagged \HasNoChildren) "/" "[Gmail]/Starred"
            * LIST (\HasNoChildren \Trash) "/" "[Gmail]/Trash"
            a003 OK Success       
        '''

        '''
            ['Archive', 'Calendar', 'Calendar/Birthdays', '"Calendar/India holidays"', '"Calendar/United Kingdom holidays"', 'Contacts', '"Conversation History"', '"Deleted Items"', 'Drafts', 'INBOX', 'Journal', '"Junk Email"', 'Notes', 'Outbox', '"Sent Items"', 'Tasks']
        '''

    # Open Mailbox (Read/Write)
    def Select(self, mailbox):
        SELECT_CMD = f'a003 SELECT {mailbox}'
        code, response = self.Send_CMD(SELECT_CMD)
        print(mailbox)
        print(f'SELECT response: {response}\n')
        if code != 'OK':
            raise Exception('__SELECT Error__')
        self.selected_mailbox = mailbox
    
    # Read Mailbox (Read Only)
    def Examine(self, mailbox):
        EXAMINE_CMD = f'a004 EXAMINE {mailbox}'
        code, response = self.Send_CMD(EXAMINE_CMD)
        print(f'{mailbox} mailbox selected for read only access')
        print(f'EXAMINE response: {response}\n')
        if code != 'OK':
            raise Exception('__EXAMINE Error__')
        self.selected_mailbox = mailbox
        

    # Check Status of Mailbox (Not used as such)
    def Status(self, mailbox):
        STATUS_CMD = f'a005 STATUS {mailbox} (UIDNEXT MESSAGES UIDVALIDITY HIGHESTMODSEQ)'
        code, response = self.Send_CMD(STATUS_CMD)
        print(f'STATUS response: {response}\n')
        if code != 'OK':
            raise Exception('__STATUS Error__')

    ''' Selected State Function '''

    # Disselect mailbox. Used after Select or Examine
    def close_mailbox(self):
        code, response = self.Send_CMD(self.CLOSE_CMD)
        print(f'CLOSE Response: {response}')
        if code != 'OK':
            raise Exception('__CLOSE Error__')

    def parse_body_structure(self, bodies, item, no, index, level):
        if level > 0:
            decimal_part = (1 / 10**(level))
            int_part_len = len(str(no).split('.')[0])
            no += decimal_part
            no = round(no, int_part_len + level)
           
        ans = {}
        split_arr = item.split(' ')
        length = len(split_arr)
        i = index
        ans['attachment'] = False
        ans['text'] = False
        valid = True
        while(i < length):
            ele = split_arr[i] 
            # print(ele)
            if ele == '(':
                if split_arr[i+1] in ['text', 'image', 'application', '(']:
                    res, no, i = self.parse_body_structure(bodies, item, no, i+1, level+1)
            elif ele in ['text', 'image', 'application']:
                ans[ele] = split_arr[i+1]
                i += 1
            elif ele in ['7bit', '8bit', 'base64', 'quoted-printable']:
                ans['content-transfer-encoding'] = ele
                ans['size'] = split_arr[i+1]
                i += 1
            elif ele == 'charset':
                ans[ele] = split_arr[i+1]
                i += 1
            elif ele == 'filename':
                ans['attachment'] = True
                ans[ele] = split_arr[i+1]
                i += 1
            elif ele in ['alternative', 'related', 'mixed']:
                valid = False
                break
            elif ele == ')' and split_arr[i-1] == 'nil':
                break
            i += 1
        
        res = {}
        if valid:
            res[str(no)] = ans
            bodies.append(res)
            print(res)
        return res, no, i

    def fetch_body_structure(self, start_index):
        # Check start_index with max index
        cmd = f'a225 FETCH {start_index} (BODYSTRUCTURE)'
        code, response = self.Send_CMD(cmd)
        print(f'FETCH Body Structure response:\n{response}')
        if code != 'OK':
            raise Exception('__FETCH Body Structure Error__')

        _ = '* ' + str(start_index) + ' FETCH (BODYSTRUCTURE ('
        response = response[len(_): ].split('a225')[0][:-2]
        # print(response + '\n')
        # If body has only one part then add parantheses to make following code work
        if response[0] != '(':
            response = '(' + response
            response += ')'

        # Separate each item of body structure 
        stack = []
        body_parts = []
        body_part = ''
        response = response.lower()
        for i in range(len(response)):
            ch = response[i]
            if ch == '(':
                stack.append('(')
                if len(stack) > 1:
                    body_part += ' ( '
            elif ch == ')' and len(stack):
                stack.pop()
                if len(stack) == 0:
                    body_parts.append(body_part)
                    body_part = ''
                else:
                    body_part += ' ) '
            else:
                if ch == '"':
                    continue
                body_part += ch

        bodies = []
        for no, body_part in enumerate(body_parts):
            self.parse_body_structure(bodies, body_part, no+1, 0, 0)

        # return

        # Extract Mail Text and Download Attachments
        for body in bodies:
            for key in body:
                try:
                    body_part_no = int(key)
                except:
                    body_part_no = float(key)
                body_part = body[key]
                content = self.fetch_body_part(start_index, body_part_no)
                if body_part['attachment']:
                    filePath = 'downloads/' + str(start_index) + '-' + body_part['filename']
                    binary = False
                    if body_part['text']:
                        file = open(filePath, 'w+')
                    else: # binary file
                        file = open(filePath, 'wb')
                        binary = True
                    encoding = body_part['content-transfer-encoding']
                    if encoding in ['7bit', '8bit']:
                        file.write(content)
                        file.close()
                    elif encoding == 'base64':
                        decoded_content = base64.b64decode(content)
                        # Binary files don't required data in byte
                        if binary:
                            file.write(decoded_content)
                        else:
                            file.write(decoded_content.decode('utf-8'))
                        file.close()
                    elif encoding == 'quoted-printable':
                        decoded_content = QP.decodestring(content)
                        if binary:
                            file.write(decoded_content)
                        else:
                            file.write(decoded_content.decode('utf-8'))
                        file.close()
                    else:
                        print(f'Unknown encoding: {encoding}')
                        break
                elif body_part['text']:
                    filePath = 'downloads/'+ str(start_index) + '-'
                    if body_part['text'] == 'plain':
                        filePath += 'data.txt'
                        file = open(filePath, 'w+')
                    elif body_part['text'] == 'html':
                        filePath += 'data.html'
                        file = open(filePath, 'w+')
                    else:
                        print(f"Unknown text format: {body_part['text']}")
                        break
                    encoding = body_part['content-transfer-encoding']
                    if encoding in ['7bit', '8bit']:
                        file.write(content)
                        file.close()
                    elif encoding == 'base64':
                        decoded_content = base64.b64decode(content).decode('utf-8')
                        file.write(decoded_content)
                        file.close()
                    elif encoding == 'quoted-printable':
                        decoded_content = QP.decodestring(content).decode('utf-8')
                        file.write(decoded_content)
                        file.close()
                    else:
                        print(f'Unknown encoding: {encoding}')
                        break
                break
                    

        '''
            INBOX

            FETCH Body Structure response:
            * 1 FETCH (BODYSTRUCTURE 
            (
                ("TEXT" "PLAIN" 
                    ("CHARSET" "UTF-8" "DELSP" "yes" "FORMAT" "flowed")
                    NIL NIL "BASE64" 4564 92 NIL NIL NIL
                )
                ("TEXT" "HTML" 
                    ("CHARSET" "UTF-8")
                    NIL NIL "QUOTED-PRINTABLE" 38967 780 NIL NIL NIL
                )
                "ALTERNATIVE" 
                    ("BOUNDARY" "00000000000092f1030589e24b62") 
                NIL NIL
            )
            )a225 OK Success
            CLOSE Response: a012 OK Returned to authenticated state. (Success)
        '''

    def fetch_body_part(self, start_index, body_part_no):
        print(body_part_no)
        cmd = f'a225 FETCH {start_index} (FLAGS BODY[{body_part_no}])' # Reference rfc imap doc page 57
        code, response = self.Send_CMD(cmd)
        # print(f'FETCH response:\n{response}')
        
        if code != 'OK':
            raise Exception('__FETCH Complete Mail Error__')
        
        # Remove first line - it is a command itself
        for i in range(len(response)):
            if response[i] == '\n':
                response = response[i+1:]
                break
        # Take response before character ')'
        for i in range(len(response)-1, -1, -1):
            if response[i] == ')':
                response = response[ :i]
                break
        # print(response)
        return response

    def fetch_mail_header(self, start_index, count):
        # A654 FETCH 2:4 (FLAGS BODY[HEADER.FIELDS (DATE FROM)])
        # cmd = f'a225 FETCH {start_index}:{start_index + count} (BODY.PEEK[HEADER])'
        cmd = f'A654 FETCH {start_index}:{start_index + count} (BODY[HEADER.FIELDS (DATE SUBJECT FROM TO BCC Content-Type Content-Transfer-Encoding)])'
        code, response = self.Send_CMD(cmd)
        if code != 'OK':
            raise Exception('__FETCH Error__')
        print(f'FETCH response:\n {response}\n')
        
        if response[-10:-8] == 'OK':
            response = response[: -10] + '\n)\n'

        Headers = []
        header = {}
        lines = response.splitlines()
        for line in lines:
            if line.startswith('Date:') or line.startswith('DATE:'):
                header['Date'] = line[6:]
            elif line.startswith('From:') or line.startswith('FROM:'):
                header['From'] = line[6:]
            elif line.startswith('To:') or line.startswith('TO:'):
                header['To'] = line[4:]
            elif line.startswith('Bcc:') or line.startswith('BCC:'):
                header['Bcc'] = line[5:]
            elif line.startswith('Subject:') or line.startswith('SUBJECT:'):
                header['Subject'] = line[9:]
            elif line.startswith('Content-Type:'):
                header['Content-Type'] = line[14:]
            elif line.startswith('Content-Transfer-Encoding:'):
                header['Content-Transfer-Encoding'] = line[27:]
            elif line == ')':
                Headers.append(header)
                header = {}

        print('Headers.....\n')
        for header in Headers:
            for key in header:
                print(f'{key}: {header[key]}')
            print()

        '''
            Content-Type: text/plain; charset="utf-8"  (for sent mail)

            Content-Type: multipart/alternative; boundary="0000000000003eaeeb059ad8f802"  (for important, Inbox)
        '''


    ''' Any State Functions '''

    def Logout(self):
        code, response = self.Send_CMD(self.LOGOUT_CMD)
        # print(f'logout response: {response}')
        if code != 'OK':
            raise Exception('__LOGOUT Error__')
        print('Logout Successfully!')

    def Noop(self):
        code, response = self.Send_CMD(self.NOOP_CMD)
        # print(f'NOOP response: {response}')
        if code != 'OK':
            raise Exception('__NOOP Error__')
        print('NOOP Successfully!')

    def close_connection(self):
        print('\nDisconnected...')
        self.__socket.close()

# imap_socket = IMAP()
# # mailboxes, folders = imap_socket.Get_All_MailBoxes()
# # print(mailboxes)
# # print(folders)
# # for mailbox in mailboxes:
# #     imap_socket.Examine(mailbox)
# imap_socket.Examine('"Sent Items"')
# # imap_socket.Examine('INBOX')
# # imap_socket.Examine('"[Gmail]/Important"')
# # imap_socket.Examine('"[Gmail]/Sent Mail"')
# # imap_socket.Status('INBOX')
# # imap_socket.Noop() 
# # imap_socket.fetch_body_part(26, 5)
# # imap_socket.fetch_mail_header(1, 2)
# imap_socket.fetch_body_structure(44)
# imap_socket.close_mailbox()
# imap_socket.Logout()
# imap_socket.close_connection()

# TODO Rename, Delete



'''
    References:

    encodings: https://datatracker.ietf.org/doc/html/rfc4648.html#section-4

    For Quoted-Printable strings: https://en.wikipedia.org/wiki/Quoted-printable

    More on encodings: https://stackoverflow.com/questions/25710599/content-transfer-encoding-7bit-or-8-bit

    how to decode QP encoded text: https://stackoverflow.com/questions/43824650/encoding-issue-decode-quoted-printable-string-in-python

    More on Body Structure: http://sgerwk.altervista.org/imapbodystructure.html

    MIME : Multipurpose Internet Mail Extensions (MIME) is an Internet standard that extends the format of email messages to support text in character sets other than ASCII, as well as attachments of audio, video, images, and application programs. Message bodies may consist of multiple parts, and header information may be specified in non-ASCII character sets. Email messages with MIME formatting are typically transmitted with standard protocols, such as the Simple Mail Transfer Protocol (SMTP), the Post Office Protocol (POP), and the Internet Message Access Protocol (IMAP). 

'''

'''
    SELECT

    C: A142 SELECT INBOX
    S: * 172 EXISTS
    S: * 1 RECENT
    S: * OK [UNSEEN 12] Message 12 is first unseen
    S: * OK [UIDVALIDITY 3857529045] UIDs valid
    S: * OK [UIDNEXT 4392] Predicted next UID
    S: * FLAGS (\Answered \Flagged \Deleted \Seen \Draft)
    S: * OK [PERMANENTFLAGS (\Deleted \Seen \*)] Limited
    S: A142 OK [READ-WRITE] SELECT completed
'''

'''
    EXAMINE

    C: A932 EXAMINE blurdybloop
    S: * 17 EXISTS
    S: * 2 RECENT
    S: * OK [UNSEEN 8] Message 8 is first unseen
    S: * OK [UIDVALIDITY 3857529045] UIDs valid
    S: * OK [UIDNEXT 4392] Predicted next UID
    S: * FLAGS (\Answered \Flagged \Deleted \Seen \Draft)
    S: * OK [PERMANENTFLAGS ()] No permanent flags permitted
    S: A932 OK [READ-ONLY] EXAMINE completed
'''

'''
    FETCH Body Structure response:
    * 1 FETCH 
            (
                BODYSTRUCTURE 
                (
                    ("TEXT" "PLAIN" 
                        ("CHARSET" "UTF-8" "DELSP" "yes" "FORMAT" "flowed") 
                        NIL NIL "BASE64" 4564 92 NIL NIL NIL
                    )
                    ("TEXT" "HTML" 
                        ("CHARSET" "UTF-8") 
                        NIL NIL "QUOTED-PRINTABLE" 38967 780 NIL NIL NIL
                    ) 
                    "ALTERNATIVE" 
                    ("BOUNDARY" "00000000000092f1030589e24b62") 
                    NIL NIL
                )
            )
    * 2 FETCH (BODYSTRUCTURE (("TEXT" "PLAIN" ("CHARSET" "UTF-8" "DELSP" "yes" "FORMAT" "flowed") NIL NIL "BASE64" 2274 46 NIL NIL NIL)("TEXT" "HTML" ("CHARSET" "UTF-8") NIL NIL "QUOTED-PRINTABLE" 18212 365 NIL NIL NIL) "ALTERNATIVE" ("BOUNDARY" "000000000000ee5fdc0596f875b8") NIL NIL))
    * 3 FETCH (BODYSTRUCTURE (("TEXT" "PLAIN" ("CHARSET" "UTF-8" "DELSP" "yes" "FORMAT" "flowed") NIL NIL "BASE64" 672 14 NIL NIL NIL)("TEXT" "HTML" ("CHARSET" "UTF-8") NIL NIL "QUOTED-PRINTABLE" 4590 92 NIL NIL NIL) "ALTERNATIVE" ("BOUNDARY" "000000000000d539d5059ad8f32f") NIL NIL))
    * 4 FETCH (BODYSTRUCTURE (("TEXT" "PLAIN" ("CHARSET" "UTF-8" "DELSP" "yes" "FORMAT" "flowed") NIL NIL "BASE64" 898 18 NIL NIL NIL)("TEXT" "HTML" ("CHARSET" "UTF-8") NIL NIL "QUOTED-PRINTABLE" 4884 98 NIL NIL NIL) "ALTERNATIVE" ("BOUNDARY" "0000000000003da410059ad8f419") NIL NIL))
    * 5 FETCH (BODYSTRUCTURE (("TEXT" "PLAIN" ("CHARSET" "UTF-8" "DELSP" "yes" "FORMAT" "flowed") NIL NIL "BASE64" 836 17 NIL NIL NIL)("TEXT" "HTML" ("CHARSET" "UTF-8") NIL NIL "QUOTED-PRINTABLE" 5097 102 NIL NIL NIL) "ALTERNATIVE" ("BOUNDARY" "00000000000041167b059ad8f40f") NIL NIL))
    * 6 FETCH (BODYSTRUCTURE (("TEXT" "PLAIN" ("CHARSET" "UTF-8" "DELSP" "yes" "FORMAT" "flowed") NIL NIL "BASE64" 2614 53 NIL NIL NIL)("TEXT" "HTML" ("CHARSET" "UTF-8") NIL NIL "BASE64" 23678 474 NIL NIL NIL) "ALTERNATIVE" ("BOUNDARY" "0000000000003eaeeb059ad8f802") NIL NIL))
    * 7 FETCH (BODYSTRUCTURE (("TEXT" "PLAIN" ("CHARSET" "utf-8") NIL NIL "QUOTED-PRINTABLE" 3178 64 NIL NIL NIL)("TEXT" "HTML" ("CHARSET" "ascii") NIL NIL "QUOTED-PRINTABLE" 6775 136 NIL NIL NIL) "ALTERNATIVE" ("BOUNDARY" "6496099cfaaa454292ed19801a4c4245") NIL NIL))
    * 8 FETCH (BODYSTRUCTURE (("TEXT" "PLAIN" ("CHARSET" "utf-8") NIL NIL "QUOTED-PRINTABLE" 3682 74 NIL NIL NIL)("TEXT" "HTML" ("CHARSET" "ascii") NIL NIL "QUOTED-PRINTABLE" 15735 315 NIL NIL NIL) "ALTERNATIVE" ("BOUNDARY" "18549ad55ff346e2859b78f3c2f2525d") NIL NIL))

    * 15 FETCH (BODYSTRUCTURE ("TEXT" "PLAIN" NIL NIL NIL "7BIT" 62 2 NIL NIL NIL))
    * 16 FETCH (BODYSTRUCTURE ("TEXT" "PLAIN" NIL NIL NIL "7BIT" 64 2 NIL NIL NIL))
    * 17 FETCH (BODYSTRUCTURE ("TEXT" "PLAIN" NIL NIL NIL "7BIT" 64 2 NIL NIL NIL))
    * 18 FETCH (BODYSTRUCTURE ("TEXT" "PLAIN" NIL NIL NIL "7BIT" 64 2 NIL NIL NIL))
    * 19 FETCH (BODYSTRUCTURE ("TEXT" "PLAIN" NIL NIL NIL "7BIT" 64 2 NIL NIL NIL))
    * 20 FETCH (BODYSTRUCTURE (("TEXT" "PLAIN" ("CHARSET" "us-ascii") NIL NIL "7BIT" 60 2 NIL NIL NIL) "MIXED" ("BOUNDARY" "===============4313263700089492913==") NIL NIL))
    * 21 FETCH (BODYSTRUCTURE (("TEXT" "PLAIN" ("CHARSET" "us-ascii") NIL NIL "7BIT" 60 2 NIL NIL NIL) "MIXED" ("BOUNDARY" "===============0953870309850649022==") NIL NIL))
    * 22 FETCH (BODYSTRUCTURE (("TEXT" "PLAIN" ("CHARSET" "us-ascii") NIL NIL "7BIT" 60 2 NIL NIL NIL)("APPLICATION" "OCTET-STREAM" NIL NIL NIL "BASE64" 34 NIL ("ATTACHEMENT" ("FILENAME" "attachment.txt")) NIL) "MIXED" ("BOUNDARY" "===============2810837026992375651==") NIL NIL))
'''

'''
    for sent mail 26
    
    (
        ("TEXT" "PLAIN" ("CHARSET" "UTF-8") NIL NIL "7BIT" 2 1 NIL NIL NIL)
        ("TEXT" "HTML" ("CHARSET" "UTF-8") NIL NIL "7BIT" 24 1 NIL NIL NIL) 
        "ALTERNATIVE" ("BOUNDARY" "0000000000005ff63b05cffc47c1") NIL NIL)
        ("TEXT" "PLAIN" ("CHARSET" "US-ASCII" "NAME" "Timetable.txt") "<17cec9c74adba9d04031>" NIL "BASE64" 652 14 NIL ("ATTACHMENT" ("FILENAME" "Timetable.txt")) NIL)
        ("TEXT" "PLAIN" ("CHARSET" "US-ASCII" "NAME" "WebPoints.txt") "<17cec9c925ada6f9d392>" NIL "BASE64" 1218 25 NIL ("ATTACHMENT" ("FILENAME" "WebPoints.txt")) NIL)("IMAGE" "PNG" ("NAME" "Screenshot_20211104-213931.png") "<17cec9cf8a6ad0c26313>" NIL "BASE64" 1374868 NIL ("ATTACHMENT" ("FILENAME" "Screenshot_20211104-213931.png")) NIL)("APPLICATION" "OCTET-STREAM" ("NAME" "student_info.py") "<17cec9d5c449ea5ad454>" NIL "BASE64" 2548 NIL ("ATTACHMENT" ("FILENAME" "student_info.py")) NIL) "MIXED" ("BOUNDARY" "0000000000005ff63d05cffc47c3") NIL NIL

    [' 
        ( TEXT PLAIN  ( CHARSET UTF-8 )  NIL NIL 7BIT 2 1 NIL NIL NIL )  
        ( TEXT HTML  ( CHARSET UTF-8 )  NIL NIL 7BIT 24 1 NIL NIL NIL )  ALTERNATIVE  ( BOUNDARY 0000000000005ff63b05cffc47c1 )  NIL NIL', 
        'TEXT PLAIN  ( CHARSET US-ASCII NAME Timetable.txt )  <17cec9c74adba9d04031> NIL BASE64 652 14 NIL  ( ATTACHMENT  ( FILENAME Timetable.txt )  )  NIL'
        , 'TEXT PLAIN  ( CHARSET US-ASCII NAME WebPoints.txt )  <17cec9c925ada6f9d392> NIL BASE64 1218 25 NIL  ( ATTACHMENT  ( FILENAME WebPoints.txt )  )  NIL'
        , 'IMAGE PNG  ( NAME Screenshot_20211104-213931.png )  <17cec9cf8a6ad0c26313> NIL BASE64 1374868 NIL  ( ATTACHMENT  ( FILENAME Screenshot_20211104-213931.png )  )  NIL'
        , 'APPLICATION OCTET-STREAM  ( NAME student_info.py )  <17cec9d5c449ea5ad454> NIL BASE64 2548 NIL  ( ATTACHMENT  ( FILENAME student_info.py )  )  NIL'
        , ' MIXED BOUNDARY 0000000000005ff63d05cffc47c3'
    ]

    [
        {'text': 'html', 'charset': 'utf-8', 'content-transfer-encoding': '7bit', 'size': '24', 'boundary': '0000000000005ff63b05cffc47c1'}, 
        {'text': 'plain', 'charset': 'us-ascii', 'content-transfer-encoding': 'base64', 'size': '652', 'filename': 'timetable.txt'}, 
        {'text': 'plain', 'charset': 'us-ascii', 'content-transfer-encoding': 'base64', 'size': '1218', 'filename': 'webpoints.txt'}, 
        {'content-transfer-encoding': 'base64', 'size': '1374868', 'filename': 'screenshot_20211104-213931.png'}, {'application': 'octet-stream', 'content-transfer-encoding': 'base64', 'size': '2548', 'filename': 'student_info.py',{'boundary': '0000000000005ff63d05cffc47c3'}
    ]
'''

r'''
    LIST

    C: A101 LIST "" ""
    S: * LIST (\Noselect) "/" ""
    S: A101 OK LIST Completed
    C: A102 LIST #news.comp.mail.misc ""
    S: * LIST (\Noselect) "." #news.
    S: A102 OK LIST Completed
    C: A103 LIST /usr/staff/jones ""
    S: * LIST (\Noselect) "/" /
    S: A103 OK LIST Completed
    C: A202 LIST ~/Mail/ %
    S: * LIST (\Noselect) "/" ~/Mail/foo
    S: * LIST () "/" ~/Mail/meetings
    S: A202 OK LIST completed
'''

