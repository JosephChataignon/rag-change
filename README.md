This repository contains a Retrieval-Augmented Generation (RAG) framework for efficient information retrieval and natural language generation. It is being developed at the University of Bern.
It is a fork of https://github.com/dsl-unibe-ch/rag-framework








# Install

### Install code and dependencies
Clone the project `git clone https://github.com/JosephChataignon/rag-change`
Create a virtual environment `python -m venv venv`, and enter it `source venv/bin/activate`
Install python modules `pip install -r requirements.txt`


### Settings
You need a `.env` file in the project directory, you can copy the sample file given as example:
`cp .env.sample .env`
You also need a local settings file. Create ragchange/config/local.yaml, or copy the defaults
settings file `cp ragchange/config/defaults.yaml ragchange/config/local.yaml`
Settings you write in local.yaml will override settings from defaults.yaml


### Set up Django
create admin with `python manage.py createsuperuser`
apply migrations with `python manage.py migrate`
Run tests with `python3 manage.py test`


### Run server locally
For local testing, run server with `python3 manage.py runserver`


### Run server in production
For production, change the .env file:
- set DJANGO_DEBUG=False
- configure allowed hosts in the environment variable DJANGO_ALLOWED_HOSTS (comma separated)
- make sure to set a secure key in DJANGO_SECRET_KEY

Collect static files with `python manage.py collectstatic`
In your server config, add a location block to serve static files. For example, in nginx:
    location /static/ { # This parameter should match STATIC_URL
        alias /home/change/rag-change/staticfiles/; # This parameter should match STATIC_ROOT
    }







