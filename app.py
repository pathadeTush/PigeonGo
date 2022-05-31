from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from forms import LoginForm, LoadMoreMailForm, DownloadAttachmentForm, WriteMailForm
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
from dotenv import load_dotenv, dotenv_values
import os

class User():
   def __init__(self, imap_client=None, smtp_client=None):
      # print("\n\t===== User instantiated ====")
      self.imap_client = imap_client
      self.smtp_client = smtp_client
   def load_client(self, client='imap'):
      if 'email' not in session or 'password' not in session:
         # raise Exception('Login Credientials not found in session')
         flash('Login Credientials not found in session', 'alert-danger')
         return redirect('login')
      email = session['email']
      password = session['password']
      password = fernet.decrypt(password).decode()
      try:
         if client == 'imap':
            self.imap_client = IMAP(email, password)
         else:
            self.smtp_client = SMTP(email, password)
      except Exception as e:
         flash(f'Error occured - {e}', 'alert-danger')
   def is_active(self, client='imap'):
      if client == 'imap':
         return not(self.imap_client == None)
      else:
         return not(self.smtp_client == None)


def verify_client(client = 'imap'):
   if 'loggedin' not in session:
      flash('Not logged in', 'alert-danger')
      return redirect(url_for('login'))
   if not user.is_active(client):
      # print(f'logging again for {client} client')
      user.load_client(client)
   elif client == 'smtp' and user.smtp_client.pending:
      user.smtp_client.close_connection()
      user.load_client(client)

load_dotenv()
env_vars = dotenv_values(".env")
try:
   FERNET_KEY = bytes(env_vars['FERNET_KEY'], 'utf-8')
except:
   FERNET_KEY = os.environ.get('FERNET_KEY')
fernet = Fernet(FERNET_KEY)

app = Flask(__name__)
try:
   app.config['SECRET_KEY'] = env_vars['SECRET_KEY']
except:
   app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
attachment_dir = os.path.join(os.getcwd(), 'attachments')
if not os.path.isdir(attachment_dir):
   os.mkdir(attachment_dir)
app.config['ATTACHMENT_DIR'] = attachment_dir

user = User()

@app.route('/')
@app.route('/home')
def home():
   return render_template('home.html', title='Home')
   
@app.route('/login', methods=['GET', 'POST'])
def login():
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
         user.imap_client = IMAP(email, password)
      except Exception as e:
         flash(f'error occurred - {e}', 'alert-danger')
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
   res = verify_client()
   if(res):
      return res
   try:
      user.imap_client.Get_All_MailBoxes()
   except Exception as e:
      res = verify_client()
      if(res):
         return res
      flash(f"error occurred! - {e} - Trying again...", "alert-danger")
      return redirect('menu')

   mailboxes = []

   for mailbox in user.imap_client.mailboxes:
      mailbox = mailbox.replace('[', '<').replace(']', '>').replace(' ', '-').replace('/', '$')
      mailboxes.append(mailbox)

   return render_template('mailbox.html', title='Read Mail', mailboxes=mailboxes)

@app.route('/open_mailbox/<mailbox>', methods=['GET', 'POST'])
def open_mailbox(mailbox):
   was_active = user.is_active()
   res = verify_client()
   if(res):
      return res
   prev_mailbox = mailbox
   mailbox = mailbox.replace('<', '[').replace('>', ']').replace('-', ' ').replace('$', '/')
   if not was_active:
      try:
         user.imap_client.Get_All_MailBoxes()
      except Exception as e:
         res = verify_client()
         if(res):
            return res
         flash(f"error occurred! - {e} - Try again...", "alert-danger")
         return redirect(url_for('read_mails'))

   try:
      user.imap_client.Select(mailbox)
      total_mails = user.imap_client.total_mails
   except Exception as e:
      res = verify_client()
      if(res):
         return res
      flash(f"error occurred! - {e} - Try again...", "alert-danger")
      return redirect(url_for('read_mails'))
   mail_buffer = 10
   headers = []
   if request.method == 'POST':
      try:
         headers = user.imap_client.fetch_mail_header(1, mail_buffer)
      except Exception as e:
         res = verify_client()
         if(res):
            return res
         flash(f"error occurred! - {e} - Try again...", "alert-danger")
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
            flash(f"error occurred! - {e} - Trying again...", "alert-danger")
            return redirect(url_for('open_mailbox', mailbox=prev_mailbox))
   allFetched = False
   if(len(headers) >= total_mails):
      allFetched = True
   return render_template('headers.html', title = f'{prev_mailbox}', headers=headers, allFetched=allFetched)

@app.route('/<mailbox>/<index>', methods=['GET', 'POST'])
def mail(mailbox, index):
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
         flash(f"error occurred! - {e} - Try refereshing page...", "alert-danger")
         return redirect(url_for('open_mailbox', mailbox=prev_mailbox))

   prev_mailbox = mailbox
   mailbox = mailbox.replace('<', '[').replace('>', ']').replace('-', ' ').replace('$', '/')

   try:
      user.imap_client.Select(mailbox)
      index = int(index)
      header = user.imap_client.fetch_mail_header(index, 1, single=True)
      bodies = user.imap_client.fetch_body_structure(index)
   except Exception as e:
      res = verify_client()
      if(res):
         return res
      flash(f"error occurred! - {e} Try again...", "alert-danger")
      return redirect(url_for('open_mailbox', mailbox=prev_mailbox))

   data = []
   if not bodies:
      flash(f'max index possible: {user.imap_client.total_mails}', 'alert-warning')
   else:
      try:
         data = user.imap_client.extract_text_html(index, bodies)
      except:
         flash('error occured in parsing text! Try again...', 'alert-danger')
         return redirect(url_for('open_mailbox', mailbox=prev_mailbox))
      if data['html']:
         file = open('static/html.html', 'w+')
         file.write(data['html'])
         file.close()
   form = DownloadAttachmentForm()
   if request.method == 'POST' and form.validate_on_submit():
      try:
         download_path = user.imap_client.download_attachment(index, bodies)
      except Exception as e:
         res = verify_client()
         if(res):
            return res
         flash(f'Downloads failed! - {e} - Try again', 'alert-danger')
         return redirect(url_for('mail', mailbox=prev_mailbox, index=index))
      flash(f'Attachment downloaded successfully to {download_path}!', 'alert-success')
      return redirect(url_for('mail', mailbox=prev_mailbox, index=index))
   return render_template('mail.html', mailbox=prev_mailbox, header=header, data=data, form=form)

@app.route('/write_mail', methods=['GET', 'POST'])
def write_mail():
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
      if not(len(attachments) == 1 and attachments[0].filename == ''):
         for attachment in attachments:
            filename = secure_filename(attachment.filename)
            mimetype = attachment.mimetype
            Attachments.append({'filename':filename, 'mimetype':mimetype})
            try:
               attachment.save(os.path.join(attachment_dir, filename))
            except:
               pass
               flash('invalid file', 'alert-warning')
               return redirect(url_for('write_mail'))
      # print(f'attachments: {Attachments}')
      try:
         user.smtp_client.send_email(TO_email, Subject, Body, Attachment = Attachments)
      except Exception as e:
         empty_folder(attachment_dir)
         res = verify_client('smtp')
         if(res):
            return res
         flash(f'Something went wrong! Mail not sent. - {e} - Try Again!', 'alert-danger')
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
   try:
      if user.is_active('imap'):
         user.imap_client.close_connection()
      if user.is_active('smtp'):
         user.smtp_client.close_connection()
   except:
      pass
   user.imap_client = None
   user.smtp_client = None
   session.clear()
   flash('logout successfully!', 'alert-success')
   return redirect(url_for('login'))

def empty_folder(folder):
   for file in os.listdir(folder):
      os.remove(os.path.join(folder, file))


if __name__ == '__main__':
   from IMAP.main import IMAP
   from SMTP.main import SMTP
   app.run(debug=False)