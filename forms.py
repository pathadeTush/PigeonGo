from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import PasswordField, SubmitField, StringField, TextAreaField, MultipleFileField
from wtforms.validators import DataRequired, Length, Email

class LoginForm(FlaskForm):
   email = StringField('Email ID', validators=[DataRequired(), Email()])
   password = PasswordField('Password', validators=[DataRequired()])
   submit = SubmitField('Login')

class WriteMailForm(FlaskForm):
   TO_email = StringField('To', validators=[DataRequired(), Email()], render_kw={"placeholder": "put email address (valid) of recipent"})
   Subject = StringField('Subject', render_kw={"placeholder": "Give subject to your mail!"})
   Body = TextAreaField('Body', render_kw={"placeholder": "Type text here..."})
   attachment = MultipleFileField('attachments', render_kw={"placeholder": "add files..."})
   submit = SubmitField('Send Mail')
