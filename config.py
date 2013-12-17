# -*- coding: utf-8 -*-
import os
basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
CSRF_ENABLED = True

# Change us
SECRET_KEY = '2secret4u' # Crypt functions use this value to sign cookies n shit
CONVERT_CORES = 2 # How many cores used for encoding
VIDEO_FOLDER = '/abs/path/to/videos/' # Where the videos at
ROTTEN_KEY = 'change_me' # RottenTomatoes API key
SUBTITLES_LANG_PRIORITY = 'fin,eng'

# celery broker and backend locations
BROKER_URL = 'amqp://'
CELERY_RESULT_BACKEND = 'amqp://'
