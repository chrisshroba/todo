import os

from src.models import *

tasks = [
    'Read that article',
    'Click [[https://www.accelebrate.com/blog/using-defaultdict-python/|this link]]',
    'Watch [[https://www.youtube.com/watch?v=--hsVknT1c0|this video]]',
    'Write that post',
    'Build that thing',
    'Do that thing that takes lots and lots and lots of words to explain, '
    'thus causing this particular todo list item to be particularly '
    'long, and probably running over onto multiple lines and taking up the '
    'full width of the app',
    'Go to that place',
    'Talk to that person',
    'Read that book',
    'Design that page',
    'Code that program',
    'Learn that thing',
    'Eat that food'
]

# create_task("Today", heading=1)
# map(create_task, tasks[:5])
# create_task("Tomorrow", heading=1)
# map(create_task, tasks[5:])

# for i in range(8):
#     create_task("Task {}".format(i), order_id=i)

i = 0


def create_tasks(n):
    global i
    for _ in range(n):
        create_task("Task {}".format(i))
        i += 1


create_task("Done", heading=1)
create_tasks(4)

create_task("Today", heading=1)
create_tasks(4)

create_task("Tomorrow", heading=1)
create_tasks(4)

create_task("Eventually", heading=1)
create_tasks(4)

# with open("/Users/christophershroba/Downloads/todoi", encoding='utf-8') as f:
#     tasks = f.read().split("\n")
#     for task in tasks:
#         create_task(task)
