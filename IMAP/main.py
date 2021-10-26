import socket
import ssl
import os
import time

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
        Response = ''
        while True:
            response = self.__socket.recv(1024).decode().rstrip('\r\t\n')
            try:
                code = response.split('\n')[-1].split(' ')[1]
            except:
                pass 
            else:
                Response += response
                if code in status_code:
                    break
                continue
        
        return code, Response


    ''' Not Authenticated Functions '''

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

        MailBoxes = []
        folders = []

        for line in lines:
            MailBox = line.split('"/"')[1][1:]
            folder = MailBox[1:-1]
            folder = folder.split('/')[-1]
            if folder != '[Gmail]':
                folders.append(folder)
                MailBoxes.append(MailBox)
                # print(MailBox)
        
        return MailBoxes, folders

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

    # Open Mailbox
    def Select(self, mailbox):
        SELECT_CMD = f'a003 SELECT {mailbox}'
        code, response = self.Send_CMD(SELECT_CMD)
        print(mailbox)
        print(f'SELECT response: {response}\n')
        if code != 'OK':
            raise Exception('__SELECT Error__')
    
    # Read Mailbox
    def Examine(self, mailbox):
        EXAMINE_CMD = f'a004 EXAMINE {mailbox}'
        code, response = self.Send_CMD(EXAMINE_CMD)
        print(mailbox)
        print(f'EXAMINE response: {response}\n')
        if code != 'OK':
            raise Exception('__EXAMINE Error__')

    # Check Status of Mailbox
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

    def fetch_complete_mail(self, start_index):
        cmd = f'a225 FETCH {start_index}:{start_index+1} (FLAGS BODY[])'
        code, response = self.Send_CMD(cmd)
        # print(f'FETCH response:\n {response}')
        file = open('inbox-1.txt', 'w+')
        file.write(response)
        file.close()
        if code != 'OK':
            raise Exception('__FETCH Complete Mail Error__')

    def fetch_mail_header(self, start_index, count):
        cmd = f'a225 FETCH {start_index}:{start_index + count - 1} (FLAGS BODY])'
        code, response = self.Send_CMD(cmd)
        print(f'FETCH response:\n {response}')
        if code != 'OK':
            raise Exception('__FETCH Error__')

        '''
            HEADER
             * 1 FETCH (FLAGS (\Seen) BODY[HEADER] {665}
            Return-Path: <pathadetushar2@gmail.com>
            Received: from [127.0.1.1] ([117.233.122.76]) by smtp.googlemail.com with
            ESMTPSA id c21sm3429394pfo.91.2021.04.11.00.31.34 for
            <tusharpathade475@gmail.com> (version=TLS1_3 cipher=TLS_AES_256_GCM_SHA384
            bits=256/256); Sun, 11 Apr 2021 00:31:36 -0700 (PDT)
            From: pathadetushar2@gmail.com
            X-Google-Original-From: noreply@demo.com
            Content-Type: text/plain; charset="utf-8"
            MIME-Version: 1.0
            Content-Transfer-Encoding: 7ba225 OK Success
        '''

    def fetch_mail_body_structure(self, start_index, count = 1):
        cmd = f'a225 FETCH {start_index}:{start_index + count - 1} (BODYSTRUCTURE)'
        code, response = self.Send_CMD(cmd)
        print(f'FETCH Body Structure response:\n {response}')
        if code != 'OK':
            raise Exception('__FETCH Body Structure Error__')

        '''
            INBOX
            EXAMINE response: * FLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing)
            * OK [PERMANENTFLAGS ()] Flags permitted.
            * OK [UIDVALIDITY 1] UIDs valid.
            * 65 EXISTS
            * 0 RECENT
            * OK [UIDNEXT 66] Predicted next UID.
            * OK [HIGHESTMODSEQ 25029]
            a004 OK [READ-ONLY] INBOX selected. (Success)

            FETCH Body Structure response:
            * 1 FETCH (BODYSTRUCTURE (("TEXT" "PLAIN" ("CHARSET" "UTF-8" "DELSP" "yes" "FORMAT" "flowed") NIL NIL "BASE64" 4564 92 NIL NIL NIL)("TEXT" "HTML" ("CHARSET" "UTF-8") NIL NIL "QUOTED-PRINTABLE" 38967 780 NIL NIL NIL) "ALTERNATIVE" ("BOUNDARY" "00000000000092f1030589e24b62") NIL NIL))a225 OK Success
            CLOSE Response: a012 OK Returned to authenticated state. (Success)
        '''

    def fetch_mail_body_text(self, start_index, count = 1):
        cmd = f'a225 FETCH {start_index}:{start_index + count - 1} (FLAGS BODY[TEXT])'
        code, response = self.Send_CMD(cmd)
        print(f'FETCH Body Text response:\n {response}')
        if code != 'OK':
            raise Exception('__FETCH Body Text Error__')


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
# imap_socket.Examine('INBOX')
imap_socket.Examine('"[Gmail]/Sent Mail"')
# imap_socket.Status('INBOX')
# imap_socket.Noop() 
# imap_socket.fetch_complete_mail(1)
# imap_socket.fetch_mail_header(1, 1)
# imap_socket.fetch_mail_body_structure(1)
imap_socket.fetch_mail_body_text(1)
imap_socket.close_mailbox()
imap_socket.Logout()
imap_socket.close_connection()

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
    CREATE

    C: A003 CREATE owatagusiam/
    S: A003 OK CREATE completed
    C: A004 CREATE owatagusiam/blurdybloop
    S: A004 OK CREATE completed
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



'''
    def capability(self):
        code, response = self.send_cmd(self.CAPABILITY_CMD)
        print(f'capability response: {response}')
        if code != 'OK':
            raise Exception('__CAPABILITY Error__')
    
    def start_TLS(self):
        code, response = self.send_cmd(self.STARTTLS_CMD, True)
        # print(f'STARTTLS response: {response}')
        if code != 'OK':
            raise Exception('__STARTTLS Error__')

'''

'''

LAST Response

    connection response: * OK Gimap ready for requests from 117.228.193.165 q13mb189540682pjq
    connected to ('imap.gmail.com', 993) successfully!
    Authenticated Successfully!
    ['"INBOX"', '"[Gmail]/All Mail"', '"[Gmail]/Drafts"', '"[Gmail]/Important"', '"[Gmail]/Sent Mail"', '"[Gmail]/Spam"', '"[Gmail]/Starred"', '"[Gmail]/Trash"']
    ['INBOX', 'All Mail', 'Drafts', 'Important', 'Sent Mail', 'Spam', 'Starred', 'Trash']
    "INBOX"
    SELECT response: * FLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing)
    * OK [PERMANENTFLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing \*)] Flags permitted.
    * OK [UIDVALIDITY 1] UIDs valid.
    * 65 EXISTS
    * 0 RECENT
    * OK [UIDNEXT 66] Predicted next UID.
    * OK [HIGHESTMODSEQ 22748]
    a002 OK [READ-WRITE] INBOX selected. (Success)

    "[Gmail]/All Mail"
    SELECT response: * FLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing)
    * OK [PERMANENTFLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing \*)] Flags permitted.
    * OK [UIDVALIDITY 12] UIDs valid.
    * 88 EXISTS
    * 0 RECENT
    * OK [UIDNEXT 97] Predicted next UID.
    * OK [HIGHESTMODSEQ 22748]
    a002 OK [READ-WRITE] [Gmail]/All Mail selected. (Success)

    "[Gmail]/Drafts"
    SELECT response: * FLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing)
    * OK [PERMANENTFLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing \*)] Flags permitted.
    * OK [UIDVALIDITY 6] UIDs valid.
    * 0 EXISTS
    * 0 RECENT
    * OK [UIDNEXT 7] Predicted next UID.
    * OK [HIGHESTMODSEQ 22748]
    a002 OK [READ-WRITE] [Gmail]/Drafts selected. (Success)

    "[Gmail]/Important"
    SELECT response: * FLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing)
    * OK [PERMANENTFLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing \*)] Flags permitted.
    * OK [UIDVALIDITY 9] UIDs valid.
    * 8 EXISTS
    * 0 RECENT
    * OK [UIDNEXT 9] Predicted next UID.
    * OK [HIGHESTMODSEQ 22748]
    a002 OK [READ-WRITE] [Gmail]/Important selected. (Success)

    "[Gmail]/Sent Mail"
    SELECT response: * FLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing)
    * OK [PERMANENTFLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing \*)] Flags permitted.
    * OK [UIDVALIDITY 5] UIDs valid.
    * 23 EXISTS
    * 0 RECENT
    * OK [UIDNEXT 24] Predicted next UID.
    * OK [HIGHESTMODSEQ 22748]
    a002 OK [READ-WRITE] [Gmail]/Sent Mail selected. (Success)

    "[Gmail]/Spam"
    SELECT response: * FLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing)
    * OK [PERMANENTFLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing \*)] Flags permitted.
    * OK [UIDVALIDITY 3] UIDs valid.
    * 1 EXISTS
    * 0 RECENT
    * OK [UIDNEXT 3] Predicted next UID.
    * OK [HIGHESTMODSEQ 22748]
    a002 OK [READ-WRITE] [Gmail]/Spam selected. (Success)

    "[Gmail]/Starred"
    SELECT response: * FLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing)
    * OK [PERMANENTFLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing \*)] Flags permitted.
    * OK [UIDVALIDITY 4] UIDs valid.
    * 0 EXISTS
    * 0 RECENT
    * OK [UIDNEXT 1] Predicted next UID.
    * OK [HIGHESTMODSEQ 22748]
    a002 OK [READ-WRITE] [Gmail]/Starred selected. (Success)

    "[Gmail]/Trash"
    SELECT response: * FLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing)
    * OK [PERMANENTFLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing \*)] Flags permitted.
    * OK [UIDVALIDITY 2] UIDs valid.
    * 0 EXISTS
    * 0 RECENT
    * OK [UIDNEXT 1] Predicted next UID.
    * OK [HIGHESTMODSEQ 22748]
    a002 OK [READ-WRITE] [Gmail]/Trash selected. (Success)

    Logout Successfully!

    Disconnected...

'''


'''
    INBOX
    EXAMINE response: * FLAGS (\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing)
    * OK [PERMANENTFLAGS ()] Flags permitted.
    * OK [UIDVALIDITY 1] UIDs valid.
    * 65 EXISTS
    * 0 RECENT
    * OK [UIDNEXT 66] Predicted next UID.
    * OK [HIGHESTMODSEQ 24096]
    a004 OK [READ-ONLY] INBOX selected. (Success)

    FETCH response:
    * 53 FETCH (FLAGS (\Seen) BODY[HEADER.FIELDS (DATE FROM)] {87}
    Date: Thu, 08 Jul 2021 10:40:14 +0000
    From: Rathina from Crio.Do <rathina@crio.in>

    )
    * 54 FETCH (FLAGS (\Seen) BODY[HEADER.FIELDS (DATE FROM)] {87}
    Date: Fri, 09 Jul 2021 04:35:08 +0000
    From: Rathina from Crio.Do <rathina@crio.in>

    )
    * 55 FETCH (FLAGS (\Seen) BODY[HEADER.FIELDS (DATE FROM)] {87}
    Date: Fri, 09 Jul 2021 04:39:06 +0000
    From: Rathina from Crio.Do <rathina@crio.in>

    )
    * 56 FETCH (FLAGS (\Seen) BODY[HEADER.FIELDS (DATE Fa225 OK Success
    Logout Successfully!
'''