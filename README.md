# Hacker News Project

## Installation and Setup

### Production

### Development

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
