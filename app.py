import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, FloatField, HiddenField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
import random

# Load environment variables
load_dotenv()

# Setup Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///users.db')  # Use environment variable or default to SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Custom ID generator function
def generate_quote_id():
    while True:
        new_id = random.randint(100000, 999999)
        if not QuoteRequest.query.get(new_id):
            return new_id

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.String(25), primary_key=True)
    password_hash = db.Column(db.String(128), nullable=False)

# QuoteRequest model
class QuoteRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True, default=generate_quote_id)
    user_id = db.Column(db.String(25), db.ForeignKey('user.id'), nullable=False)
    business_type = db.Column(db.String(100), nullable=False)
    requirements = db.Column(db.Text, nullable=False)
    contact_info = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # 'Pending', 'Accepted', 'Denied'
    quote_price = db.Column(db.Float)
    user = db.relationship('User', backref=db.backref('quote_requests', lazy=True))

# Update model
class Update(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.String(20), nullable=False)

# ContactMessage model
class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Flask-Login user loader
@login_manager.user_loader
def load_user(username):
    logger.debug(f'Loading user with username: {username}')
    return User.query.get(username)

# Forms
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=35)])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class QuoteRequestForm(FlaskForm):
    business_type = StringField('Business Type', validators=[DataRequired()])
    requirements = TextAreaField('Requirements', validators=[DataRequired()])
    contact_info = StringField('Contact Info', validators=[DataRequired()])
    submit = SubmitField('Request Quote')

class QuoteResponseForm(FlaskForm):
    quote_id = HiddenField('Quote ID', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Pending Approval', 'Pending Approval'),
        ('Approved', 'Approved'),
        ('Denied', 'Denied'),
        ('In Progress', 'In Progress'),
        ('View Updates', 'View Updates'),
        ('Complete Awaiting Payment', 'Complete Awaiting Payment'),
        ('Complete', 'Complete')
    ], validators=[DataRequired()])
    quote_price = FloatField('Quote Price')
    submit = SubmitField('Submit Response')

class UpdateForm(FlaskForm):
    update_content = TextAreaField('Update Content', validators=[DataRequired()])
    submit = SubmitField('Add Update')

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# Routes
@app.route('/')
def home():
    logger.debug('Rendering home page')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    logger.debug('Login route accessed')
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        logger.debug(f'Login attempt for username: {username}')
        user = User.query.get(username)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            logger.debug(f'User {username} logged in successfully')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
        logger.warning(f'Invalid login attempt for username: {username}')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    logger.debug('Register route accessed')
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        logger.debug(f'Registration attempt for username: {username}')
        if User.query.get(username):
            flash('Username already exists')
            logger.warning(f'Username {username} already exists')
        else:
            new_user = User(id=username, password_hash=password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            logger.debug(f'User {username} registered and logged in successfully')
            return redirect(url_for('dashboard'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logger.debug(f'User {current_user.id} logged out')
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    request_form = QuoteRequestForm()
    response_form = QuoteResponseForm()
    update_form = UpdateForm()
    search_query = request.args.get('search_query')

    if request_form.validate_on_submit() and current_user.id != 'admin':
        new_request = QuoteRequest(
            user_id=current_user.id,
            business_type=request_form.business_type.data,
            requirements=request_form.requirements.data,
            contact_info=request_form.contact_info.data
        )
        db.session.add(new_request)
        db.session.commit()
        flash('Quote request submitted successfully', 'success')
        return redirect(url_for('dashboard'))

    if response_form.validate_on_submit() and current_user.id == 'admin':
        try:
            quote_id = int(response_form.quote_id.data)
            quote = QuoteRequest.query.get(quote_id)
            if quote:
                quote.status = response_form.status.data
                quote.quote_price = response_form.quote_price.data
                db.session.commit()
                flash('Quote response submitted successfully', 'success')
            else:
                flash('Quote not found', 'danger')
        except ValueError:
            flash('Invalid Quote ID', 'danger')
        return redirect(url_for('dashboard'))

    if update_form.validate_on_submit() and current_user.id == 'admin':
        content = update_form.update_content.data
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_update = Update(content=content, timestamp=timestamp)
        db.session.add(new_update)
        db.session.commit()
        flash('Update added successfully', 'success')
        return redirect(url_for('dashboard'))

    if current_user.id == 'admin':
        if search_query:
            quotes = QuoteRequest.query.filter_by(id=search_query).all()
        else:
            quotes = QuoteRequest.query.all()
    else:
        quotes = QuoteRequest.query.filter_by(user_id=current_user.id).all()

    return render_template('dashboard.html', quotes=quotes, request_form=request_form, response_form=response_form, update_form=update_form)


    if update_form.validate_on_submit() and current_user.id == 'admin':
        content = update_form.update_content.data
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_update = Update(content=content, timestamp=timestamp)
        db.session.add(new_update)
        db.session.commit()
        flash('Update added successfully', 'success')
        return redirect(url_for('dashboard'))

    if current_user.id == 'admin':
        quotes = QuoteRequest.query.all()
    else:
        quotes = QuoteRequest.query.filter_by(user_id=current_user.id).all()

    return render_template('dashboard.html', quotes=quotes, request_form=request_form, response_form=response_form, update_form=update_form)

@app.route('/quote_details/<int:quote_id>')
@login_required
def quote_details(quote_id):
    if current_user.id != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    quote = QuoteRequest.query.get_or_404(quote_id)
    return jsonify({
        'id': quote.id,
        'business_type': quote.business_type,
        'requirements': quote.requirements,
        'contact_info': quote.contact_info,
        'status': quote.status,
        'quote_price': quote.quote_price
    })

@app.route('/get_updates')
@login_required
def get_updates():
    updates = Update.query.order_by(Update.timestamp.desc()).all()
    updates_list = [{'content': update.content, 'timestamp': update.timestamp} for update in updates]
    return jsonify(updates_list)

@app.route('/add_update', methods=['POST'])
@login_required
def add_update():
    if current_user.id == 'admin':
        content = request.form.get('update_content')
        if content:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_update = Update(content=content, timestamp=timestamp)
            db.session.add(new_update)
            db.session.commit()
            return jsonify({'success': 'Update added successfully'})
    return jsonify({'error': 'Failed to add update'})

@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')

    if not name or not email or not message:
        flash('All fields are required!', 'danger')
        return redirect(url_for('home'))

    new_message = ContactMessage(name=name, email=email, message=message)
    db.session.add(new_message)
    db.session.commit()

    flash('Message received successfully!', 'success')
    return redirect(url_for('success'))

@app.route('/success')
def success():
    return render_template('success.html')



@app.route('/admin/messages')
@login_required
def view_messages():
    if current_user.id != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))

    messages = ContactMessage.query.order_by(ContactMessage.timestamp.desc()).all()
    return render_template('admin_messages.html', messages=messages)

@app.route('/add_review', methods=['POST'])
def add_review():
    data = request.get_json()
    username = data.get('username')
    content = data.get('content')
    
    if username and content:
        new_review = Review(username=username, content=content)
        db.session.add(new_review)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/get_reviews', methods=['GET'])
def get_reviews():
    reviews = Review.query.order_by(Review.timestamp.desc()).all()
    return jsonify([{'username': review.username, 'content': review.content} for review in reviews])

@app.route('/site_map')
def site_map():
    logger.debug('Rendering site map page')
    return render_template('sitemap.html')


# Function to create the database tables
def create_db():
    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")

if __name__ == '__main__':
    create_db()  # Create database tables if they don't exist
    app.run(host='0.0.0.0', port=10000)



