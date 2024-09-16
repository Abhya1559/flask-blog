from flask import Flask,render_template, flash, request,redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField ,PasswordField,BooleanField,ValidationError,TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from wtforms.widgets import TextArea
from flask_login import UserMixin,login_user,LoginManager, login_required, logout_user,current_user
from flask_ckeditor import CKEditor
from flask_ckeditor import CKEditorField
from flask_wtf.file import FileField
from werkzeug.utils import secure_filename
import uuid as uuid
import os


app = Flask(__name__) 
#Add Ck editor
ckeditor = CKEditor(app)
  # Flask constructor 
#add database URI = UNIFORM RESOURCE INDICATOR
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Abhya%405niko@localhost/our_users'

app.config['SECRET_KEY'] = "abhya@"
UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#intialize the database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#create a search form
class SearchForm(FlaskForm):
    searched = StringField("Searched",validators=[DataRequired()])
    submit = SubmitField("Submit")

class LoginForm(FlaskForm):
    username = StringField("Username",validators=[DataRequired()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Submit")

@app.route('/login', methods = ['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username =form.username.data).first()
        if user:
            #check the hash
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("login Successfully!!")
                return redirect(url_for('dashboard'))
            else:
                flash("Wrong username and password! try again")
        else:
            flash("That user doesnot exsist!")
    return render_template('login.html',form = form)

#create logout function
@app.route('/logout',methods = ['GET','POST'])
@login_required
def logout():
    logout_user()
    flash("You have been logout!!")
    return redirect(url_for('login'))

@app.route('/dashboard',methods = ['GET','POST'])
@login_required
def dashboard():
    form = UserForm()
    id = current_user.id
    name_to_update = User.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.favourite_color = request.form['favourite_color']
        name_to_update.username = request.form['username']
        name_to_update.about_author = request.form['about_author']
        

        if request.files['profile_pic']:
            name_to_update.profile_pic = request.files['profile_pic']
        # Save that im

            # Grab Image Name 
            pic_filename = secure_filename(name_to_update.profile_pic.filename)
            # set uid
            pic_name = str(uuid.uuid1()) + "_" + pic_filename
            saver = request.files['profile_pic']
            
            #change it to a string
            name_to_update.profile_pic = pic_name
            try:
                db.session.commit()
                saver.save(os.path.join(app.config['UPLOAD_FOLDER'],pic_name))
                flash("User Updated Successfully")
                return render_template("dashboard.html",form = form,name_to_update = name_to_update)
            except:
                flash("Error!! Let's try again")
                return render_template("dashboard.html",form = form,name_to_update = name_to_update)
        else:
            db.session.commit()
            flash("User Updated Successfully")
            return render_template("dashboard.html",form = form,name_to_update = name_to_update)

    else:
        flash("Error!! Let's try again")
        return render_template("dashboard.html",form = form,name_to_update = name_to_update,id = id)
    return render_template('dashboard.html')


class PostForm(FlaskForm):
    title = StringField("Title",validators=[DataRequired()])
    #content =StringField("Content",validators=[DataRequired()],widget=TextArea())
    content = CKEditorField('Content',validators=[DataRequired()])
    author =StringField("Author")
    slug = StringField("Slug",validators=[DataRequired()])
    submit =SubmitField("Submit")

@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
    post_to_delete = Post.query.get_or_404(id)
    id = current_user.id
    if id == post_to_delete.poster.id or id == 2:
        try:
            db.session.delete(post_to_delete)
            db.session.commit()
            flash("Hey Blog post was deleted")
            posts = Post.query.order_by(Post.date_posted)
            return render_template("posts.html",posts = posts)
        except:
            flash("Oops There was a problem deleting Post, try  again")
            posts = Post.query.order_by(Post.date_posted)
            return render_template("posts.html",posts = posts)
    else:    
        flash("you are not authorized to delete the post")
        posts = Post.query.order_by(Post.date_posted)
        return render_template("posts.html",posts = posts)

@app.route('/posts')
def posts():
    #Grab All the post from database
    posts = Post.query.order_by(Post.date_posted)
    return render_template("posts.html",posts = posts)

@app.route('/posts/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    return render_template('post.html', post=post)

@app.route('/posts/edit/<int:id>', methods = ['GET','POST'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.author = form.author.data
        post.slug = form.slug.data
        post.content = form.content.data
        #Update data base
        db.session.add(post)
        db.session.commit()
        flash("Post has been Updated")
        return redirect(url_for('post',id = post.id))
    
    
    if current_user.id == post.poster_id:
        form.title.data = post.title
        #form.author.data = post.author
        form.slug.data = post.slug
        form.content.data = post.content
        return render_template('edit_post.html', form = form)
    
    else:
        flash("You are not authorized to edit this post")
        posts = Post.query.order_by(Post.date_posted)
        return render_template("posts.html",posts = posts)

#Add Post Page
@app.route('/add-post',methods = ['GET','POST'])
@login_required
def add_post():
    form = PostForm()

    if form.validate_on_submit():
        poster = current_user.id
        post = Post(title=form.title.data,content= form.content.data, poster_id = poster ,slug = form.slug.data)
        #clear  The Form
        form.title.data =''
        form.content.data =''
        form.author.data =''
        form.slug.data =''

        #Add post data to database
        db.session.add(post)
        db.session.commit()

        flash("Blog Post Submitted SuccessFully")

        #redirect to web page
    return render_template("add_post.html",form = form)
#Json Thing
@app.route('/date')
def get_current_date():
    favourite_pizza = {
        "Jhon": "pepperoni",
        "Mary":"cheese"
    }
    return favourite_pizza
    return {"Date": date.today()}

#create a blog post model
class Post(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    #author = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime,default = datetime.now())
    slug = db.Column(db.String(255))
    #foreighn key to link users 
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'))
 


#create model
class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key = True)
    username = db.Column(db.String(20), nullable = False,unique = True)
    name = db.Column(db.String(200),nullable = False)
    email =db.Column(db.String(200),nullable = False,unique= True)
    favourite_color = db.Column(db.String(120))
    about_author = db.Column(db.Text(500),nullable = True)
    date_added=db.Column(db.DateTime,default = datetime.now())
    profile_pic = db.Column(db.String(500),nullable = True)
    #Doing Some password Stuff
    password_hash = db.Column(db.String(128))
    #user can have many post
    posts = db.relationship('Post',backref = 'poster')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)

@app.route('/delete/<int:id>')
def delete(id):
    if id  == current_user.id:
        name = None
        form = UserForm()

        user_to_delete = User.query.get_or_404(id)
        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            flash("user deleted SuccessFully")
            our_users = User.query.order_by(User.date_added).all()
            return render_template("add_user.html",form = form,name=name,our_users = our_users)
        except:
            flash("Oops! There is a problem")
            return render_template("add_user.html",form = form,name=name,our_users = our_users)
    else:
        flash("Sorry You are not allowed to delete the user")
        return redirect(url_for('dashboard'))


#update database Record
@app.route('/update/<int:id>',methods = ['GET','POST'])
def update(id):
    form = UserForm()
    name_to_update = User.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.favourite_color = request.form['favourite_color']
        name_to_update.username = request.form['username']
        try:
            db.session.commit()
            flash("User Updated Successfully")
            return render_template("user.html",form = form,name_to_update = name_to_update)
        except:
            flash("Error!! Let's try again")
            return render_template("update.html",form = form,name_to_update = name_to_update)
    else:
        flash("Error!! Let's try again")
        return render_template("update.html",form = form,name_to_update = name_to_update,id = id)

#create A string
    def __repr__(self):
        return '<Name %r' % self.name
    

class UserForm(FlaskForm):
    name = StringField("Name",validators = [DataRequired()])
    username = StringField("username",validators = [DataRequired()])
    email = StringField("Email",validators=[DataRequired()])
    favourite_color = StringField("Favourite Color..")
    about_author = TextAreaField("About Author")
    profile_pic = FileField("Profile pic")
    password_hash = PasswordField('password',validators=[DataRequired(),EqualTo('password_hash2',message='passwords must match!')])
    password_hash2 =PasswordField('Confirm Password',validators=[DataRequired()])
    submit = SubmitField("Submit")

#create class form
class NamerForm(FlaskForm):
    name = StringField("What is your name?",validators = [DataRequired()])
    submit = SubmitField("Submit")

class PasswordForm(FlaskForm):
    email = StringField("What is your email?",validators = [DataRequired()])
    password_hash = PasswordField("What is your password?",validators = [DataRequired()])
    submit = SubmitField("Submit")

@app.context_processor
def base():
    form = SearchForm()
    return dict(form = form)

#create a search function
@app.route('/search',methods = ["POST"])
def search():
    form = SearchForm()
    posts = Post.query
    if form.validate_on_submit():
        post.searched = form.searched.data
        posts = posts.filter(Post.content.like('%' + post.searched + '%'))
        posts = posts.order_by(Post.title).all()
        return render_template("search.html", form = form, searched = post.searched, posts = posts)

@app.route('/user/add', methods = ['GET','POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user is None:
            ##hash Password
            hashed_pw = generate_password_hash(form.password_hash.data,'pbkdf2:sha256')
            user = User(username = form.username.data,name = form.name.data, email = form.email.data,favourite_color = form.favourite_color.data,password_hash = hashed_pw)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.name.data = ''
        form.username.data =''
        form.email.data = ''
        form.favourite_color.data = ''
        form.password_hash.data =''

        
        flash("User Added Successfully!")
    our_users = User.query.order_by(User.date_added).all()
    return render_template("add_user.html",form = form,name=name,our_users = our_users)

#Creating an Admin area
@app.route('/admin')
@login_required
def admin():
    id = current_user.id
    if id == 3:
        return render_template("admin.html")
    else:
        flash("you must have to be admin to access the admin page..")
        return redirect(url_for('dashboard'))
# def index():
#     return "<h1>hello WOrld</h1>"

@app.route('/')
def index():
    first_name = "Abhya"
    stuff = "This is <strong>Bold Text</strong>"
    favourite_pizza = ["Pepperoni","cheese","Mushrooms",41]
    return render_template("index.html",first_name=first_name,stuff = stuff, favourite_pizza =  favourite_pizza)

#localhost:5000/user/Abhya
@app.route('/user/<name>')
def user(name):
    return render_template("user.html",user_name=name)

#create custom error pages

#invalid URL
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"),404

@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"),500
#create password page
@app.route('/test_pw',methods = ['GET','POST'])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None

    form = PasswordForm()
    #validate Form
    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        form.email.data = ''
        form.password_hash.data = ''

        pw_to_check = User.query.filter_by(email =email).first()

        #check Hash password
        passed = check_password_hash(pw_to_check.password_hash, password)
        #flash("Form submitted successfully")
    return render_template("test_pw.html",email = email, password = password ,pw_to_check = pw_to_check,passed=passed, form = form)
@app.route('/name',methods = ['GET','POST'])
def name():
    name = None
    form = NamerForm()
    #validate Form
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        flash("Form submitted successfully")
    return render_template("name.html",name = name, form = form)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)