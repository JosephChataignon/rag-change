This repository contains a Retrieval-Augmented Generation (RAG) framework for efficient information retrieval and natural language generation. It is being developed at the University of Bern.
It is a fork of https://github.com/dsl-unibe-ch/rag-framework








# Install

These instructions are given for an install on Ubuntu. Other linux distributions and other OS have not been tested.

### Install code and dependencies
Clone the project `git clone https://github.com/JosephChataignon/rag-change`
Create a virtual environment `python -m venv venv`, and enter it `source venv/bin/activate`
Install python modules `pip install -r requirements.txt`
Note: you might still need to install additional package for LLM access. depending on the LLM provider you want to use.


### Settings
You need a `.env` file in the project directory, you can copy the sample file given as example:
`cp .env.sample .env`
You also need a local settings file. Create ragchange/config/local.yaml, or copy the defaults
settings file `cp ragchange/config/defaults.yaml ragchange/config/local.yaml`
Settings you write in local.yaml will override settings from defaults.yaml
Create directories logs and data (they're used but in .gitignore so it's safer to create them first) `mkdir logs data`


### Set up Django
create admin with `python manage.py createsuperuser`
apply migrations with `python manage.py migrate`
Run tests with `python3 manage.py test`


### Data ingestion
You need to ingest data before running the server.
`python3 


### Run the interface server

#### Run server locally
For local testing, run server with `python3 manage.py runserver`


#### Run server in production
For production, change the .env file:
- set DJANGO_DEBUG=False
- configure allowed hosts in the environment variable DJANGO_ALLOWED_HOSTS (comma separated)
- make sure to set a secure key in DJANGO_SECRET_KEY

Collect static files with `python manage.py collectstatic`
In your server config, add a location block to serve static files. For example, in nginx:
    location /static/ { # This parameter should match STATIC_URL from settings.py
        alias /home/change/rag-change/staticfiles/; # This parameter should match STATIC_ROOT from settings.py
    }


#### Example settings for production
You need a webserver and a WSGI to serve the application. Here are example files for a case using Nginx as 
webserver and Gunicorn as WSGI.

Nginx config file (usually in `/etc/nginx/sites-available/rag-change`):
```
server {
    listen 80;
    server_name example-url.com; # don't forget to authorize thsi URL in DJANGO_ALLOWED_HOSTS
    location /static/ {
        alias /home/user/rag-change/staticfiles/;
    }
    location / {
        # include proxy_params;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

For Gunicorn, first make sure gunicorn is installed `pip install gunicorn`.
Create a new config file `/etc/systemd/system/gunicorn.service` for the Gunicorn daemon,
and paste this inside (adapt parameters to your own machine).
```
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=your-username
Group=www-data
WorkingDirectory=/home/user/rag-change
Environment="PYTHONPATH=/home/user/rag-change"
ExecStart=/home/user/rag-change/venv/bin/gunicorn --workers 5 --bind 127.0.0.1:8000 --timeout 360 --chdir django-server ragchange.wsgi:application

[Install]
WantedBy=multi-user.target
```
Start the gunicorn service and enable it on boot with:
```
systemctl start gunicorn
systemctl enable gunicorn
systemctl restart nginx
```
You can check that Gunicorn and Nginx are running correctly:
```
sudo systemctl status gunicorn
sudo systemctl status nginx
```

