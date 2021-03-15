from flask import Flask, redirect, render_template, url_for, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm, CSRFProtect
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

app = Flask(__name__)
app.secret_key = '8788e69b1f17a2ce706a9d9c'

# set default button sytle and size, will be overwritten by macro parameters
app.config['BOOTSTRAP_BTN_STYLE'] = 'primary'
app.config['BOOTSTRAP_BTN_SIZE'] = 'sm'
app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'darkly'  # uncomment this line to test bootswatch theme

bootstrap = Bootstrap(app)
csrf = CSRFProtect(app)

yt_data = {}

home = expanduser("~")
MUSIC_DIR = os.path.join(home, 'Music')
if not os.path.exists(MUSIC_DIR):
    os.makedirs(MUSIC_DIR)


def convert_sec_to_hms(seconds):
    min, sec = divmod(seconds, 60)
    hour, min = divmod(min, 60)
    return f'{round(hour)}h:{round(min)}m:{round(sec)}s'


def download_and_convert_to_mp3(form):
    base, ext = os.path.splitext(yt_data.get('output_filepath_mp3'))
    output_filepath_ytdl_ext = base + '.%(ext)s'
    subprocess.run(
        ['youtube-dl', '-f', 'bestaudio', '--restrict-filenames', '--extract-audio', '--audio-format', 'mp3', '-o',
         output_filepath_ytdl_ext, yt_data.get('url')])

    audio_file = eyed3.load(yt_data.get('output_filepath_mp3'))
    audio_file.initTag()
    audio_file.tag.artist = form.artist.data
    audio_file.tag.genre = form.genre.data
    audio_file.tag.album_artist = form.album_artist.data
    audio_file.tag.album = form.album.data
    audio_file.tag.composer = form.composer.data
    audio_file.tag.images.set(3, yt_data.get('byte_img').getvalue(), 'image/jpeg')
    audio_file.tag.save()


def encoded_img():
    response = requests.get(yt_data.get('yt_info').get('thumbnail'))
    img = Image.open(io.BytesIO(response.content))
    byte_img = io.BytesIO()
    img.save(byte_img, "JPEG")
    yt_data['byte_img'] = byte_img
    yt_data['encoded_img_data'] = base64.b64encode(byte_img.getvalue())


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


@app.route('/ytform', methods=['GET', 'POST'])
def yt_form():
    form = YTDLForm()
    if form.validate_on_submit():
        download_and_convert_to_mp3(form=form)
        flash(f'Song {yt_data.get("filename")[:20]}...mp3 successfully downloaded', 'success')
        return redirect(url_for('home'))

    return render_template('yt_form.html', form=form, img_data=yt_data.get('encoded_img_data').decode('utf-8'))


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    form = YTGetInfoForm()
    if form.validate_on_submit():
        yt_data['url'] = form.url.data
        with youtube_dl.YoutubeDL() as ydl:
            yt_data['yt_info'] = ydl.extract_info(form.url.data, download=False)
        # Geting output file path and checking it already exists
        filename = re.sub(r'[^\x00-\x7f]', r'', yt_data['yt_info']["title"])  # Removing all non-ascii
        filename = re.sub('[^0-9a-zA-Z]+', '_', filename)  # Replacing all non-alpha-numeric with '_'
        yt_data['filename'] = filename
        yt_data['output_filepath_mp3'] = os.path.join(MUSIC_DIR, filename + '.mp3')

        print(f"\n{yt_data['output_filepath_mp3']}\n")

        if not os.path.exists(yt_data['output_filepath_mp3']):
            encoded_img()
            return redirect(url_for('yt_form'))
        else:
            flash(f'Song {yt_data.get("filename")[:20]}...mp3 already exists', 'warning')
            return redirect(url_for('home'))

    return render_template('yturl.html', form=form)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=4400)
