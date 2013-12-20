Netflask
======
Simple private HTML5 video gallery written in Flask.


Features
======
  - HTML5 player using mediaElement player
  - Automatically scans library for new movies (Remember to set a cronjob!)
  - Automatically converts new videos into proper formats
  - Automatically fetches subtitles
  - Fetches movie data from RottenTomatoes API
  - Uses X-Accel-Redirect to serve videos in a secure way
  

Requirements
======
  - Python 2
  - RabbitMQ server
  - FFmpeg - [Custom install instructions available here](https://fisle.eu/view/Installing-FFmpeg-from-source-on-Debian-Wheezy)


Bugs
=====
  - Videos are not playing under Firefox on Linux, due to codec licensing issues. You can enable WebM encoding in sources.


Installation
=====
    git clone http://git.vpsboard.com/fisle/netflask.git

    cd netflask

    virtualenv venv

    source venv/bin/activate

    pip install -r requirements.txt

  * Edit app/templates/modify.html, change JS values 'apikey' to RottenTomatoes API key.

  * Edit config.py    

  * Deploy! [Gunicorn deploy guide](http://docs.gunicorn.org/en/latest/deploy.html)

  * Point your browser to /setup to create new user

  * Set up cronjob for scan.py. This scans for new video files.

    */5 * * * * /path/to/venv/bin/python /path/to/scan.py scan_folders


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


Like my work?
=====
Donations are always accepted and encourages the development of Open Source Software.
BTC: 19LUqCSZjMqy8H5jQTiHdmfcAPd5ZcyLJm
LTC: LMGK2Hu8SotnKYRxV4NE8sZ7wKBc6Aaezo
