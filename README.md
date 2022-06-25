# PigeonGo
### App is hosted on live. [view demo](https://PigeonGo.herokuapp.com)

![PigeonGo](./screenshots/1.png?raw=true "Home")
![PigeonGo](./screenshots/5.png?raw=true "Headers")
![PigeonGo](./screenshots/9.png?raw=true "Write Mail")

## Installation

### Steps to run (Linux):

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

- **Deactivate the virtual environment**
  - `deactivate`


## Features
- ### Read Mails
- ### Download attachments
- ### Send Mail with attachments.
- ### Secure - sockets are wrapped inside SSL context.
- ### User friendly GUI.


## TODO:
- ### Improve [parser](https://github.com/pathadeTush/PigeonGo/blob/01fddf086f73075c76b08d60f265856186cab5a4/IMAP/main.py#L292).
- ### Store opened mails as cache on server and delete them once user is logged out.
- ### Add more features:
    - ### Mark mail read/unread
    - ### Delete mail
    - ### check for new mail
    - ### Unsubscribe newsletters
- ### Improve frontend


## Reference:
RFC [3501](https://datatracker.ietf.org/doc/html/rfc3501), [5321](https://datatracker.ietf.org/doc/html/rfc5321), [821](https://datatracker.ietf.org/doc/html/rfc821), [2554](https://datatracker.ietf.org/doc/html/rfc2554), [2487](https://datatracker.ietf.org/doc/html/rfc2487)