from flask import Flask, redirect, url_for, flash, render_template, jsonify, request,session, make_response
from flask_login import login_required, logout_user, current_user, login_user
from .config import Config
from .models import db, login_manager, Token
from .oauth import blueprint
from .cli import create_db
from .models import db, User, OAuth, Token, Recipe, RecipeLike, Comments
from flask_cors import CORS
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import SQLAlchemyError
from flask_mail import Message, Mail
import datetime
import uuid


app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(blueprint, url_prefix="/login")
app.cli.add_command(create_db)
db.init_app(app)
mail = Mail()
mail.init_app(app)



bcrypt = Bcrypt(app)
migrate = Migrate(app, db)
login_manager.init_app(app)
CORS(app)

@app.route('/login', methods=["POST"])
def login():
    user = User.query.filter_by(email=request.get_json()['email']).first()
    if user and bcrypt.check_password_hash(user.password, request.get_json()['password']):
        token = Token.query.filter_by(user_id=user.id).first()
        if not token:
            token = Token(uuid=str(uuid.uuid4().hex), user_id=user.id)
            db.session.add(token)
            db.session.commit()
        login_user(user, remember=True)
    
    return jsonify({
        "username": user.name,
        "token": token.uuid
    })

@app.route("/logout")
@login_required
def logout():
    token = Token.query.filter_by(user_id=current_user.id).first()
    if token:
        db.session.delete(token)
        db.session.commit()
    logout_user()
    flash("You have logged out")
    return jsonify({"success": True})

@app.route("/")
def index():
    return render_template("home.html")


@app.route('/getuser')
@login_required
def getuser():
    profile_img = OAuth.query.filter_by(user_id=current_user.id).first()
    if profile_img:
        return jsonify({
            "user_id": current_user.id,
            "user_name": current_user.name,
            "profile_img_id": profile_img.provider_user_id
        })
    else:
        return jsonify({
            "user_id": current_user.id,
            "user_name": current_user.name,
        })

@app.route('/home')
@login_required
def home():
    return jsonify({
    })

@app.route('/posts', methods=["GET", "POST"])
def posts():
    posts = Recipe.query.all()
    jsonified_recipes = []
    for post in posts:
        like_count = RecipeLike.query.filter_by(recipe_id=post.id).count()
        post.like = like_count
        db.session.commit()
        jsonified_recipes.append(post.as_dict())
    return jsonify(jsonified_recipes)

@app.route('/post', methods=["GET", "POST"])
def post():
    recipe_id =request.get_json()["recipe_id"]
    post = Recipe.query.filter_by(id=recipe_id).first()
    return jsonify({
        "title":post.title,
        "ingredients":post.ingredients, 
        "directions":post.directions, 
        "user_id":post.id,
    })

@app.route('/register', methods=["POST"])
def register():
    hashed_password = bcrypt.generate_password_hash(
    request.get_json()['password']).decode('utf-8')
   
    user = User(
            name=request.get_json()["username"],
            email=request.get_json()["email"], 
            password=hashed_password
            )
    try:
        db.session.add(user)
        db.session.commit()
        login_user(user)
    except SQLAlchemyError as e:
        import code; code.interact(local=dict(globals(), **locals()))
        error = str(e.__dict__['orig'])
        return error

    return jsonify({
        "email": "email"
    })

@app.route('/post_recipe', methods=["GET", "POST", "OPTIONS"])
@login_required

def post_recipe():
    print('hi Loi')
    print(request.files)
    # recipe = Recipe(
    #     title=request.get_json()["title"],
    #     ingredients=request.get_json()["ingredients"], 
    #     directions=request.get_json()["directions"], 
    #     user_id=current_user.id,
    #     # image_file=request.get_json()["image_file"]
    # )
    # db.session.add(recipe)
    # db.session.commit()
    # return jsonify({
    #     "asdf": "asdfs",
    #     "wqhwqhdwqh": "qwddwqhgdwq"
    # })
    return jsonify({
        "hi": "hi"
    })

@app.route('/like', methods=["GET", "POST"])
@login_required
def like():
    print('exists', current_user.id)
    like_exists = RecipeLike.query.filter_by(user_id=current_user.id, recipe_id=request.get_json()["recipe_id"]).first()
    if like_exists: 
        like = RecipeLike.query.filter_by(user_id=current_user.id, recipe_id=request.get_json()["recipe_id"]).first()
        db.session.delete(like)
        db.session.commit()
    else:
        like = RecipeLike(user_id=current_user.id, recipe_id=request.get_json()["recipe_id"])
        db.session.add(like)
        db.session.commit()
    return jsonify({

    })
    
@app.route('/get_likes', methods=["GET", "POST"])
@login_required
def get_likes():
    likes = Recipe.query.all()
    jsonified_likes = []
    for like in likes:
        jsonified_likes.append(like.as_dict())
    return jsonify(
        jsonified_likes
    )
    
@app.route('/profile', methods=["GET", "POST"])
@login_required
def profile():
    user_recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    jsonified_recipes = []
    for recipe in user_recipes:
        jsonified_recipes.append(recipe.as_dict())
    return jsonify(jsonified_recipes)

@app.route('/favorites', methods=["GET", "POST"])
@login_required
def favorites():
    return jsonify()

@app.route('/comment', methods=["GET", "POST"])
@login_required
def comment():
    comment = Comments(body=request.get_json()["comment"], user_id=current_user.id, recipe_id=request.get_json()["recipe_id"])
    db.session.add(comment)
    db.session.commit()
    return jsonify({
        
    })

@app.route('/get_comments', methods=["GET", "POST"])
@login_required
def get_comments():
    comments = Comments.query.filter_by(recipe_id=request.get_json()["recipe_id"]).all()
    jsonified_comments = []
    for comment in comments:
        jsonified_comments.append(comment.amazing())
    return jsonify(jsonified_comments)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('users.reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    print('reqiuestesaasfas')
    if not current_user.is_authenticated:
        # return redirect(url_for('main.home'))
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        # return redirect(url_for('users.login'))
    return jsonify({ 
        "blah": "blah"
    })


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)