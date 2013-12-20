from app import app, db

# Roles
ROLE_USER = 0
ROLE_MOD = 1
ROLE_ADMIN = 2

# User model
class User(db.Model):
  __tablename__ = 'users'
  id = db.Column(db.Integer, primary_key = True)
  username = db.Column(db.String(64), index = True, unique = True)
  password = db.Column(db.String)
  role = db.Column(db.SmallInteger, default = ROLE_USER)

  def is_authenticated(self):
    return True

  def is_active(self):
    return True

  def get_id(self):
    return unicode(self.id)

  def is_anonymous(self):
    return False

# Movie model
class Movie(db.Model):
  __tablename__ = 'movies'
  id = db.Column(db.Integer, primary_key = True)
  name = db.Column(db.String(255), index = True, unique = True)
  url = db.Column(db.String(255))
  srt = db.Column(db.String(255))
  status = db.Column(db.SmallInteger)
  description = db.Column(db.Text)
  genres = db.Column(db.String(255))
  ratings = db.Column(db.String(255))
  posters = db.Column(db.Text)
  type = db.Column(db.String(255))
