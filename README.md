Flaskfix
======
Simple private HTML5 video gallery written in Flask.

Supports .srt subtitles. Uses RottenTomatoes API to fetch video info.

Uses X-Accel-Redirect to serve video files.

Note: Subtitle names must be identical to video file, apart from extension.

Installation
=====
    virtualenv venv

    source venv/bin/activate

    pip install -r requirements.txt

Edit scan.py and point first line to absolute path of venv/bin/python

Edit app/templates/modify.html, change JS values 'apikey' to RottenTomatoes API key.

Edit config.py    

    ./run.py

Browse to 127.0.0.1:5000/setup

Set up cronjob for scan.py. This scans for new video files.


Deploying
=====

Nginx conf:

    location /raw_videos/ {
      internal;
      alias /absolute/path/to/videos/;
    }



Problems
=====
pip install -r requirements.txt fails?

    source venv/bin/activate

    wget http://python-distribute.org/distribute_setup.py

    python distribute_setup.py
