# YouTube MP3 Downloader

### Installation

1. `git clone <this repo>`
1. Create a virtual environment.
1. Have `ffmpeg` installed.
1. If you want to host this on a Raspberry Pi, then [follow these instructions](https://www.techcoil.com/blog/how-to-setup-python-imaging-library-pillow-on-raspbian-stretch-lite-for-processing-images-on-your-raspberry-pi/) to install the `pillow` package dependencies.
1. `pip install -U pip setuptools bootstrap-flask requests eyed3 flask-wtf pillow youtube-dl`
1. `export FLASK_APP=app.py`
1. `flask run`
1. Launch `http://127.0.0.1:5000/`

### User Guide

1. Follow the screenshots in the `images/` folder

![](images/S1.PNG)
![](images/S2.PNG)
![](images/S3.PNG)