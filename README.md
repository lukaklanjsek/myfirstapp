Installation:
1. ```git pull```
2. ```sudo apt install python3-venv```
2. ```python3 -m venv env``` Create new virtual environment for the application
3. ```source env/bin/activate```
5. ```pip install -r requirements.txt```
6. Minimal settings for personal use:
7. copy .env.example into same folder as manage.py and rename into .env
8. edit .env file,  generate new secret key, for example from "https://djecrety.ir/" and put it in the "your-secret-key-here-generate-new-one" (no space between "=" and your new secret key)
9. ```python manage.py migrate```
10. ```python manage.py createsuperuser``` and follow instructions in the terminal (email can be blank)
11. ```python manage.py runserver```
Congratulations, this is it!