from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify, send_from_directory
from forms import LoginForm, WriteMailForm
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
from dotenv import load_dotenv, dotenv_values
from IMAP.main import IMAP
from SMTP.main import SMTP
import os

load_dotenv()
env_vars = dotenv_values(".env")
app = Flask(__name__)
try:
   FERNET_KEY = bytes(env_vars['FERNET_KEY'], 'utf-8')
   app.config['SECRET_KEY'] = env_vars['SECRET_KEY']
except:
   FERNET_KEY = os.environ.get('FERNET_KEY')
   app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
fernet = Fernet(FERNET_KEY)

attachment_dir = os.path.join(os.getcwd(), 'attachments')
if not os.path.isdir(attachment_dir):
   os.mkdir(attachment_dir)

app.config['DOWNLOADS'] = 'downloads'

def something_went_wrong(e):
   flash('something went wrong. Try again or refresh the page...', 'alert-danger')
   if(app.config['user'].debug):
      flash(f'{e}', 'alert-danger')

class User():
   def __init__(self, imap_client=None, smtp_client=None, debug=False):
      self.imap_client = imap_client
      self.smtp_client = smtp_client
      self.debug = debug
   def load_client(self, client='imap'):
      if 'email' not in session or 'password' not in session:
         flash('Login Credientials not found in session', 'alert-danger')
         return redirect('login')
      email = session['email']
      password = session['password']
      password = fernet.decrypt(password).decode()
      try:
         if client == 'imap':
            if self.imap_client:
               self.imap_client.create_socket()
            else:
               self.imap_client = IMAP(email, password, self.debug)
         else:
            if self.smtp_client:
               self.smtp_client.create_socket()
            else:
               self.smtp_client = SMTP(email, password, self.debug)
      except Exception as e:
         something_went_wrong(e)
   def is_active(self, client='imap'):
      if client == 'imap':
         return not(self.imap_client == None)
      else:
         return not(self.smtp_client == None)


def verify_client(client = 'imap'):
   if 'loggedin' not in session:
      flash('Not logged in', 'alert-danger')
      return redirect(url_for('login'))
   user = app.config['user']
   if not user.is_active(client):
      user.load_client(client)
   elif client == 'smtp' and user.smtp_client.pending:
      print('pending.... closing smtp socket')
      user.smtp_client.pending = False
      user.smtp_client.close_connection()
      user.load_client(client)
   elif client == 'imap' and user.imap_client.pending:
      print('pending.... closing imap socket')
      user.imap_client.pending = False
      user.imap_client.close_connection()
      user.load_client(client)

app.config['user'] = User(debug=False)

@app.route('/')
@app.route('/home')
def home():
   return render_template('home.html', title='Home')
   
@app.route('/login', methods=['GET', 'POST'])
def login():
   user = app.config['user']
   if 'loggedin' in session and session['loggedin']:
      if not user.is_active():
         user.load_client()
      flash('Already logged in', 'alert-warning')
      return redirect(url_for('menu'))
   form = LoginForm()
   if request.method == 'POST' and form.validate_on_submit():
      email = form.email.data
      password = form.password.data
      try:
         user.imap_client = IMAP(email, password, user.debug)
      except Exception as e:
         something_went_wrong(e)
         return redirect(url_for('login'))
      session['email'] = email
      password = fernet.encrypt(password.encode())
      session['password'] = password
      session['loggedin'] = True
      flash('Logged in successfully!', 'alert-success')
      return redirect(url_for('menu'))
   return render_template('login.html', title='login', form=form)

@app.route('/menu')
def menu():
   res = verify_client()
   if(res):
      return res
   return render_template('menu.html', title='menu')

@app.route('/read_mails')
def read_mails():
   user = app.config['user']
   res = verify_client()
   if(res):
      return res
   try:
      user.imap_client.Get_All_MailBoxes()
   except Exception as e:
      res = verify_client()
      if(res):
         return res
      something_went_wrong(e)
      return redirect('menu')

   mailboxes = []

   for mailbox in user.imap_client.mailboxes:
      mailbox = mailbox.replace('[', '<').replace(']', '>').replace(' ', '-').replace('/', '$')
      mailboxes.append(mailbox)

   return render_template('mailbox.html', title='Read Mail', mailboxes=mailboxes)

@app.route('/open_mailbox/<mailbox>', methods=['GET', 'POST'])
def open_mailbox(mailbox):
   user = app.config['user']
   res = verify_client()
   if(res):
      return res
   prev_mailbox = mailbox
   mailbox = mailbox.replace('<', '[').replace('>', ']').replace('-', ' ').replace('$', '/')
   try:
      user.imap_client.Get_All_MailBoxes()
   except Exception as e:
      res = verify_client()
      if(res):
         return res
      something_went_wrong(e)
      return redirect(url_for('read_mails'))

   try:
      user.imap_client.Select(mailbox)
      total_mails = user.imap_client.total_mails
   except Exception as e:
      res = verify_client()
      if(res):
         return res
      something_went_wrong(e)
      return redirect(url_for('read_mails'))
   mail_buffer = 10
   headers = []
   if request.method == 'POST' or total_mails == 0:
      try:
         headers = user.imap_client.fetch_mail_header(1, mail_buffer)
      except Exception as e:
         res = verify_client()
         if(res):
            return res
         something_went_wrong(e)
         return redirect(url_for('open_mailbox', mailbox=prev_mailbox))
      return jsonify({"headers": headers})
   else:
      headers = user.imap_client.headers[mailbox]
      if(len(headers) == 0):
         try:
            headers = user.imap_client.fetch_mail_header(1, mail_buffer)
         except Exception as e:
            res = verify_client()
            if(res):
               return res
            something_went_wrong(e)
            return redirect(url_for('open_mailbox', mailbox=prev_mailbox))
   allFetched = False
   if(len(headers) >= total_mails):
      allFetched = True
   return render_template('headers.html', title = f'{prev_mailbox}', headers=headers, allFetched=allFetched)

@app.route('/<mailbox>/<index>', methods=['GET', 'POST'])
def mail(mailbox, index):
   user = app.config['user']
   was_active = user.is_active()
   res = verify_client()
   if(res):
      return res
   if not was_active:
      try:
         user.imap_client.Get_All_MailBoxes()
      except Exception as e:
         res = verify_client()
         if(res):
            return res
         something_went_wrong(e)
         return redirect(url_for('open_mailbox', mailbox=prev_mailbox))

   prev_mailbox = mailbox
   mailbox = mailbox.replace('<', '[').replace('>', ']').replace('-', ' ').replace('$', '/')

   try:
      user.imap_client.Select(mailbox)
      index = int(index)
      header = user.imap_client.fetch_mail_header(index, 1, single=True)
      bodies = user.imap_client.fetch_body_structure(index)
      # print(bodies)
   except Exception as e:
      res = verify_client()
      if(res):
         return res
      something_went_wrong(e)
      return redirect(url_for('open_mailbox', mailbox=prev_mailbox))

   data = []
   if not bodies:
      flash(f'max index possible: {user.imap_client.total_mails}', 'alert-warning')
   else:
      try:
         data = user.imap_client.extract_text_html(index, bodies)
      except Exception as e:
         something_went_wrong(e)
         return redirect(url_for('open_mailbox', mailbox=prev_mailbox))
      if data['html']:
         downloads = os.path.join(os.getcwd(), app.config['DOWNLOADS'])
         filepath = os.path.join(downloads, 'html.html')
         file = open(f'{filepath}', 'w+')
         file.write(data['html'])
         file.close()
   if request.method == 'POST':
      try:
         file_saved = user.imap_client.download_attachment(index, bodies)
      except Exception as e:
         res = verify_client()
         if(res):
            return res
         something_went_wrong(e)
         return redirect(url_for('mail', mailbox=prev_mailbox, index=index))
      return jsonify({'file_saved': file_saved})
   return render_template('mail.html', mailbox=prev_mailbox, header=header, data=data)

@app.route('/write_mail', methods=['GET', 'POST'])
def write_mail():
   user = app.config['user']
   res = verify_client('smtp')
   if(res):
      return res
   form = WriteMailForm()
   if request.method == 'POST' and form.validate_on_submit():
      TO_email = form.TO_email.data
      Subject = form.Subject.data
      Body = form.Body.data
      attachments = form.attachment.data
      # print(attachments, len(attachments))
      Attachments = []
      attach = {}
      if not(len(attachments) == 1 and attachments[0].filename == ''):
         for attachment in attachments:
            filename = secure_filename(attachment.filename)
            mimetype = attachment.mimetype
            Attachments.append({'filename':filename, 'mimetype':mimetype})
            try:
               attachment.save(os.path.join(attachment_dir, filename))
            except:
               flash('invalid file', 'alert-warning')
               return redirect(url_for('write_mail'))
         attach = {'attachment_dir': attachment_dir, 'Attachments': Attachments}
      # print(f'attachments: {Attachments}')
      try:
         user.smtp_client.send_email(TO_email, Subject, Body, Attachment = attach)
      except Exception as e:
         empty_folder(attachment_dir)
         res = verify_client('smtp')
         if(res):
            return res
         something_went_wrong(e)
         return redirect(url_for('write_mail'))
      empty_folder(attachment_dir)
      flash('Mail sent successfully!', 'alert-success')
      return redirect(url_for('mail_success'))
   return render_template('write_mail.html', title='Write Mail', form=form)

@app.route('/mail_success')
def mail_success():
   res = verify_client('smtp')
   if(res):
      return res
   return render_template('mail_success.html', title='Mail Sent Success')

@app.route('/logout')
def logout():
   if 'loggedin' not in session:
      flash('Not logged in', 'alert-danger')
      return redirect(url_for('login'))
   user = app.config['user']
   if user.is_active('imap'):
      try:
         user.imap_client.Logout()
      except:
         pass
      user.imap_client.close_connection()
   if user.is_active('smtp'):
      try:
         user.smtp_client.quit()
      except:
         pass
      user.smtp_client.close_connection()
   session.clear()
   del user
   empty_folder(os.path.join(os.getcwd(), app.config['DOWNLOADS']))
   flash('logout successfully!', 'alert-success')
   return redirect(url_for('login'))

@app.route('/downloads/<path:filename>', methods=['GET', 'POST'])
def download(filename):
   downloads = os.path.join(os.getcwd(), app.config['DOWNLOADS'])
   return send_from_directory(directory=downloads, path=filename)

def empty_folder(folder):
   for file in os.listdir(folder):
      os.remove(os.path.join(folder, file))

if __name__ == '__main__':
   app.run(debug=False)