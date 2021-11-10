from flask import Flask, render_template, redirect, url_for, request, session, flash
from forms import LoginForm
from IMAP.main import IMAP
from SMTP.main import SMTP

class MAIL_SERVER:
    def __init__(self, server, port):
        self.server = server
        self.port = port

imap_mail_servers = {}
imap_mail_servers['gmail.com'] = MAIL_SERVER('imap.gmail.com', 993)
imap_mail_servers['outlook.com'] = MAIL_SERVER('outlook.office365.com', 993)
imap_mail_servers['hotmail.com'] = MAIL_SERVER('outlook.office365.com', 993)
imap_mail_servers['coep.ac.in'] = MAIL_SERVER('outlook.office365.com', 993)

app = Flask(__name__)
app.config['SECRET_KEY'] = '0d44fd179c0a3d8bc9d053f710f9ac529ede4758'

@app.route('/')
@app.route('/home')
def home():
   return render_template('home.html', title='Home')
   
@app.route('/login', methods=['GET', 'POST'])
def login():
   if 'loggedin' in session and session[loggedin]:
      flash('Already logged in', 'warning')
      return redirect('home')
   form = LoginForm()
   if request.method == 'POST' and form.validate_on_submit():
      email = form.email.data
      password = form.password.data
      session['email'] = email
      session['password'] = password
      domain = email.strip().split('@')[1].lower()
      if domain not in imap_mail_servers:
         flash('Invalid email address. Gmail and outlook services supported only', 'danger')
         return redirect('login')
      imap_client = IMAP(imap_mail_servers[domain].server, imap_mail_servers[domain].port)
      session['loggedin'] = True
      session['imap_client'] = imap_client
      return redirect('home')
   return render_template('login.html', title='login', form=form)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
   if 'loggedin' in session and session[loggedin]:
      flash('Already logged in', 'warning')
      return redirect('home')
   session.clear()
   return redirect('login')

if __name__ == '__main__':
   app.run(debug=True)