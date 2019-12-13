from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_login import LoginManager, UserMixin
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
import datetime 
app = Flask(__name__)

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_view = "facebook.login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.request_loader
def load_user_from_request(request):
    api_key = request.headers.get('Authorization')
    if api_key:
        api_key = api_key.replace('Token ', '', 1)
        token = Token.query.filter_by(uuid=api_key).first()
        if token:
            return token.user
    return None
    

class User(UserMixin, db.Model):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)
    password = db.Column(db.String(256))
    email = db.Column(db.String(50), unique=True)
    img_url = db.Column(db.String(100))
    fb_img_id = db.Column(db.Numeric(asdecimal=False))
    recipes = db.relationship('Recipe', backref='user', lazy=True)
    comments = db.relationship("Comments", backref="user", lazy=True)
    
    def get_reset_token(self, expires_sec=1800):
        s = Serializer("nope-me", expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')
    
    @staticmethod
    def verify_reset_token(token):
        s = Serializer("nope-me")
        try: 
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User)

class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User")

class Recipe(db.Model):
    __searchable__ =["title"]

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    ingredients = db.Column(db.JSON, nullable=False)
    directions = db.Column(db.Text, nullable=False)
    like = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    deleted = db.Column(db.Boolean, default=False)
    comments = db.relationship("Comments", backref="recipe", lazy=True)
    images = db.relationship("Images", backref="recipe", lazy=True)

    def amazing(self):
        return { "id": self.id,
                "title": self.title,
                "ingredients":self.ingredients,
                "like":self.like,
                "user_id":self.user_id,
                "directions": self.directions,
                "description": self.description,
                "comments":[ i.amazing() for i in self.comments],
                "user_name":self.user.name,
                "deleted":self.deleted,
                "img_url":self.user.img_url,
                "fbId": self.user.fb_img_id,
                "images": [ i.amazing() for i in self.images],
                "created": self.created
                }
    def likedRecipe(self, pid, curU):
        isLiked = False
        if not curU.is_authenticated:
            isLiked = False 
        elif curU.is_authenticated:
            if RecipeLike.query.filter_by(user_id=curU.id, recipe_id=pid).first():
                isLiked = True
        return { "id": self.id,
                "title": self.title,
                "ingredients":self.ingredients,
                "like":self.like,
                "user_id":self.user_id,
                "directions": self.directions,
                "description": self.description,
                "comments":[ i.amazing() for i in self.comments],
                "user_name":self.user.name,
                "deleted":self.deleted,
                "img_url":self.user.img_url,
                "fbId": self.user.fb_img_id,
                "images": [ i.amazing() for i in self.images],
                "created": self.created,
                "isLiked" : isLiked
                }

    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

class RecipeLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    recipe_id = db.Column(db.Integer)

    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

class Comments(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"))
    deleted = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def amazing(self):
        return { "id": self.id,
                "body": self.body,
                "recipe_id":self.recipe_id,
                "user_name":self.user.name,
                "user_id": self.user_id,
                "deleted": self.deleted,
                "img": self.user.img_url,
                "fb_img": self.user.fb_img_id,
                "created": self.created
                }

class Images(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"))
    img_url = db.Column(db.String, default='default.jpg')

    def amazing(self):
        return { "id": self.id,
                "recipe_id": self.recipe_id,
                "img_url":self.img_url,
                }

    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}


