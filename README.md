# TODO

This is my personal To Do List app.
I tried several other services and found that
none of them worked well for me, and I wanted
a service that I had complete control over, so I created this.

Screenshot here: ![Screenshot of app](http://i.imgur.com/FmoheCB.png)

Implemented:

  * Task creation, deletion, update
  * Persistence to SQLite3 DB
  * Task categories
  * "Move to Today" button

Up next:

  * Testing!  Need to determine how to dynamically set Database so I'm not manipulating prod db ([MyStack Overflow Question Here](http://stackoverflow.com/questions/41305870/how-can-i-dynamically-set-the-sqlite-database-file-in-peewee))
  * Dockerize it!
  * Add multiple users with login to prepare for release