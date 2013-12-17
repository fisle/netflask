#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Script to check for new movies.
# Set a cronjob for this to periodically check
#
from flask.ext.script import Manager
from app import app, db, lm
from app.models import Movie
import os, glob, formic, urllib2, base64, json
from config import CONVERT_CORES, VIDEO_FOLDER, BROKER_URL, CELERY_RESULT_BACKEND, SUBTITLES_LANG_PRIORITY
from celery import Celery
import shlex
import subprocess
import time
manager = Manager(app)

celery = Celery(broker=BROKER_URL, backend=CELERY_RESULT_BACKEND)

# Convert functions, we are using only convert_mp4. For Firefox support, you should also use convert_webm.
@celery.task()
def convert_ogg(id, movie):
  movie_out = movie.replace(movie[-4:], ".ogv")
  command = 'ffmpeg -i "{!s}" -threads {!s} -acodec libvorbis -ac 2 -ar 44100 -crf 18 "{!s}"'.format(movie, CONVERT_CORES, movie_out)
  proc = subprocess.Popen(shlex.split(command))
  proc.communicate()
  complete(id)

@celery.task()
def convert_webm(id, movie):
  movie_out = movie.replace(movie[-4:], ".webm")
  command = 'ffmpeg -i "{!s}" -threads {!s} -acodec libvorbis -ac 2 -ar 44100 -crf 18 -vcodec libvpx "{!s}"'.format(movie, CONVERT_CORES, movie_out)
  proc = subprocess.Popen(shlex.split(command))
  proc.communicate()
  complete(id)

@celery.task()
def convert_mp4(id, movie):
  """Backgrounded function which converts input movie into x264 .mp4 file"""
  movie_out = movie.replace(movie[-4:], ".mp4") # Replace extension with .mp4
  command = 'ffmpeg -i "{!s}" -threads {!s} -acodec libfaac -vcodec libx264 -crf 18 "{!s}"'.format(movie, CONVERT_CORES, movie_out)
  proc = subprocess.Popen(shlex.split(command)) # split command properly and run it
  proc.communicate()
  # movie converted? we are done :>
  complete(id)

def complete(id):
  """Set movie status to completed in DB"""
  movie = Movie.query.filter_by(id = id).first()
  movie.status = 1
  db.session.commit()

@celery.task()
def get_subtitle(file_name):
  """Fetches subtitles automatically using frameboise, then converts them to srt with subconvert"""
  command = 'framboise --save-all "{!s}" -l {!s}'.format(file_name, SUBTITLES_LANG_PRIORITY)
  proc = subprocess.Popen(shlex.split(command))
  proc.communicate()
  path = os.path.abspath(file_name)
  fileset = formic.FileSet(include=["*.sub"], directory = path)
  for filename in fileset:
    command = 'subconvert -q "{!s}"'.format(filename)
    proc = subprocess.Popen(shlex.split(command))
    proc.communicate()

@manager.command
def scan_folders():
  """Scans video folders for video files, converts new videos and adds them to DB"""
  movies = []
  # Check for mp4, mkv, avi files in video folder
  fileset = formic.FileSet(include=["*.mp4", "*.mkv", "*.avi"], directory=VIDEO_FOLDER)
  # Loop found files
  for file_name in fileset:
    # Return relative path of found files
    rec_name = file_name.replace(VIDEO_FOLDER, '')
    rel_name = rec_name
    rec_name = rec_name.replace('.avi', '.mp4')
    # See if path found in database, if not: continue
    if Movie.query.filter_by(url = rec_name).first() < 1:
      # Check if filesize is different after 5 second, aka not completely uploaded yet
      size = os.path.getsize(file_name)
      time.sleep(5)
      if size == os.path.getsize(file_name):
        # Fetch subtitles automatically
        get_subtitle(file_name)
        # Generate subtitle path from movie path
        subsrt = rec_name.replace('.mp4', '.srt')
        subsrt = subsrt.replace('.avi', '.srt')
        subsrt = subsrt.replace('.mkv', '.srt')
        # Get extension and add movie to database as IN_PROGRESS
        extension = os.path.splitext(rel_name)[1]
        dbextension = os.path.splitext(rec_name)[1]
        newmovie = Movie(url = rec_name, srt = subsrt, type = dbextension)
        db.session.add(newmovie)
        db.session.commit()
        # Check if needs converting or can just call done
        if extension == '.mp4':
          complete(newmovie.id)
        elif extension == '.avi':
          convert_mp4(newmovie.id, file_name)
        elif extension == '.mkv':
          complete(newmovie.id)

if __name__ == '__main__':
  manager.run()
