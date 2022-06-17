# PigeonGo

## Installation
### App is hosted on live. [view demo](https://PigeonGo.herokuapp.com)
### PigeonGo is an opensource email client which works with popular email services like Gmail and outlook.

### Steps to run:

- **First create virtual environment and activate it.**

  - **Install virtual environment**
  - `sudo pip3 install virtualenv`
  - **Create virtual environment**
  - `virtualenv venv`
  - **Activate virtual environment**
  - `. venv/bin/activate`

- **Install dependencies**

  - `python3 -r requirements.txt`

- **Run the program**
  - `python3 app.py`
- **Explore App**
  - Open browser and type http://127.0.0.1:5000
  - There you go!
  
- **To stop the program Press** </br>
  - For windows and linux - `ctrl + c`

- **Deactivate the virtual environment**
  - `deactivate`


## Features
- ### Read Mails
- ### Download attachments
- ### Send Mail with attachments.
- ### Secure - sockets are wrapped inside SSL context.
- ### User friendly GUI.


## Issues
- ### For outlook, attachments aren't getting mailed along with body.


## TODO:
- ### Improve parser.
- ### Store opened mails as cache on server and delete them once user is logged out.
- ### Add more features:
    - ### Mark mail read/unread
    - ### Delete mail
    - ### check for new mail
    - ### Unsubscribe newsletters
- ### Make code more modular.
- ### Improve frontend


## Reference:
RFC [3501](https://datatracker.ietf.org/doc/html/rfc3501), [5321](https://datatracker.ietf.org/doc/html/rfc5321), [821](https://datatracker.ietf.org/doc/html/rfc821), [2554](https://datatracker.ietf.org/doc/html/rfc2554), [2487](https://datatracker.ietf.org/doc/html/rfc2487)