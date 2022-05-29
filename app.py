from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from forms import LoginForm, LoadMoreMailForm, DownloadAttachmentForm, WriteMailForm
from werkzeug.utils import secure_filename
from IMAP.main import IMAP
from SMTP.main import SMTP
import os

class User():
   def __init__(self, imap_client=None, smtp_client=None):
      print("\n\t===== User instantiated ====")
      self.imap_client = imap_client
      self.smtp_client = smtp_client
   def load_user(self, client='imap'):
      if 'email' not in session or 'password' not in session:
         # raise Exception('Login Credientials not found in session')
         flash('Login Credientials not found in session', 'alert-danger')
         return redirect('login')
      email = session['email']
      password = session['password']
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


def verify_login(client = 'imap'):
   if 'loggedin' not in session:
      flash('Not logged in', 'alert-danger')
      return redirect('login')
   if not user.is_active(client):
      print(f'logging again for {client} client')
      user.load_user(client)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('IMAP_SMTP_KEY')
user = User()

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
      session['password'] = password
      session['loggedin'] = True
      flash('Logged in successfully!', 'alert-success')
      return redirect(url_for('menu'))
   return render_template('login.html', title='login', form=form)

@app.route('/menu')
def menu():
   res = verify_login()
   if(res):
      return res
   return render_template('menu.html', title='menu')

@app.route('/read_mails')
def read_mails():
   res = verify_login()
   if(res):
      return res
   try:
      user.imap_client.Get_All_MailBoxes()
   except Exception as e:
      res = verify_login()
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
   res = verify_login()
   if(res):
      return res
   prev_mailbox = mailbox
   mailbox = mailbox.replace('<', '[').replace('>', ']').replace('-', ' ').replace('$', '/')
   if not was_active:
      try:
         user.imap_client.Get_All_MailBoxes()
      except Exception as e:
         res = verify_login()
         if(res):
            return res
         flash(f"error occurred! - {e} - Try again...", "alert-danger")
         return redirect(url_for('read_mails'))

   try:
      user.imap_client.Select(mailbox)
      total_mails = user.imap_client.total_mails
   except Exception as e:
      res = verify_login()
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
         res = verify_login()
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
            res = verify_login()
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
   res = verify_login()
   if(res):
      return res
   if not was_active:
      try:
         user.imap_client.Get_All_MailBoxes()
      except Exception as e:
         res = verify_login()
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
      res = verify_login()
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
         res = verify_login()
         if(res):
            return res
         flash(f'Downloads failed! - {e} - Try again', 'alert-danger')
         return redirect(url_for('mail', mailbox=prev_mailbox, index=index))
      flash(f'Attachment downloaded successfully to {download_path}!', 'alert-success')
      return redirect(url_for('mail', mailbox=prev_mailbox, index=index))
   return render_template('mail.html', mailbox=prev_mailbox, header=header, data=data, form=form)

@app.route('/write_mail', methods=['GET', 'POST'])
def write_mail():
   res = verify_login()
   if(res):
      return res
   res = verify_login(client='smtp')
   if(res):
      return res
   form = WriteMailForm()
   if request.method == 'POST' and form.validate_on_submit():
      TO_email = form.TO_email.data
      Subject = form.Subject.data
      Body = form.Body.data
      attachments = form.attachment.data
      Attachments = []
      for attachment in attachments.split(','):
         if(len(attachment.strip()) == 0):
            continue 
         Attachments.append(attachment.strip())
      # for attachment in attachments:
      #    filename = secure_filename(attachment.filename)
      #    mimetype = attachment.mimetype
      #    Attachments.append({'filename':filename, 'mimetype':mimetype})
      # print(f'attachments: {Attachments}')
      try:
         user.smtp_client.send_email(TO_email, Subject, Body, Attachment = Attachments)
      except Exception as e:
         res = verify_login()
         if(res):
            return res
         flash(f'Something went wrong! Mail not sent. - {e} - Try Again!', 'alert-danger')
         return redirect(url_for('write_mail'))
      flash('Mail sent successfully!', 'alert-success')
      return redirect(url_for('mail_success'))
   return render_template('write_mail.html', title='Write Mail', form=form)

@app.route('/mail_success')
def mail_success():
   res = verify_login()
   if(res):
      return res
   res = verify_login(client='smtp')
   if(res):
      return res
   return render_template('mail_success.html', title='Mail Sent Success')

@app.route('/logout')
def logout():
   res = verify_login()
   if(res):
      return res
   res = verify_login(client='smtp')
   if(res):
      return res
   try:
      user.imap_client.Logout()
      user.imap_client.close_connection()
      user.imap_client = None
      user.smtp_client.quit()
      user.smtp_client.close_connection()
      user.smtp_client = None
   except Exception as e:
      flash(f'Logout failed! - {e}', 'alert-warning')
      return redirect(url_for('menu'))
   session.clear()
   flash('logout successfully!', 'alert-success')
   return redirect(url_for('login'))

if __name__ == '__main__':
   app.run(debug=True)