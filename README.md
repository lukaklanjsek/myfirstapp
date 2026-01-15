# Songs and singers participation tracker

## Installation

1. ```sudo apt install python3-venv```
2. ```python3 -m venv venv``` Create new virtual environment for the application
3. ```source venv/bin/activate```
4. ```pip install -r requirements.txt```

Minimal settings for running the app locally:

6. Copy .env.example to .env
7. Edit .env file, generate a new 32-character secret key and put it in the
   "your-secret-key-here-generate-new-one"
8. ```python manage.py migrate```
9. ```python manage.py createsuperuser``` and follow instructions in the
   terminal (email can be blank)
10. ```python manage.py runserver```

Congratulations, this is it!

## Requirements

- Python 3.14+

## Usage

### Managing songs

Add a composer and a poet for your new song. You can also add them alter, but
adding them first makes managing songs cleaner.

- Sections with asterisk are mandatory.
- ID of the song is inputted manually, for when your archive is non-sequential.
- There is an alphabetical non-searchable drop-down menu for previously created
  composers and poets.

There is a connection between each song to its composer, poet and dates of
rehearsals.

### Managing members

You can add members that participate on your rehearsals.

Ticker "is active" is important for listing the member:

- at the top of members page;
- at creation of a new rehearsal;

### Managing rehearsals

Rehearsals connect songs, active members and a calendar.

In the list of rehearsals there is a preview of songs related to it and names of
active members that are not present.

- Members with "active" status appear with a checkbox for their rehearsal
  participation.
- Songs have a search-drop-down menu; you can search among song titles or
  composer names.

## Support

Feel free to open issue on github.

## Licence

Apache 2.0.

## Known issues

- Order of the songs in specific rehearsal is not preserved yet.
- Activity of the members is not yet connected to the status of "is active".