import forms
import models

from forms import PostForm
from flask_bcrypt import check_password_hash
from flask import (Flask, g, 
render_template, flash, redirect, url_for, abort)
from flask_login import (LoginManager, login_user, 
logout_user, login_required, current_user)


DEBUG = True
PORT = 8000
HOST = '0.0.0.0'

app = Flask(__name__)
app.secret_key = 'snch0c1i!' # used for signing sessions for when we use flash

login_manager = LoginManager() # handles user auth
login_manager.init_app(app) # initializes user auth in app. 
login_manager.login_view = 'login' # Creates view for login


@login_manager.user_loader
def load_user(userid):
    """responsible for loading a user from whatever data-source(sqlite db) we use"""
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None


@app.before_request
def before_request():
    """connect to the db before request"""
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user


@app.after_request
def after_request(response):
    """close the db connection after each request"""
    g.db.close()
    return response


@app.route('/register', methods=('GET', 'POST'))
def register():
    """registers user and loads user into db."""
    form = forms.RegisterForm()
    if form.validate_on_submit():
        flash("You have completed registration!", 'success') # success is a category which 
        # will help organize the html later. 
        models.User.create_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data            
        ) 
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.route('/login', methods=('GET', 'POST'))
def login():
    """logs user into app linking the html page to login"""
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExists:
            flash("Your email and password don't match.", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user) # NOTE see 'logout_user' above - 
                # they both create sessions and gives user a cookie. 
                flash("You're now logged in!", "success")
                return redirect(url_for('index'))
            else:
                flash("Your email and password don't match.", "error")
    return render_template('login.html', form=form)


@app.route('/logout') # defaults to "GET" when its not specified. 
@login_required # decorator that means you have to be 
# logged in to get to this view. s
def logout():
    logout_user() # NOTE see 'login_user' above - 
    # they both create sessions and gives user a cookie. 
    # logout_user deletes the cookie 'kills the session'
    flash("You've been logged out", 'Success')
    return redirect(url_for('index'))


@app.route('/stream')
@app.route('/stream/<username>')
def stream(username=None):
    template='stream.html'
    if username and username != current_user.username:
        try:
            user = models.User.select().where(models.User.username**username).get()
        except models.DoesNotExist:
            abort(404)
        else:
            stream = user.posts.limit(100)
    else:
        stream = current_user.get_stream().limit(100)
        user=current_user
    if username:
        template='user_stream.html'
    return render_template(template, stream=stream, user=user)


@app.route('/post/<int:post_id>')
def view_post(post_id):
    posts = models.Post.select().where(models.Post.id == post_id)
    if posts.count() == 0:
        abort(404)
    return render_template('stream.html', stream=posts)


@app.route('/new_post', methods=('GET', 'POST'))
@login_required
def post():
    form = forms.PostForm()
    if form.validate_on_submit:
        models.Post.create(user=g.user._get_current_object(), content=PostForm.content) # had to changes this from the form created 
        # due to content causing a backlog error for content.post. 
        # NOTE NOTE NOTE NOTE NOTE NOTE content = above in creation of my model is the reason as to why I am not able to see post on screen. 
        # original script was: content=form.content.data.strip() - this causes an error from jinja2 engine for flask. 
        flash("You have spoken", "success")
        return redirect(url_for('index'))
    return render_template('post.html', form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    try:
        to_user = models.User.get(models.User.username**username)
    except models.DoesNotExists:
        abort(404)
    else:
        try:
            models.Relationship.create(
                from_user=g.user._get_current_object(),
                to_user=to_user
            )
        except models.IntegrityError:
            pass
        else:
            flash("You're now following {} ".format(to_user.username), 'success')
    return redirect(url_for('stream')) # redirect(url_for('stream'), username=to_user.username)



@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    try:
        to_user = models.User.get(models.User.username**username)
    except models.DoesNotExists:
        abort(404)
    else:
        # try: NOTE didnt need this code in here, but it shows weird in the database. 
        #     models.Relationship.get(
        #         from_user=g.user._get_current_object(),
        #         to_user=to_user
        #     ).delete_instance()
        # except models.IntegrityError:
        #     pass
        # else:
        flash("You've unfollowed {} ".format(to_user.username), 'success')
    return redirect(url_for('stream')) # redirect(url_for('stream'), username=to_user.username)


@app.route('/')
def index():
    """Home page."""
    stream = models.Post.select().limit(100)
    return render_template('stream.html', stream=stream)


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

if __name__ == "__main__":
    models.initialize()
    try:
        with models.DATABASE.transaction(): # transaction says try this out 
            # if it doesnt work remove what was done. 
            models.User.create_user(
                username='Adrian',
                email='ap.brown011@gmail.com',
                password='password',
                admin=True
            )
    except ValueError: # handles users already being in the db
        pass
    app.run(debug=DEBUG, port=PORT, host=HOST)
