# al_techtest
Interact with APIs to identify the average number of words in an artists songs

# Setup
Create and activate new Python virtual environment:
python3 -m virtualenv test
cd test
source bin/activate

Clone repository into current directory:

git clone https://github.com/fergusmclellan/al_techtest.git

cd al_techtest/

Install python libraries:

pip install -r requirements.txt

Launch web server using gunicorn:

gunicorn al_song_lyrics:server -b 0.0.0.0:8050
(change port as required)

Or to run directly using the Dash/Flask web server
1) comment out the line "server = app.server" in al_song_lyrics.py
2) Run: python al_song_lyrics.py

(Gunicorn can take slightly longer to startup.)

# A running copy of the application is available
A working copy of the application is currently running on Heroku:
https://al-song-lyrics.herokuapp.com/
Please note, Heroku is free, and the application can be slightly sluggish, so please bear with it.

# Usage
1) Open your web browser, and point it at the IP address/name of your web server and the port specified 
2) Simply enter the artist or artists into the text box and click on the Submit button. 
3) If entering more than one artist in the text box, separate artist names using a comma.
4) If multiple artists are entered, the dashboard will take longer to retrieve artist and lyric information.

Output:
1) Mean number of lyrics per artist, variance and standard deviation are displayed in the first table.
2) The Plotly interactive scatter plot displays the number of words per song versus the release year.
3) More information on songs can be viewed by clicking on the Show songs button.
