# Hacker News Project

## Description

Hacker News Project is a Flask application that displays the top 20 stories from the [Hacker News API](https://hackernews.api-docs.io/v0/overview) along with details and comments for each story. Users can signup or login using their email or Google OAuth, and then can like/dislike stories, view their profile information, and view their liked/disliked stories. If the User has an admin role, the User can visit an admin panel where the Admin can view every liked/disliked story, edit every story’s keywords, delete a story, and refresh the top 20 stories’ comments.

### File Structure

```sh
.
├── README.md
├── app.py                      # Entry point for the application
├── configs                     # Config files for VM
│   ├── gunicorn.config
│   ├── nginx.config
│   └── ssh.config
├── hacker_news
│   ├── __init__.py
│   ├── db
│   │   ├── __init__.py
│   │   ├── db.py               # Creates database object
│   │   └── models.py           # Defines all of the database tables and models
│   ├── static
│   │   ├── js
│   │   │   ├── bootstrap.min.js
│   │   │   └── utilities.js    # All javascript for the templates
│   │   └── styles
│   │       ├── bootstrap.min.css
│   │       └── index.css       # Custom CSS for application templates
│   ├── tasks
│   │   └── __init__.py         # Runs a task that updates story data at intervals
│   ├── templates               # All the HTML that Flask serves
│   │   ├── admin.html
│   │   ├── base.html
│   │   ├── edit-story.html
│   │   ├── home.html
│   │   ├── profile.html
│   │   └── story.html
│   ├── utilities
│   │   ├── __init__.py
│   │   ├── login_manager.py    # Utilities for handling login and sessions
│   │   └── news_api.py         # Utilities for querying Hacker News API and database
│   └── views                   # Routes for each section of the website
│       ├── __init__.py
│       ├── admin.py
│       ├── home.py
│       ├── login.py
│       ├── profile.py
│       └── story.py
└── requirements.txt            # List of pip packages this application requires
```

## Installation and Setup

### Setup

To setup this project we require a [Auth0](https://auth0.com) application account.

1. Obtain Auth0 credentials and place them in an `.env` file in the root of the project along with a long random string for the Secret Key.

    ```py
    # .env

    AUTH0_CLIENT_ID=
    AUTH0_CLIENT_SECRET=
    AUTH0_DOMAIN=something.us.auth0.com
    APP_SECRET_KEY=abcdefghijklmnopqrstuvwxyz
    ```

2. Create a `config.json` and assign the folder the database will be created in.

    ```py
    # .config.json

    {
    "DEBUG": true,
    "ADMIN_LIST": ["example@abcd.com", ], # Emails the server will make admin on login/signup
    "SQLALCHEMY_DATABASE_URI": "sqlite:///path/to/database.db"
    }
    ```

3. Create a Python virtual environment and activate it.

    ```bash
    python -m venv env
    . env/bin/activate
    ```

4. Install required packages from requirements.txt

    ```bash
    pip install -r requirements.txt
    ```

### Development

To run this project we use the [Flask development server](https://flask.palletsprojects.com/en/2.2.x/server).

Assuming you have [setup](#setup) the project, run the development server

```bash
flask --debug run
```

### Production

To run this project in a production setting, we use [Gunicorn](https://gunicorn.org).

## Mid-semeseter Project Evaluation

**Due: 11.4.22**

### Updates and Upgrades

When we need to upgrade or update our application or machine, we can point to another VM in our Azure group.

### Config

Configurations for the machine can be found at `/configs`.

## Homework 1

**Due: 10.20.22**

### How `curl yourdomain.com` works

Curl is a Linux command line tool that allows you to interact with a server using multiple supported protols. When using the command with a domain name like `curl google.com` it defaults to `HTTP` and sends a request to the server and displays the result.

Internally, curl prepares a GET request to send to a server. Since it doesn't know what IP the domain points to, it uses a DNS to resolve the domain into an IP address it can request data from. Since we didn't specify a protocol in the beginning of the url (http://, sftp:// etc.), it defaults to `HTTP`, which serves data by default on port 80. Curl sends the GET request to the IP address of the server on port 80 (ex: 142.250.105.113:80) and recieves an HTML document and other resources. If we specify the protocol to be `HTTPS`, `curl https://google.com`, then it will use port 443 instead.

### How Flask serves web pages on a server

To connect a Flask application to nginx (which is the web server running on our machine that listens on port 80 and 443 per configuration), we have to use a WSGI server such as Gunicorn. WSGI (Web Srver Gateway Interface) is a defined interface for Python applications to commuincate with a web server. The flow of this process is as follows: first nginx recives an `HTTP(s)` request and then looks to the WSGI server to resolve what data to respond with. The WSGI server calls an object that we initialize in our Python application and sends the request data using this object. The Python app does its magic and returns response data using this same object, which the WSGI server passes along to nginx for it to serve back to the users browser.

### How we secure our server

The first level of security starts at what ports we will allow our machine to be accessed from. We created VM using Microsoft Azure, and when setting it up we configured it to only accept requests on ports 80, 443, and 22 for `HTTP` `HTTPS` and `SSH`.

We then specify some configurations for connecting to those ports. For `SSH` we specified to only allow connections using a certificate instead of allowing access with a password. For `HTTP` and `HTTPS` we use our nginx configuration to redirect any connections from port 80 to port 443 and we use Certbot to create and add our SSL certifcates to be able to use `HTTPS`.

There are other ways we secure our machine and our application as well. We whitelist our computers IP address on our Azure machine over SSH so only we can SSH onto it. A way we secure our application is using a `.env` file to store keys that we use to access services like auth0 or for providing unique keys for encryption in our application like when we use session cookies.
