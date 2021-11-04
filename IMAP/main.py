import socket
import ssl
import os
import time
from bs4 import BeautifulSoup
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

class IMAP:

    email_id = os.environ.get('EMAIL_USER')
    email_pwd = os.environ.get('EMAIL_PASS')
    # email_id = os.environ.get('EMAIL_CLG_USER')
    # email_pwd = os.environ.get('EMAIL_CLG_PASS')

    HOST = 'imap.gmail.com'
    # HOST = 'outlook.office365.com'
    PORT = 993

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

    def __init__(self, HOST = HOST, PORT = PORT):
        self.HOST = HOST
        self.PORT = PORT

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
        except Exception as e:
            raise ConnectionError('__Check your internet connection once!')

        # verify confirmation from server
        connection_response = self.__socket.recv(1024).decode().rstrip('\r\t\n')
        print(f'connection response: {connection_response}')
        status = connection_response[2:4]
        if status != 'OK':
            raise ConnectionError(f'Fails to connect {self.HOST, self.PORT}')
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

        self.MailBoxes = []
        folders = []

        for line in lines:
            MailBox = line.split('"/"')[1][1:]
            folder = MailBox.rstrip('"')
            folder = folder.split('/')[-1]
            folders.append(folder)
            self.MailBoxes.append(MailBox)
            # print(MailBox)
        
        return self.MailBoxes, folders

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

    # Open Mailbox
    def Select(self, mailbox):
        SELECT_CMD = f'a003 SELECT {mailbox}'
        code, response = self.Send_CMD(SELECT_CMD)
        print(mailbox)
        print(f'SELECT response: {response}\n')
        if code != 'OK':
            raise Exception('__SELECT Error__')
        self.selected_mailbox = mailbox
    
    # Read Mailbox
    def Examine(self, mailbox):
        EXAMINE_CMD = f'a004 EXAMINE {mailbox}'
        code, response = self.Send_CMD(EXAMINE_CMD)
        print(f'{mailbox} mailbox selected for read only access')
        # print(f'EXAMINE response: {response}\n')
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

    # Fetch Envelope allows atmost 8 mail headers to be fetched
    def fetch_mail_body_structure(self, start_index, count = 1):
        cmd = f'a225 FETCH {start_index}:{start_index + count - 1} (BODYSTRUCTURE)'
        code, response = self.Send_CMD(cmd)
        # print(f'FETCH Body Structure response:\n{response}')
        if code != 'OK':
            raise Exception('__FETCH Body Structure Error__')

        _ = '* ' + str(start_index) + ' FETCH (BODYSTRUCTURE ('
        response = response[len(_): ].split('a225')[0][:-2]
        print(response + '\n')
        # If body has only one part then add parantheses to make following code work
        if response[0] != '(':
            response = '(' + response
            response += ')'
        stack = []
        body_parts = []
        body_part = ''
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

        print(body_parts)
        
        items = []
        for body_part in body_parts:
            item = {}
            body_part = body_part.lower().split(' ')
            length = len(body_part)
            idx = 0
            while(idx < length):
                ele = body_part[idx]
                if ele == 'text':
                    item['text'] = body_part[idx+1]
                    idx += 1
                elif ele == 'charset':
                    item[ele] = body_part[idx+1]
                    idx += 1
                elif ele in ['7bit', '8bit', 'base64', 'quoted-printable']:
                    item['content-transfer-encoding'] = body_part[idx]
                    item['size'] = body_part[idx+1]
                    idx += 1
                elif ele == 'boundary':
                    item[ele] = body_part[idx+1]
                    break
                elif ele == 'application':
                    item[ele] = body_part[idx+1]
                    idx += 1
                elif ele == 'attachement':
                    item[ele] = True
                elif ele == 'filename':
                    item[ele] = body_part[idx+1]
                    idx += 1
                idx += 1
            items.append(item)

        print(items)


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
        '''
            INBOX mailbox selected for read only access
            FETCH ENVELOPE response:
            * 1 FETCH (ENVELOPE ("Mon, 27 May 2019 10:58:27 -0700" "Finish setting up your new Google Account" (("Google Community Team" NIL "googlecommunityteam-noreply" "google.com")) (("Google Community Team" NIL "googlecommunityteam-noreply" "google.com")) (("Google Community Team" NIL "googlecommunityteam-noreply" "google.com")) ((NIL NIL "pathadetushar2" "gmail.com")) NIL NIL NIL "<41b9bff798be5ce06ae19d982183decf2176b622-20063660-110518678@google.com>"))a225 OK Success
            CLOSE Response: a012 OK Returned to authenticated state. (Success)
        '''
        '''
            * 1 FETCH (INTERNALDATE "27-May-2019 17:58:43 +0000")a225 OK Success
        '''

    # For outlook all header elementsa and content-type, content-transfer-encoding, Content-Description, Content-Disposition present in body part
    def fetch_complete_mail(self, start_index):
        # cmd = f'a225 FETCH {start_index} (FLAGS BODY[])' # Reference rfc imap doc page 57
        # code, response = self.Send_CMD(cmd)
        # print(f'FETCH response:\n{response}')
        
        # # file = open('sent-mail-1.txt', 'w+')
        # # file.write(response)
        # # file.close()
        # if code != 'OK':
        #     raise Exception('__FETCH Complete Mail Error__')

        self.__socket.send(f'a222 FETCH {start_index} (FLAGS BODY[1])\r\n'.encode())
        self.__socket.settimeout(10)
        response = self.__socket.recv(39000).decode()
        print(response)
        return

        is_multipart = False
        content_info = {}        
        content_type = 'content-type:'
        content_type_len = len(content_type)
        content_tr_en = 'content-transfer-encoding:'
        content_tr_en_len = len(content_tr_en)
        boundary = 'boundary='
        boundary_len = len(boundary)
        lines = response.splitlines()
        idx = 0
        for line in lines:
            line = line.strip()
            if line.lower().startswith(content_type):
                content_info[content_type] = line[content_type_len+1:].split(';')[0]
                type = content_info[content_type].split('/')
                if type[0].lower() == 'multipart':
                    is_multipart = True
                if is_multipart:
                    boundary_part = line.split(';')[1]
                    if boundary_part[1: boundary_len+1].lower() == boundary:
                        content_info[boundary] = boundary_part[boundary_len+1: ][1:-1]
                        break
                    # if boundary is on 1 line below and not on same line
                    else:
                        idx += 1
                        line = lines[idx].strip().split(';')[0]
                        _ = line[: boundary_len]
                        if _.lower() == boundary:
                            content_info[boundary] = line[boundary_len+1: ][1:-1]
                            break
            elif line.lower().startswith(content_tr_en):
                content_info[content_tr_en] = line[content_tr_en_len+1:].strip()
            # If blank line appears or first body part ends    
            if len(line) == 0:
                idx += 1
                break
            idx += 1
        print(content_info)

        # if body is not multipart type
        if not is_multipart:
            content = ''
            while idx+1 < len(lines):
                line = lines[idx].strip()
                content += line +'\n'
                idx += 1
            print(f'content: {content}')
            return


        # if body is multipart type 
        new_body_part = '--'+content_info[boundary]
        end_of_body = new_body_part + '--'
        body_parts = []
        total_lines = len(lines)
        line = lines[idx].strip()
        while not line.startswith(end_of_body) and idx+1 < total_lines:
            if line.startswith(new_body_part):
                body_part = {}
                idx += 1
                line = lines[idx].strip()
                # Extract content-info for body part
                while(len(line) != 0):
                    info = line.split(';')
                    body_part[info[0].split(' ')[0].lower()] = info[0].split(' ')[1]
                    for i in range(1, len(info)):
                        _ = info[i].strip().split('=')
                        key, value = _[0], _[1]
                        body_part[key.lower()] = value
                    idx += 1
                    line = lines[idx]
                content = ''
                idx += 1
                line = lines[idx].strip()
                while(not line.startswith(new_body_part) and not line.startswith(end_of_body)):
                    content += line +'\n'
                    idx += 1
                    line = lines[idx].strip()
                body_part['content:'] = content
                body_parts.append(body_part)
            elif idx+1 < total_lines:
                idx += 1
                line = lines[idx]
            else:
                break
        
        filePath = 'mail-bodies/' + str(self.selected_mailbox) + '-' + str(start_index) + '.'

        for body_part in body_parts:
            content = body_part['content:']
            if body_part[content_type] == 'text/plain':
                file = filePath + 'txt'
            elif body_part[content_type] == 'text/html':
                file = filePath + 'html'
            else:
                raise Exception(f'{body_part[content_type]} got')
            if body_part[content_tr_en] == 'base64':
                file = open(file, 'w+')
                decoded_content = base64.b64decode(content).decode('utf-8')
                file.write(decoded_content)
                file.close()
            elif body_part[content_tr_en] == 'quoted-printable':
                file = open(file, 'w+')
                # Reference: https://beautiful-soup-4.readthedocs.io/en/latest/#quick-start
                parsed_data = BeautifulSoup(content, features='html.parser')
                decoded_content = QP.decodestring(content).decode('utf-8')
                file.write(decoded_content)
                file.close()
            else:
                raise Exception(f'{body_part[content_tr_en]} got') 

        print(f'total body parts: {len(body_parts)}')    


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

    # Fetch mail body and extract content with mail body of html type
    def fetch_html_body_content(self, start_index, count = 1):
        cmd = f'a225 FETCH {start_index}:{start_index + count} (FLAGS BODY[TEXT])'
        code, response = self.Send_CMD(cmd)
        # print(f'FETCH Body Text response:\n {response}')
        if code != 'OK':
            raise Exception('__FETCH Body Text Error__')
        
        # To extract content from html format data
        # Reference: https://beautiful-soup-4.readthedocs.io/en/latest/#quick-start
        parsed_data = BeautifulSoup(response, features="html.parser")
        for s in parsed_data(['script', 'style']):
            s.decompose()
        content = ' '.join(parsed_data.stripped_strings)
        print(content)
        # print(QP.decodestring(content).decode('utf-8'))

    # Fetch content from plain/text mail body
    def fetch_plain_body_content(self, start_index, count = 1):
        cmd = f'a225 FETCH {start_index}:{start_index + count} (FLAGS BODY[TEXT])'
        code, response = self.Send_CMD(cmd)
        print(f'fetch plain body content response ...\n{response}')
        if code != 'OK':
            raise Exception('__Fetch Error__')
        
        if response[:3] == f'* {start_index}':
            response = response.splitlines()
            length = len(response)
            content = ''
            for i in range(1, length):
                if response[i] == ')':
                    break
                content += response[i] + '\n'

        print('response............')
        print(content)

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

imap_socket = IMAP()
# mailboxes, folders = imap_socket.Get_All_MailBoxes()
# print(mailboxes)
# print(folders)
# for mailbox in mailboxes:
#     imap_socket.Examine(mailbox)
# imap_socket.Examine('"Sent Items"')
# imap_socket.Examine('INBOX')
# imap_socket.Examine('"[Gmail]/Important"')
imap_socket.Examine('"[Gmail]/Sent Mail"')
# imap_socket.Status('INBOX')
# imap_socket.Noop() 
# imap_socket.fetch_complete_mail(1)
# imap_socket.fetch_mail_header(1, 2)
# imap_socket.fetch_html_body_content(3402)
# imap_socket.fetch_plain_body_content(1)
imap_socket.fetch_mail_body_structure(26)
imap_socket.close_mailbox()
imap_socket.Logout()
imap_socket.close_connection()


'''
    References:

    encodings: https://datatracker.ietf.org/doc/html/rfc4648.html#section-4

    For Quoted-Printable strings: https://en.wikipedia.org/wiki/Quoted-printable

    More on encodings: https://stackoverflow.com/questions/25710599/content-transfer-encoding-7bit-or-8-bit

    how to decode QP encoded text: https://stackoverflow.com/questions/43824650/encoding-issue-decode-quoted-printable-string-in-python

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
    
    (("TEXT" "PLAIN" ("CHARSET" "UTF-8") NIL NIL "7BIT" 2 1 NIL NIL NIL)("TEXT" "HTML" ("CHARSET" "UTF-8") NIL NIL "7BIT" 24 1 NIL NIL NIL) "ALTERNATIVE" ("BOUNDARY" "0000000000005ff63b05cffc47c1") NIL NIL)("TEXT" "PLAIN" ("CHARSET" "US-ASCII" "NAME" "Timetable.txt") "<17cec9c74adba9d04031>" NIL "BASE64" 652 14 NIL ("ATTACHMENT" ("FILENAME" "Timetable.txt")) NIL)("TEXT" "PLAIN" ("CHARSET" "US-ASCII" "NAME" "WebPoints.txt") "<17cec9c925ada6f9d392>" NIL "BASE64" 1218 25 NIL ("ATTACHMENT" ("FILENAME" "WebPoints.txt")) NIL)("IMAGE" "PNG" ("NAME" "Screenshot_20211104-213931.png") "<17cec9cf8a6ad0c26313>" NIL "BASE64" 1374868 NIL ("ATTACHMENT" ("FILENAME" "Screenshot_20211104-213931.png")) NIL)("APPLICATION" "OCTET-STREAM" ("NAME" "student_info.py") "<17cec9d5c449ea5ad454>" NIL "BASE64" 2548 NIL ("ATTACHMENT" ("FILENAME" "student_info.py")) NIL) "MIXED" ("BOUNDARY" "0000000000005ff63d05cffc47c3") NIL NIL

    [' ( TEXT PLAIN  ( CHARSET UTF-8 )  NIL NIL 7BIT 2 1 NIL NIL NIL )  ( TEXT HTML  ( CHARSET UTF-8 )  NIL NIL 7BIT 24 1 NIL NIL NIL )  ALTERNATIVE  ( BOUNDARY 0000000000005ff63b05cffc47c1 )  NIL NIL', 'TEXT PLAIN  ( CHARSET US-ASCII NAME Timetable.txt )  <17cec9c74adba9d04031> NIL BASE64 652 14 NIL  ( ATTACHMENT  ( FILENAME Timetable.txt )  )  NIL', 'TEXT PLAIN  ( CHARSET US-ASCII NAME WebPoints.txt )  <17cec9c925ada6f9d392> NIL BASE64 1218 25 NIL  ( ATTACHMENT  ( FILENAME WebPoints.txt )  )  NIL', 'IMAGE PNG  ( NAME Screenshot_20211104-213931.png )  <17cec9cf8a6ad0c26313> NIL BASE64 1374868 NIL  ( ATTACHMENT  ( FILENAME Screenshot_20211104-213931.png )  )  NIL', 'APPLICATION OCTET-STREAM  ( NAME student_info.py )  <17cec9d5c449ea5ad454> NIL BASE64 2548 NIL  ( ATTACHMENT  ( FILENAME student_info.py )  )  NIL', ' MIXED BOUNDARY 0000000000005ff63d05cffc47c3']

    [{'text': 'html', 'charset': 'utf-8', 'content-transfer-encoding': '7bit', 'size': '24', 'boundary': '0000000000005ff63b05cffc47c1'}, {'text': 'plain', 'charset': 'us-ascii', 'content-transfer-encoding': 'base64', 'size': '652', 'filename': 'timetable.txt'}, {'text': 'plain', 'charset': 'us-ascii', 'content-transfer-encoding': 'base64', 'size': '1218', 'filename': 'webpoints.txt'}, {'content-transfer-encoding': 'base64', 'size': '1374868', 'filename': 'screenshot_20211104-213931.png'}, {'application': 'octet-stream', 'content-transfer-encoding': 'base64', 'size': '2548', 'filename': 'student_info.py'}, {'boundary': '0000000000005ff63d05cffc47c3'}]
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

