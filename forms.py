from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, StringField
from wtforms.validators import DataRequired, Length, Email

class LoginForm(FlaskForm):
   email = StringField('Email ID', validators=[DataRequired(), Email()])
   password = PasswordField('Password', validators=[DataRequired()])
   submit = SubmitField('Login')