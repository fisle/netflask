# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, url_for, session, request, g, send_from_directory, send_file, Response, abort, safe_join, make_response
from flask.ext.login import login_user, logout_user, current_user, login_required
from sqlalchemy import exc
from app import app, db, lm
from forms import LoginForm, SignupForm, ModifyForm, PasswordForm
from models import User, Movie
from flask.ext.wtf import Form
from wtforms import TextField
import os, glob, formic, urllib2, base64, json
from config import CONVERT_CORES, VIDEO_FOLDER, ROTTEN_KEY
from werkzeug.security import generate_password_hash, check_password_hash

@lm.user_loader
def load_user(user_id):
  user_id = User.query.get(user_id)
  return user_id

@app.before_request
def before_request():
  g.user = current_user

# Setup page
@app.route('/setup', methods = ['GET', 'POST'])
def setup():
  # Try if database exists
  try:
    # If no user found in database, show form
    if db.session.query(User).count() < 1:
      form = SignupForm()
      # Passed form validation? continue
      if form.validate_on_submit():
        # Create user object and add it to database
        user = User(username = form.username.data, password = generate_password_hash(form.password.data))
        db.session.add(user)
        db.session.commit()
        flash('Account created! You are now logged in!')
        # Log new user in
        login_user(user)
        return redirect(url_for('index'))
      return render_template('signup.html', form = form)
    else:
      flash('Setup already completed.')
      return redirect(url_for('index'))
  # If not, let's create the database:
  except exc.OperationalError:
    db.create_all()
    return redirect(url_for('setup'))

# Movie listing by querying the DB
@app.route('/')
@app.route('/index')
@login_required
def index():
  new_movies = Movie.query.filter_by(status = 1).all()
  movies = Movie.query.filter_by(status = 2).order_by(Movie.name.asc()).all()
  return render_template('movies.html', movies = movies, new_movies = new_movies)

# Watch movie page
@app.route('/movies/watch/<movie_id>')
@login_required
def movie(movie_id):
  movie = Movie.query.filter_by(id = movie_id).first()
  return render_template('index.html', movie = movie)

# Subtitles. For scandinavian letters to work we need to re-encode them to UTF-8
@app.route('/subtitles/')
@login_required
def subtitles():
  movie = request.args.get('movie')
  videofolder = VIDEO_FOLDER
  path = safe_join(videofolder, movie)
  if movie.endswith('.srt'):
    filename = safe_join(videofolder, movie)
    with open(filename, 'r') as fd:
      movie = fd.read()
    movie = movie.decode('iso-8859-1').encode('utf-8')
    return Response(movie, mimetype='text/plain')
  else:
    flash('Not a subtitle file.')
    return redirect(url_for('index'))

# This is where the magic happens ~
# Get movie url by ID, pass request to HTTPd to serve correct video file
@app.route('/videos/<movie>')
@login_required
def video(movie):
  # Movie name is just ID.extension so we can split it with dot
  split = movie.split('.')
  movie_id = split[0]
  extension = split[1]
  movie = Movie.query.filter_by(id = movie_id).first()
  # Remove extensions from urls fetched from database
  url = movie.url
  url = url.replace('.mp4','')
  url = url.replace('.avi','')
  url = url.replace('.mkv','')
  # Append correct extension to it
  redirect_path = '/raw_videos/{!s}.{!s}'.format(url, extension)

  response = make_response('')
  # Generate proper mimetypes
  if extension == 'webm':
    mimetype = 'video/webm'
  elif extension == 'mkv':
    mimetype = 'video/h264'
  elif extension == 'mp4':
    mimetype = 'video/mp4'
  # Let HTTPd serve the file
  response.headers['Content-Type'] = mimetype
  response.headers['X-Accel-Redirect'] = redirect_path
  return response

# New movie found!
@app.route('/modify', methods = ['GET', 'POST'])
@login_required
def modify():
  form = ModifyForm()
  if form.validate_on_submit():
    movie = form.name.data

    # Get movie data and put it to our database
    rotten_url = 'http://api.rottentomatoes.com/api/public/v1.0/movies/{!s}.json?apikey={!s}'.format(movie, ROTTEN_KEY)
    movie = urllib2.urlopen(rotten_url)
    movie = movie.read()
    movie = json.loads(movie)
    description = movie['synopsis']
    genres = movie['genres']

    # Put all genres in a string
    final = ""
    counter = 1
    for genre in genres:
      final += genre
      if len(genres) > 1 and counter < len(genres):
        final += ', '
      counter += 1
    genres = final

    ratings = movie['ratings']
    ratings = ratings.get('audience_score')
    posters = movie['posters']
    posters = posters.get('thumbnail')
    movie = movie['title']
    ticketid = form.id.data

    # Just dump it to database
    querymovie = Movie.query.filter_by(id = ticketid).first()
    querymovie.status = 2
    querymovie.description = description
    querymovie.genres = genres
    querymovie.ratings = ratings
    querymovie.posters = posters
    querymovie.name = movie
    db.session.commit()
    flash(movie+' added!')

  items = Movie.query.filter_by(status = 1).all()
  return render_template('modify.html', form = form, items = items)

@app.route('/profile', methods = ['GET', 'POST'])
@login_required
def profile():
  form = PasswordForm()
  if form.validate_on_submit():
    user_data = User.query.filter_by(id = g.user.id).first()
    if check_password_hash(user_data.password, form.password.data):
      user_data.password = generate_password_hash(form.newpassword.data)
      db.session.commit()
      flash('Password changed!')
      return redirect(url_for('profile'))
  return render_template('profile.html', form = form)
  
# Register page. Only logged in users can create new users
# TODO: Only staff can register accounts
@app.route('/signup', methods = ['GET', 'POST'])
@login_required # Comment this line to let guests create new accounts
def signup():
  form = SignupForm()
  # Form validation passed? Add new user.
  if form.validate_on_submit():
    user = User(username = form.username.data, password = generate_password_hash(form.password.data))
    db.session.add(user)
    db.session.commit()
    flash('Account created! You are now logged in!')
    login_user(user)
    return redirect(url_for('index'))
  return render_template('signup.html', form = form)

# Login page.
@app.route('/login', methods = ['GET', 'POST'])
def login():
  # Already authenticated? gtfo
  if g.user is not None and g.user.is_authenticated():
    flash('Already logged in.')
    return redirect(url_for('index'))
  form = LoginForm()
  # Passed form validation? let's roll
  if form.validate_on_submit():
    session['remember_me'] = form.remember_me.data
    user = form.username.data
    user_data = User.query.filter_by(username = user).first()
    # User exists
    if user_data:
      # Password matches
      if check_password_hash(user_data.password, form.password.data):
        # Ticket 'remember me'?
        if 'remember_me' in session:
          remember_me = session['remember_me']
          session.pop('remember_me', None)
        # All good, let's log user in
        login_user(user_data, remember = remember_me)
        flash('Logged in!')
        return redirect(request.args.get('next') or url_for('index'))
      else:
        flash('Invalid username or password')
    else:
      flash('Invalid username or password')
  return render_template('login.html', form = form)

@app.route('/logout')
def logout():
  logout_user()
  flash('Logged out!')
  return redirect(url_for('index'))

