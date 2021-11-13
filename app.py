from flask import Flask, render_template, redirect, url_for, request, session, flash
from forms import LoginForm
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
      self.imap_client = IMAP(email, password)
   def is_active(self):
      return not(self.imap_client == None)

user = User()


def verify_login():
   if 'loggedin' not in session:
      flash('Not logged in', 'alert-danger')
      return redirect('login')
   if not user.is_active():
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

@app.route('/read_mail')
def read_mail():
   verify_login()
   user.imap_client.Get_All_MailBoxes()
   mailboxes = user.imap_client.mailboxes

   return render_template('read_mail.html', title='Read Mail', mailboxes=mailboxes)

@app.round('/open_mailbox/<mailbox>')
def open_mailbox(mailbox):
   verify_login()
   

@app.route('/logout', methods=['GET', 'POST'])
def logout():
   verify_login()
   try:
      user.imap_client.Logout()
      user.imap_client = None
   except Exception:
      flash('Logout failed!', 'alert-warning')
      return redirect('menu')
   session.clear()
   flash('logout successfully!', 'alert-success')
   return redirect('login')

if __name__ == '__main__':
   app.run(debug=True)