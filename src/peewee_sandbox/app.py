from peewee import *
from playhouse.shortcuts import *
db = SqliteDatabase('/Users/christophershroba/Developer/projects/todo/src/peewee_sandbox/data.sqlite')


class Person(Model):
    name = CharField()
    age = IntegerField()
    american = BooleanField()

    class Meta:
        database = db


db.connect()

db.create_tables([Person], safe=True)

chris = Person(
    name="Chris",
    age=21,
    american=True
)

chris.save()

Person.delete().where(Person.id<3).execute()
