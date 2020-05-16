##########################################
# Aire Logic tech test - Fergus McLellan #
##########################################

# import dash modules
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_table
import plotly.graph_objects as go

# import pandas and other modules for retrieving and processing song data
import numpy as np
import pandas as pd
import string
import requests
from requests.exceptions import HTTPError


global SONGS_DF
SONGS_DF = pd.DataFrame(columns=["Song title", "Song release year", "Artist","Number of words"])

app = dash.Dash()

server = app.server

app.layout = html.Div([
    html.H1('Lyric count by artist information - Fergus McLellan'),
    html.Div('Enter artist names, separated using a comma, e.g. Blur,Twenty one pilots:'),
    dcc.Input(
        id='artists-in',
        value='',
        style={'fontSize':28}
    ),
    html.Button(
        id='submit-button',
        n_clicks=0,
        children='Submit',
        style={'fontSize':28}
    ),
    html.P(html.Br()),
    html.Div(id='submitted-artists-out'),
    dash_table.DataTable(id='mean_table',
                        style_header={'backgroundColor': 'rgb(30, 30, 30)'},
                        style_cell={
                                'backgroundColor': 'rgb(00, 00, 128)',
                                'color': 'white',
                                'textAlign': 'left'},
                        style_table={
                            'width': '80%',
                            'minWidth': '50%',
                        },),
    html.P(html.Br()),
    dcc.Graph(id='song-wordcount-graph'),
    html.Div('NB If no lyrics can be found, songs are discarded. If release year is not found on musicbrainz, it is set to the year 2000'),
    html.P(html.Br()),
    html.Button(
        id='show-songs-button',
        n_clicks=0,
        children='Show songs',
        style={'fontSize':28}
    ),
    dash_table.DataTable(id='song_table',
                        filter_action="native",
                        sort_action="native",
                        sort_mode="multi",
                        style_cell={
                                'textAlign': 'left'},
                        style_table={
                            'maxHeight': '50ex',
                            'overflowY': 'scroll',
                            'width': '80%',
                            'minWidth': '50%',
                        },),
])

# functions to retrieve artist and song information
def get_songs_for_artist(artist):
    """
    Input: string, artist name
    Output: dictionary of unique songs found for the artist in musicbrainz,
            key is equal to the song name, and value is the song release year
    """

    url = "https://beta.musicbrainz.org/ws/2/release/?query=artist:" + artist + "%20AND%20primarytype:Single&fmt=json"

    song_dict = dict()

    try:
        response = requests.get(url)
        response.raise_for_status()
        jsonResponse = response.json()

        if "releases" in jsonResponse:
            print("songs found")
            for release in jsonResponse["releases"]:
                song_title = release["title"]
                if "date" in release:
                    if len(release["date"]) > 4:
                        song_date = int(release["date"][:4])
                    else:
                        song_date = int(release["date"])
                else:
                    # no date is listed for this release
                    song_date = 2000

                if song_title not in song_dict.keys() and "remix" not in song_title.lower():
                    song_dict[song_title] = song_date
        else:
            print("no songs found")

    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')

    return song_dict

def get_lyrics_for_song(input_row):
    """
    Input: row from the dataframe containing two strings, the artist name and the song name
    Output: lyrics for the song from api.lyrics.ovh, with punctuation removed
            (punctuation is removed here to make it easier to count the lyrics)
    """
    artist_name = input_row["Artist"]
    song_name = input_row["Song title"]
    url = "https://api.lyrics.ovh/v1/" + artist_name + "/" + song_name

    song_lyrics = ""
    cleaned_lyrics = ""

    try:
        response = requests.get(url)
        response.raise_for_status()
        jsonResponse = response.json()

        if "lyrics" in jsonResponse:
            print("lyrics found")
            song_lyrics = jsonResponse["lyrics"]
        else:
            print("no songs found")

    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')

    if len(song_lyrics) > 0:
        # Remove line breaks and punctuation
        for string_character in song_lyrics:
            # If char is not punctuation, add it to the result.
            if string_character not in string.punctuation:
                cleaned_lyrics += string_character
        cleaned_lyrics = cleaned_lyrics.split()
        number_of_words = len(cleaned_lyrics)
        # Convert lyrics to lowercase
        cleaned_lyrics = [word.lower() for word in cleaned_lyrics]
        cleaned_lyrics = " ".join(cleaned_lyrics)

    return cleaned_lyrics

def get_songs_and_lyrics_for_artists(artist_list):
    """
    Input: string containing a list of artist names
    Creates a dataframe with song details. Dataframe is created as a global so that it
    can be referenced more easily by Dash callbacks and Plotly components.
    """
    global SONGS_DF
    artist_list = artist_list.split(",")
    for artist in artist_list:
        if len(artist) > 0:
            song_dict = get_songs_for_artist(artist)
            this_artist_df = pd.DataFrame(list(song_dict.items()), columns=["Song title", "Song release year"])
            this_artist_df["Artist"] = artist
            print(this_artist_df)
            SONGS_DF = pd.concat([SONGS_DF, this_artist_df], ignore_index=True)
            SONGS_DF["lyrics"] = SONGS_DF.apply(get_lyrics_for_song, axis=1)
            # Drop songs which do not have any lyrics (or none found)
            rows_to_drop = SONGS_DF[ SONGS_DF["lyrics"] == "" ].index

            # Delete these row indexes from dataFrame
            SONGS_DF.drop(rows_to_drop , inplace=True)
            # Calculate the number of words in each song
            SONGS_DF["Number of words"] = SONGS_DF["lyrics"].apply(lambda x: len(x.split(" ")))
            print(SONGS_DF)

# Dash callbacks
# Callback to indicate status and artist names when "Submit" button is pressed
@app.callback(
    Output('submitted-artists-out', 'children'),
    [Input('submit-button', 'n_clicks')],
    [State('artists-in', 'value')])
def output(n_clicks, artists):
    output_text = ""
    if len(artists) > 0:
        output_text =  'Please wait - searching for song information for the artists: {}'.format(artists)
    return output_text

# Callback and function to fetch song details when "Submit" button is pressed
@app.callback(
    [Output('mean_table', 'data'),
    Output('mean_table', 'columns'),
    Output('song-wordcount-graph', 'figure')],
    [Input('submit-button', 'n_clicks')],
    [State('artists-in', 'value')])
def output(n_clicks, artists):
    mean_table_data=""
    mean_table_columns_list=""
    fig = ""
    if len(artists) > 0:
        global SONGS_DF
        SONGS_DF.drop(SONGS_DF.index, inplace=True)
        get_songs_and_lyrics_for_artists(artists)
        mean_table_data = []
        for artist in SONGS_DF['Artist'].unique():
            artist_mean = round(SONGS_DF[SONGS_DF['Artist']==artist]['Number of words'].mean(),1)
            artist_var = round(SONGS_DF[SONGS_DF['Artist']==artist]['Number of words'].var(),1)
            artist_std = round(SONGS_DF[SONGS_DF['Artist']==artist]['Number of words'].std(),1)
            mean_dict = dict()
            mean_dict['Artist'] = artist
            mean_dict['Mean number of words'] = artist_mean
            mean_dict['Variance'] = artist_var
            mean_dict['Standard deviation'] = artist_std
            mean_table_data.append(mean_dict)

        mean_table_columns_list = [
            {'id': 'Artist', 'name': 'Artist'},
            {'id': 'Mean number of words', 'name': 'Mean number of words'},
            {'id': 'Variance', 'name': 'Variance'},
            {'id': 'Standard deviation', 'name': 'Standard deviation'},
        ]

        color_dict = dict()
        for artist in SONGS_DF['Artist'].unique():
            color = 'rgb(' + str(np.random.randint(255)) + ',' + str(np.random.randint(255)) + ',' + str(np.random.randint(255)) + ')'
            color_dict[artist] = color  
        SONGS_DF['color'] = SONGS_DF['Artist'].map(color_dict)
        fig = go.Figure(
                data = [go.Scatter(
                x=SONGS_DF['Song release year'],
                y=SONGS_DF['Number of words'],
                text=SONGS_DF['Song title'],
                textposition='top center',
                mode='markers+text',
                marker=dict(
                    color=SONGS_DF['color'],
                    )
                )],
                layout = go.Layout(
                title = 'Plotly scatter plot of number of words in a song vs year',
                xaxis = {'title': 'Release year'},
                yaxis = {'title': 'Number of words'},
                hovermode='closest'
                )
            )
    return mean_table_data,mean_table_columns_list,fig

# callback and function to display song details when "Show songs" button is pressed
@app.callback(
    [Output('song_table', 'data'),
    Output('song_table', 'columns')],
    [Input('show-songs-button', 'n_clicks')],
    [State('artists-in', 'value')])
def output(n_clicks, artists):
    no_lyrics_df = ""
    song_table_data = dict()
    song_table_columns_list = []

    no_lyrics_df = SONGS_DF[['Artist','Song title','Song release year','Number of words']].sort_values(by=['Song release year'])
    song_table_data = no_lyrics_df.to_dict('rows')
    for col in no_lyrics_df.columns:
        column_dict = dict()
        column_dict['id'] = col
        column_dict['name'] = col
        song_table_columns_list.append(column_dict)
    print(song_table_columns_list)
    print(song_table_data)
    return song_table_data,song_table_columns_list

if __name__ == '__main__':
    app.run_server()

