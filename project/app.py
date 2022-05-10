import os
import time
import pandas as pd #pip install
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from flask import Flask, flash
from flask import render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy #pip install
from flask_wtf import FlaskForm #pip install
from flask_login import LoginManager, UserMixin #pip install
from flask_login import current_user, login_user, login_required, logout_user
from lib.crime_scores import generate_url_and_scores
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_mail import Message, Mail



basedir = os.path.abspath(os.path.dirname(__file__))


sql_connection_string = os.environ['SQL_STRING']
API_KEY = os.environ['API_KEY']

class Config():
    """Conect to sway db"""
    SECRET_KEY=os.urandom(24)
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'sway.db')
    SQLALCHEMY_DATABASE_URI = sql_connection_string
    SQLALCHEMY_TRACK_MODIFICATIONS = True # flask-login uses sessions which require a secret Key
    SQLALCHEMY_POOL_SIZE = 1
    SQLALCHEMY_MAX_OVERFLOW = 0

# Initialization
# Create an application instance (an object of class Flask)  which handles all requests.
app = Flask(__name__)
app.config.from_object(Config)

# login_manager needs to be initiated before running the app
login_manager = LoginManager()
login_manager.init_app(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
mail = Mail(app)

db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    """User fill credentials information"""
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(80), unique=False, nullable=False)
    lastname = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    __table_args__ = {'schema':'sway_g4'}

    def __init__(self, firstname, lastname, email, password):
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        """generate password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """compare password"""
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

class RegisterTime(db.Model):
    """Registration time information"""
    id = db.Column(db.Integer, primary_key=True)
    register_time = db.Column(db.Integer) ## Epoch Time
    email = db.Column(db.String(80)) ## User who registered
    __table_args__ = {'schema':'sway_g4'}

    def __init__(self, email):
        self.email = email
        self.register_time = time.time()

class LoginTime(db.Model):
    """Login Time Information"""
    id = db.Column(db.Integer, primary_key=True)
    login_time = db.Column(db.Integer) ## Epoch Time
    email = db.Column(db.String(80)) ## User who registered
    __table_args__ = {'schema':'sway_g4'}

    def __init__(self, email):
        self.email = email
        self.login_time = time.time()


db.create_all()
db.session.commit()

class RegistrationForm(FlaskForm):
    """Registration form credentials"""
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')

class LogInForm(FlaskForm):
    """Login Form credentials"""
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ScoreForm(FlaskForm):
    """Source Destination feed"""
    Source = StringField('Source', validators=[DataRequired()])
    Destination = StringField('Destination', validators=[DataRequired()])
    submit = SubmitField('Submit')


class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(),
                                     EqualTo('password')])
    submit = SubmitField('Reset Password')

# user_loader :
# This callback is used to reload the user object
# from the user ID stored in the session.
@login_manager.user_loader
def load_user(id):
    """get user id"""
    return User.query.get(int(id))

@app.route('/register', methods=('GET', 'POST'))
def register():
    """Validate Regitration credentials requirement.Flag if already present otherwise store."""
    registration_form = RegistrationForm()
    if registration_form.validate_on_submit():
        firstname = registration_form.firstname.data
        lastname = registration_form.lastname.data
        password = registration_form.password.data
        email = registration_form.email.data

        user_count = User.query.filter_by(email=email).count()

        if user_count > 0:
            flash('Error - Existing email : ' + email)
        else:
            user = User(firstname,lastname, email, password)
            regtime = RegisterTime(email)
            db.session.add(user)
            db.session.add(regtime)
            db.session.commit()
            flash('Thanks for registering!')
            return redirect('/')
    return render_template('register.html', registration_form=registration_form)

@app.route('/', methods=('GET', 'POST'))
def login():
    """Compare with already present db user credentials.Flag if not there."""
    if current_user.is_authenticated:
        return redirect(url_for('maps'))
    login_form = LogInForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        # Look for it in the database.
        user = User.query.filter_by(email=email).first()

        # Login and validate the user.
        if user is not None and user.check_password(password):
            login_user(user)
            logtime = LoginTime(email)
            db.session.add(user)
            db.session.add(logtime)
            db.session.commit()
            return redirect(url_for('maps'))
        flash('Invalid username and password combination!')
    return render_template('login.html',login_form=login_form)

@app.route('/logout')
@login_required

def logout():
    """Logout user"""
    logout_user()
    return redirect('/')

@app.errorhandler(401)
def re_route(e):
    """reroute on error."""
    return redirect('/')

############## USER HANDLING FINISHED. DO NOT TOUCH ANYTHING ABOVE THIS #############

@app.route('/maps', methods=('GET', 'POST'))
@login_required
def maps():
    """take path scores for source destination.Show on maps."""
    color = ['red','orange','green']
    srt_full = [((0,'NULL'),'red'),((0,'NULL'),'orange'),((0,'NULL'),'green')]
    btn = 'no_button'
    api_key = API_KEY
    scoreform = ScoreForm()
    if scoreform.validate_on_submit():
        start = scoreform.Source.data
        end = scoreform.Destination.data
        scores, text = generate_url_and_scores(start,end)
        order = []
        count = 0
        for score,text in zip(scores,text):
            order.append((count,score,text))
            count += 1
        srt = sorted(order, key=lambda x: x[1],reverse=True)
        srt_full = sorted(list(zip(srt,color)), key=lambda x:x[0][0])
        color = list(pd.DataFrame(srt_full).iloc[:,1].values)
        btn = 'button'
    return render_template('maps.html',color = color,scoreform=scoreform,srt_full=sorted(srt_full,key = lambda x:x[0][1]),btn=btn,value=api_key)

@app.route('/about.html')
def about():
    """Move to about page."""
    return render_template('about.html')


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@app.route("/forget_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    reset_request_form = RequestResetForm()
    if reset_request_form.validate_on_submit():
        user = User.query.filter_by(email=reset_request_form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', form=reset_request_form)

@app.route("/forget_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password_hash = generate_password_hash(form.password.data)#.decode('utf-8')
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', form=form)

@app.route('/feedback')
def feedback():
    """Move to feedback page."""
    return render_template('feedback.html')

@app.route('/subscribe')
@login_required
def subscribe():
    """Move to subscribe page."""
    return render_template('subscribe.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
