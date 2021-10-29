# Introduction

Deadline is a web application for solving programming challenges
![Deadline Logo](http://i.imgur.com/dfZ5P8A.jpg)

## Currently going through a re-design. Here is a taste of things to come:
![Redesign Sample](http://i.imgur.com/vYst0CJ.jpg)

## Old design
<img src="/sample.gif?raw=true" width="1000px">

### Still a work in progress
Supported languages:
- Python
- Go
- Rust
- Kotlin
- C++
- Ruby
<br>
<div style="display: flex; flex-direction: row;">
<img style="display: inline; width: 200px; height: 200px; margin-right: 50px;" src="https://www.python.org/static/opengraph-icon-200x200.png" width="75" height="75">
<img style="display: inline; width: 200px; height: 200px; margin-right: 50px;" src="https://www.rust-lang.org/logos/rust-logo-512x512.png" width="75" height="75">
<img style="display: inline; width: 200px; height: 200px; margin-right: 50px;" src="https://www.unixstickers.com/image/cache/data/stickers/golang/golang.sh-600x600.png" width="75" height="75">
<img style="display: inline; width: 200px; height: 200px; margin-right: 50px;" src="http://www.freeiconspng.com/uploads/c--logo-icon-0.png" width="75" height="75">
<img style="display: inline; width: 200px; height: 200px; margin-right: 50px;" src="https://upload.wikimedia.org/wikipedia/commons/b/b5/Kotlin-logo.png" width="75" height="75">
<img style="display: inline; width: 200px; height: 200px; margin-right: 50px;" src="https://upload.wikimedia.org/wikipedia/commons/f/f1/Ruby_logo.png" width="75" height="75">
</div>

Created using the Django REST Framework and React.js

### Authors
- Plamen https://github.com/nemalp
- Stanislav https://github.com/Enether


# Up & Running

### How to get the backend working

First, you need to have **Python 3.6** installed, as that is what we use in this project.

Install all the requirements
`pip install -r requirements.txt`

You will also need to install and run a RabbitMQ server which we use for notifications. Here are some [instructions](https://www.rabbitmq.com/download.html)

For Django to connect with the database you need to have a running PostgreSQL server. Start one and either hardcode the username, password, database name and host in settings.py or be a proper gentleman and create a .env file.
Said `.env` file should be in `/deadline/deadline_/deadline/.env` _(what the fuck?)_, right beside the `settings.py` folder.
Enter the following in it, replacing the values with your local ones.
```
DB_USER=root
DB_NAME=deadline
DB_HOST=localhost
DB_PASS=iliketurtles
RABBITMQ_HOST=localhost
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest
```

Then run the migrations
`python manage.py migrate`

You're done!
`python manage.py runserver`
