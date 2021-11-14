from flask import Flask, render_template, redirect, url_for, request, session, flash
from forms import LoginForm, LoadMoreMailForm, DownloadAttachmentForm
from IMAP.main import IMAP
from SMTP.main import SMTP

class User():
   def __init__(self, imap_client=None, smtp_client=None):
      self.imap_client = imap_client
      self.smtp_client = smtp_client
   def load_user(self):
      if 'email' not in session or 'password' not in session:
         raise Exception('Login Credientials not found in session')
      email = session['email']
      password = session['password']
      try:
         self.imap_client = IMAP(email, password)
      except Exception as e:
         flash(f'{e.message}')
   def is_active(self):
      return not(self.imap_client == None)

user = User()


def verify_login():
   if 'loggedin' not in session:
      flash('Not logged in', 'alert-danger')
      return redirect('login')
   if not user.is_active():
      print('logging in again')
      user.load_user()

      
app = Flask(__name__)
app.config['SECRET_KEY'] = '0d44fd179c0a3d8bc9d053f710f9ac529ede4758'

@app.route('/')
@app.route('/home')
def home():
   return render_template('home.html', title='Home')
   
@app.route('/login', methods=['GET', 'POST'])
def login():
   if 'loggedin' in session and session['loggedin']:
      if not user.is_active():
         user.load_user()
      flash('Already logged in', 'alert-warning')
      return redirect('menu')
   form = LoginForm()
   if request.method == 'POST' and form.validate_on_submit():
      email = form.email.data
      password = form.password.data
      try:
         user.imap_client = IMAP(email, password)
      except Exception:
         flash('Invalid email id or password! Try again', 'alert-danger')
         return redirect('login')
      session['email'] = email
      session['password'] = password
      session['loggedin'] = True
      flash('Logged in successfully!', 'alert-success')
      return redirect('menu')
   return render_template('login.html', title='login', form=form)

@app.route('/menu')
def menu():
   verify_login()
   return render_template('menu.html', title='menu')

@app.route('/read_mails')
def read_mails():
   verify_login()
   user.imap_client.Get_All_MailBoxes()
   mailboxes = []

   for mailbox in user.imap_client.mailboxes:
      mailbox = mailbox.replace('[', '<').replace(']', '>').replace(' ', '-').replace('/', '$')
      mailboxes.append(mailbox)

   return render_template('mailbox.html', title='Read Mail', mailboxes=mailboxes)

@app.route('/open_mailbox/<mailbox>', methods=['GET', 'POST'])
def open_mailbox(mailbox):
   was_authenticated = user.is_active()
   verify_login()
   prev_mailbox = mailbox
   mailbox = mailbox.replace('<', '[').replace('>', ']').replace('-', ' ').replace('$', '/')
   if not was_authenticated:
      user.imap_client.Get_All_MailBoxes()
   user.imap_client.Select(mailbox)
   total_mails = user.imap_client.total_mails
   mail_buffer = 10
   form = LoadMoreMailForm()
   headers = []
   if request.method == 'POST' and form.validate_on_submit():
      headers = user.imap_client.fetch_mail_header(1, mail_buffer)
      flash('fetched more mails!', 'alert-success')
      return redirect(url_for('open_mailbox', mailbox=prev_mailbox))
   else:
      headers = user.imap_client.headers[mailbox]
      if(len(headers) == 0):
         headers = user.imap_client.fetch_mail_header(1, mail_buffer)
   if(len(headers) >= total_mails):
      form = ''
   return render_template('headers.html', title = f'{prev_mailbox}', headers=headers, form=form)

@app.route('/<mailbox>/<index>', methods=['GET', 'POST'])
def mail(mailbox, index):
   was_authenticated = user.is_active()
   verify_login()
   if not was_authenticated:
      user.imap_client.Get_All_MailBoxes()
   print(f'inside mail function mailbox: {mailbox}')
   prev_mailbox = mailbox
   mailbox = mailbox.replace('<', '[').replace('>', ']').replace('-', ' ').replace('$', '/')
   user.imap_client.Select(mailbox)
   index = int(index)
   header = user.imap_client.fetch_mail_header(index, 1, single=True)
   bodies = user.imap_client.fetch_body_structure(index)
   data = []
   if not bodies:
      flash(f'max index possible: {user.imap_client.total_mails}', 'alert-warning')
   else:
      data = user.imap_client.extract_text_html(index, bodies)
      if data['html']:
         file = open('static/html.html', 'w+')
         file.write(data['html'])
         file.close()
   form = DownloadAttachmentForm()
   if request.method == 'POST' and form.validate_on_submit():
      try:
         download_path = user.imap_client.download_attachment(index, bodies)
      except Exception:
         flash('Downloads failed! Try again', 'alert-danger')
         return redirect(url_for('mail', mailbox=prev_mailbox, index=index))
      flash(f'Attachment downloaded successfully to {download_path}!', 'alert-success')
      return redirect(url_for('mail', mailbox=prev_mailbox, index=index))
   return render_template('mail.html', mailbox=prev_mailbox, header=header, data=data, form=form)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
   verify_login()
   try:
      user.imap_client.Logout()
      user.imap_client.close_connection()
      user.imap_client = None
   except Exception:
      flash('Logout failed!', 'alert-warning')
      return redirect('menu')
   session.clear()
   flash('logout successfully!', 'alert-success')
   return redirect('login')

if __name__ == '__main__':
   app.run(debug=True)