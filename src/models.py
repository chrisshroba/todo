from pprint import pprint

from peewee import *
from playhouse.shortcuts import model_to_dict

from datetime import datetime
import os
from collections import defaultdict, OrderedDict

DB_PATH = '/Users/christophershroba/Developer/projects/todo/database.sqlite'

db = SqliteDatabase(DB_PATH)
db.connect()


class Task(Model):
    create_timestamp = DateTimeField()
    done_timestamp = DateTimeField(null=True)
    heading = IntegerField()
    order_id = IntegerField(db_column='order_id')
    text = TextField()

    class Meta:
        db_table = 'Task'
        database = db

    def to_dict(self):
        return model_to_dict(self)


db.create_tables([Task], safe=True)
print("Created tables")


def create_task(text,
                heading=0,
                create_timestamp=None,
                done_timestamp=None,
                order_id=None,
                silent=False):
    if not silent:
        log("Creating task '{}', heading={}".format(text, heading))
    if not create_timestamp:
        create_timestamp = datetime.now()
    if order_id is None:
        order_id = get_max_order_id() + 1
    task = Task(
        text=text,
        heading=heading,
        create_timestamp=create_timestamp,
        done_timestamp=done_timestamp,
        order_id=order_id
    )

    task.save()

    return task.to_dict()


def get_all_tasks():
    tasks = Task.select().order_by(Task.order_id)
    tasks_dicts = list(map(model_to_dict, tasks))
    return tasks_dicts


def get_home_tasks():
    tasks = get_home_tasks_query()
    tasks_dicts = list(map(model_to_dict, tasks))
    return tasks_dicts


def get_home_tasks_query():
    now = datetime.now()
    today_midnight = datetime(now.year, now.month, now.day)
    tasks = Task.select().where(
        (Task.done_timestamp > today_midnight) | (Task.done_timestamp.is_null())
    ).order_by(Task.order_id)
    return tasks



def get_task(item_id):
    try:
        return model_to_dict(
            Task.select().where(id=item_id).get()
        )
    except DoesNotExist:
        return None


def update_task_text(item_id, text):
    try:
        task = Task.select().where(Task.id == item_id).get()
        log("Updating task {} text from '{}' to '{}'".format(item_id, task.text,
                                                             text))
        task.text = text
        task.save()
        return model_to_dict(task)
    except DoesNotExist:
        err("Updating task {} text to '{}', but task not found".format(item_id,
                                                                       text))
        return None


def remove_task(item_id):
    try:
        task = Task.select().where(Task.id == item_id).get()
        log("Removing task {} with text {}".format(item_id, task.text))
        task.delete_instance()
        return True
    except DoesNotExist:
        err("Removing task {}, but task not found".format(item_id))
        return False


def complete_task(item_id, completion_time=None):
    try:
        task = Task.select().where(Task.id == item_id).get()
        task.done_timestamp = completion_time or datetime.now()
        task.save()
        log("Marking task {} with text '{}' as done".format(item_id, task.text))
        move_to_end_of_heading(task.order_id, "Done")
        return True
    except DoesNotExist:
        err("Tried marking task {} as done, but task not found".format(item_id))
        return False


# def execute_sql(sql):
#     db.execute(sql)


def get_max_order_id():
    max_order_id = Task.select(fn.MAX(Task.order_id)).scalar()
    if max_order_id is None:
        return -1
    return int(max_order_id)


def fix_order():
    tasks = get_home_tasks()
    for index, task in enumerate(tasks):
        task['order_id'] = index
    delete_home_tasks()
    create_from_list(tasks, silent=True)


def move_before(id_to_move, next_id):
    log("Moving task {} to be before task {}".format(id_to_move, next_id))
    # Double all order_id's
    Task.update(order_id=Task.order_id * 2).execute()
    task_to_move = Task.select().where(Task.order_id == id_to_move * 2).get()
    task_to_move.order_id = next_id * 2 - 1
    task_to_move.save()
    fix_order()


def delete_all_tasks():
    log('Deleting ALL tasks')
    Task.delete().execute()


def delete_home_tasks():
    log('Deleting ALL tasks')
    now = datetime.now()
    today_midnight = datetime(now.year, now.month, now.day)
    tasks = Task.delete().where(
        (Task.done_timestamp > today_midnight) | (Task.done_timestamp.is_null())
    ).execute()


def create_from_list(l, silent=False):
    # timer(0)
    Task.insert_many(l).execute()


    # for index, task in enumerate(l):
    #     order_id = task.get('order_id', None)
    #     create_timestamp = task.get('create_timestamp', None)
    #     done_timestamp = task.get('done_timestamp', None)
    #     heading = task.get('heading', None)
    #     text = task.get('text', None)
    #     create_task(text, heading, create_timestamp, done_timestamp, order_id,
    #                 silent=silent)
    # timer()


def get_headings(include_uncategorized=True):
    tasks = Task.select().where(Task.heading == 1)
    tasks_dicts = list(map(model_to_dict, tasks))
    if include_uncategorized and tasks_dicts[0]['order_id'] != 0:
        tasks_dicts = [{
            'text': "Uncategorized",
            'heading': 1
        }] + tasks_dicts
    return tasks_dicts


def get_categorized_tasks():
    tasks = get_all_tasks()
    categories = [task['text'] for task in get_headings()]
    categorized_tasks = {heading: [] for heading in categories}
    cur_cat = 'Uncategorized'
    for task in tasks:
        if task['heading'] == 1:
            cur_cat = task['text']
        else:
            categorized_tasks[cur_cat].append(task)
    ordered_cat_tasks = OrderedDict()
    for category in categories:
        ordered_cat_tasks[category] = categorized_tasks[category]
    return ordered_cat_tasks


def move_to_end_of_heading(order_id, heading):
    headings = get_headings()
    heading_task = Task.select().where(
        (Task.heading == 1) & (Task.text == heading)).get()
    print(heading_task)
    heading_labels = [heading['text'] for heading in headings]
    if heading not in heading_labels:  # TODO change this line
        raise Exception("Heading '{}' does not exist".format(heading))
    cat_tasks = get_categorized_tasks()
    num_tasks = len(cat_tasks[heading])
    move_before(order_id, heading_task.order_id + num_tasks + 1)


def move_task_to_today(task_id):
    order_id = Task.select().where(Task.id == task_id).get().order_id
    move_to_end_of_heading(order_id, "Today")
    return True


def log(s):
    print(s)


def err(s):
    print(s)


last_call = None


def timer(reset=None):
    global last_call
    if reset is not None:
        last_call = datetime.now()
        print("Starting timer")
    else:
        last_call = last_call or datetime.now()
        now = datetime.now()
        print("Timer value: {}".format(now - last_call))
        last_call = now


if __name__ == '__main__':
    # pprint(get_all_tasks_with_headings())
    # test_method2()
    pass
