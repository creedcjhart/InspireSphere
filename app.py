import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-for-development')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///blog.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Upload configuration
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    profile_image = db.Column(db.String(120), default='default.jpg')
    bio = db.Column(db.Text)
    posts = db.relationship('Post', backref='author', lazy=True)
    
    @property
    def is_admin(self):
        return self.role in ['owner', 'admin']
    
    @property
    def is_owner(self):
        return self.role == 'owner'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    featured_image = db.Column(db.String(200))
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_edited = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='draft')
    images = db.relationship('PostImage', backref='post', lazy=True, cascade='all, delete-orphan')

class PostImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

def create_owner_account(username='admin', email='admin@example.com', password='admin'):
    if User.query.filter_by(role='owner').first():
        return False
    
    owner = User(
        username=username,
        email=email,
        role='owner',
        is_active=True
    )
    owner.password_hash = generate_password_hash(password)
    db.session.add(owner)
    db.session.commit()
    return True

@app.before_first_request
def initialize_database():
    db.create_all()
    # Create owner account if it doesn't exist
    if not User.query.filter_by(role='owner').first():
        create_owner_account(
            username=os.getenv('ADMIN_USERNAME', 'admin'),
            email=os.getenv('ADMIN_EMAIL', 'admin@example.com'),
            password=os.getenv('ADMIN_PASSWORD', 'admin')
        )

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Owner required decorator
def owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_owner:
            flash('This section is restricted to the website owner.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    # Get only published posts, ordered by date
    posts = Post.query.filter_by(status='published').order_by(Post.date_posted.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/blog')
def blog():
    posts = Post.query.filter_by(status='published').all()
    return render_template('blog.html', posts=posts)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('home'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/admin')
@login_required
@admin_required
def admin():
    users = User.query.all()
    return render_template('admin/dashboard.html', users=users)

@app.route('/admin/system-settings')
@login_required
@owner_required
def system_settings():
    return render_template('admin/system_settings.html')

@app.route('/admin/new-post', methods=['GET', 'POST'])
@login_required
@admin_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        status = request.form.get('status', 'draft')
        
        if not title or not content:
            flash('Title and content are required', 'error')
            return redirect(url_for('new_post'))
        
        # Create new post
        post = Post(
            title=title,
            content=content,
            author=current_user,
            status=status
        )
        
        # Handle featured image
        if 'featured_image' in request.files:
            file = request.files['featured_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                post.featured_image = filename
        
        # Handle additional images in content
        if 'content_images[]' in request.files:
            files = request.files.getlist('content_images[]')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    post_image = PostImage(filename=filename)
                    post.images.append(post_image)
        
        db.session.add(post)
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('view_post', post_id=post.id))
        
    return render_template('admin/new_post.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/admin/upload-image', methods=['POST'])
@login_required
@admin_required
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({
            'location': url_for('uploaded_file', filename=filename, _external=True)
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/admin/edit-post/<int:post_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.author = "Cornelius Hart"  # Set author name
        
        if 'image' in request.files:
            image_file = request.files['image']
            if allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                post.images.append(PostImage(filename=filename, post_id=post.id))
        
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('view_post', post_id=post.id))
        
    return render_template('admin/edit_post.html', post=post)

if __name__ == '__main__':
    app.run(debug=True)