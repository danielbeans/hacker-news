"""
Interface for WSGI server to hook onto. Can call either the Flask app object or create_app

Variables:
    app
"""
from hacker_news import create_app

app = create_app()
