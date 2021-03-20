from flask import Flask, redirect, render_template, url_for, flash, session
from flask_session import Session
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms.fields import *
from wtforms.validators import DataRequired
import os
from os.path import expanduser
import eyed3
import requests
import io
import youtube_dl
import subprocess
import base64
from PIL import Image
import re
from datetime import timedelta
from pathlib import Path

app = Flask(__name__)
# app.secret_key = secrets.token_urlsafe(16)
app.secret_key = 'somesecretkey'
CSRFProtect(app)

# Check Configuration section for more details
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5)

# The maximum number of items the session stores
# before it starts deleting some, default 500
app.config['SESSION_FILE_THRESHOLD'] = 20
app.config.from_object(__name__)
Session(app)

# set default button sytle and size, will be overwritten by macro parameters
app.config['BOOTSTRAP_BTN_STYLE'] = 'primary'
app.config['BOOTSTRAP_BTN_SIZE'] = 'sm'
app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'darkly'  # uncomment this line to test bootswatch theme

bootstrap = Bootstrap(app)

MUSIC_DIR = Path.home() / 'Music'
MUSIC_DIR.mkdir(parents=True, exist_ok=True)


def convert_sec_to_hms(seconds):
    min, sec = divmod(seconds, 60)
    hour, min = divmod(min, 60)
    return f'{round(hour)}h:{round(min)}m:{round(sec)}s'


def download_and_convert_to_mp3(form, byte_img):
    base, ext = os.path.splitext(session['output_filepath_mp3'])
    output_filepath_ytdl_ext = base + '.%(ext)s'
    subprocess.run(
        ['youtube-dl', '-f', 'bestaudio', '--restrict-filenames', '--extract-audio', '--audio-format', 'mp3', '-o',
         output_filepath_ytdl_ext, session['url']])

    audio_file = eyed3.load(session['output_filepath_mp3'])
    audio_file.initTag()
    audio_file.tag.artist = form.artist.data
    audio_file.tag.genre = form.genre.data
    audio_file.tag.album_artist = form.album_artist.data
    audio_file.tag.album = form.album.data
    audio_file.tag.composer = form.composer.data
    audio_file.tag.images.set(3, byte_img.getvalue(), 'image/jpeg')
    audio_file.tag.save()


def encoded_img():
    response = requests.get(session['yt_info']['thumbnail'])
    img = Image.open(io.BytesIO(response.content))
    byte_img = io.BytesIO()
    img.save(byte_img, "JPEG")
    encoded_imgage = base64.b64encode(byte_img.getvalue())
    return byte_img, encoded_imgage


genre_values = ('Alternative', 'Bhajans', 'BWW', 'Carnatic Fusion',
                'Carnatic Traditional', 'Shloka', 'Hindi Movie', 'Tamil Movie',
                'Kannada Movie', 'Kids English Songs', 'Lullaby', 'Meditation',
                'Pop', 'Tamil Rhymes', 'Rock', 'Tamil Stories', 'Upanyasam')


class YTGetInfoForm(FlaskForm):
    url = StringField('URL', validators=[DataRequired()])
    submit = SubmitField()


class YTDLForm(FlaskForm):
    title = StringField('Song Title', validators=[DataRequired()])
    genre = SelectField(choices=genre_values)
    artist = StringField('Artist', validators=[DataRequired()])
    album = StringField('Album', validators=[DataRequired()])
    album_artist = StringField('Album Artist', validators=[DataRequired()])
    composer = StringField('Composer', validators=[DataRequired()])
    download = SubmitField()


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    """
    Basic landing page. Accepts a YouTube URL as an user input.
    :return: Returns a user form to enter MP3 metadata such as title, artist etc. as input
            Or returns the same page back, if the song requested has already been downloaded.
    """
    form = YTGetInfoForm()
    if form.validate_on_submit():
        session["url"] = form.url.data
        try:
            with youtube_dl.YoutubeDL() as ydl:
                url = form.url.data
                session["yt_info"] = ydl.extract_info(form.url.data, download=False)
        except youtube_dl.utils.DownloadError:
            flash(f'Bad url - {url}. Could not download.', 'error')
            return redirect(url_for('home'))

        filename = re.sub(r'[^\x00-\x7f]', r'', session['yt_info']["title"])  # Removing all non-ascii
        filename = re.sub('[^0-9a-zA-Z]+', '_', filename)  # Replacing all non-alpha-numeric with '_'
        session["filename"] = filename
        session["output_filepath_mp3"] = Path(MUSIC_DIR, filename + '.mp3')

        if not os.path.exists(session['output_filepath_mp3']):
            return redirect(url_for('yt_form'))
        else:
            flash(f'Song {session["filename"][:20]}...mp3 already exists', 'warning')
            return redirect(url_for('home'))

    return render_template('yturl.html', form=form)


@app.route('/ytform', methods=['GET', 'POST'])
def yt_form():
    """
    Form to enter the MP3 metadata such as title, artist, album etc.
    :return: Comes back to the home page after successfully downloading the YouTube audio file and converting it to MP3
    """
    title = session['yt_info']["title"]
    duration = convert_sec_to_hms(session['yt_info']["duration"])
    byte_img, encoded_imgage = encoded_img()

    form = YTDLForm()

    if form.validate_on_submit():
        download_and_convert_to_mp3(form=form, byte_img=byte_img)
        flash(f'Song {session["filename"][:20]}...mp3 successfully downloaded', 'success')
        return redirect(url_for('home'))

    return render_template('yt_form.html',
                           form=form,
                           img_data=encoded_imgage.decode('utf-8'),
                           title=title,
                           duration=duration)
