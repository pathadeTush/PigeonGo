from flask import Flask, render_template, redirect, url_for, request, session, flash
from forms import LoginForm
from IMAP.main import IMAP
from SMTP.main import SMTP

app = Flask(__name__)
app.config['SECRET_KEY'] = '0d44fd179c0a3d8bc9d053f710f9ac529ede4758'

@app.route('/')
@app.route('/home')
def home():
   return render_template('home.html', title='Home')

imap_client = None
   
@app.route('/login', methods=['GET', 'POST'])
def login():
   if 'loggedin' in session and session['loggedin']:
      flash('Already logged in', 'warning')
      return redirect('menu')
   form = LoginForm()
   if request.method == 'POST' and form.validate_on_submit():
      email = form.email.data
      password = form.password.data
      session['email'] = email
      session['password'] = password
      try:
         global imap_client
         imap_client = IMAP(email, password)
      except Exception:
         flash('Invalid email id or password! Try again', 'danger')
         return redirect('login')
      session['loggedin'] = True
      flash('Logged in successfully!', 'success')
      return redirect('menu')
   return render_template('login.html', title='login', form=form)

@app.route('/menu')
def menu():
   if 'loggedin' not in session:
      flash('Not logged in', 'warning')
      return redirect('login')
   print(imap_client)
   return render_template('menu.html', title='menu')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
   if 'loggedin' not in session:
      flash('Not logged in', 'warning')
      return redirect('login')
   try:
      imap_client.Logout()
   except Exception:
      flash('Logout failed!', 'warning')
      return redirect('menu')
   session.clear()
   flash('logout successfully!', 'success')
   return redirect('login')

if __name__ == '__main__':
   app.run(debug=True)