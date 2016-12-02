from pprint import pprint

from pony.orm import *
from datetime import datetime
import os
from collections import defaultdict, OrderedDict

DB_PATH = '/Users/christophershroba/Developer/projects/todo/database.sqlite'
# os.remove(DB_PATH)


db = Database()


class Task(db.Entity):
    text = Required(unicode)
    heading = Required(int)
    create_timestamp = Required(datetime)
    done_timestamp = Optional(datetime)
    order_id = Required(int, volatile=True)

    def to_dict(self):
        """
        Need this or else `update_task_text` doesn't work
        :return:
        """
        return {
            'id': self.id,
            'text': self.text,
            'heading': self.heading,
            'create_timestamp': self.create_timestamp,
            'done_timestamp': self.done_timestamp,
            'order_id': self.order_id
        }


# sql_debug(True)
db.bind('sqlite',
        DB_PATH,
        create_db=True)
db.generate_mapping(create_tables=True)


@db_session
def create_task(text,
                heading=0,
                create_timestamp=None,
                done_timestamp=None,
                order_id=None):
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

    return task.to_dict()


@db_session
def get_all_tasks():
    tasks = Task.select().order_b y(Task.order_id)
    tasks_dicts = list(map(Task.to_dict, tasks))
    return tasks_dicts


@db_session
def get_task(item_id):
    try:
        return Task[item_id].to_dict()
    except core.ObjectNotFound:
        return None


@db_session
def update_task_text(item_id, text):
    try:
        task = Task[item_id]
        log("Updating task {} text from '{}' to '{}'".format(item_id, task.text,
                                                             text))
        task.text = text
        return task.to_dict()
    except core.ObjectNotFound:
        err("Updating task {} text to '{}', but task not found".format(item_id,
                                                                       text))
        return None


@db_session
def remove_task(item_id):
    try:
        task = Task[item_id]
        log("Removing task {} with text {}".format(item_id, task.text))
        task.delete()
        return True
    except core.ObjectNotFound:
        err("Removing task {}, but task not found".format(item_id))
        return False


@db_session(serializable=True)
def complete_task(item_id, completion_time=None):
    try:
        task = Task[item_id]
        task.done_timestamp = completion_time or datetime.now()
        log("Marking task {} with text '{}' as done".format(item_id, task.text))
        move_to_end_of_heading(task.order_id, "Done")
        return True
    except core.ObjectNotFound:
        err("Tried marking task {} as done, but task not found".format(item_id))
        return False


@db_session
def execute_sql(sql):
    db.execute(sql)


@db_session
def get_max_order_id():
    max_order_id = max(t.order_id for t in Task)
    if max_order_id is None:
        return -1
    return max_order_id


@db_session
def fix_order():
    tasks = get_all_tasks()
    for index, task in enumerate(tasks):
        task['order_id'] = index
    delete_all_tasks()
    create_from_list(tasks)


@db_session
def move_before(id_to_move, next_id):
    log("Moving task {} to be before task {}".format(id_to_move, next_id))
    # Double all order_id's
    execute_sql("UPDATE Task SET order_id=order_id*2")
    task_to_move = select(
        task for task in Task if task.order_id == id_to_move * 2).first()
    # if next_id > id_to_move:
    #     next_id += 1
    task_to_move.order_id = next_id * 2 - 1
    fix_order()


@db_session
def delete_all_tasks():
    log('Deleting ALL tasks')
    execute_sql("DELETE FROM Task")


@db_session
def create_from_list(l):
    for index, task in enumerate(l):
        order_id = task.get('order_id', None)
        create_timestamp = task.get('create_timestamp', None)
        done_timestamp = task.get('done_timestamp', None)
        heading = task.get('heading', None)
        text = task.get('text', None)
        create_task(text, heading, create_timestamp, done_timestamp, order_id)


@db_session
def get_headings(include_uncategorized=True):
    tasks = select(task for task in Task if task.heading == 1)
    tasks_dicts = list(map(Task.to_dict, tasks))
    if include_uncategorized and tasks_dicts[0]['order_id'] != 0:
        tasks_dicts = [{
            'text': "Uncategorized",
            'heading': 1
        }] + tasks_dicts
    return tasks_dicts


@db_session
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


# NOT USING WITH CONTEXT MANAGER.  UNCOMMENT AND FIX WHEN AK RESPONDS
@db_session(serializable=True)
def move_to_end_of_heading(order_id, heading):
    headings = get_headings()
    heading_task = select(task for task in Task if
                          task.heading == 1 and task.text == heading).first()
    print(heading_task)
    heading_labels = [heading['text'] for heading in headings]
    if heading not in heading_labels:  # TODO change this line
        raise Exception("Heading '{}' does not exist".format(heading))
    cat_tasks = get_categorized_tasks()
    num_tasks = len(cat_tasks[heading])
    print("num: {}".format(num_tasks))
    print("orderid: {}".format(order_id))
    print("h ord: {}".format(heading_task.order_id))
    move_before(order_id, heading_task.order_id + num_tasks + 1)


# def move_to_end_of_heading(order_id, heading):
#     num_tasks = None
#     with db_session:
#         headings = get_headings()
#         heading_task = select(task for task in Task if
#                               task.heading == 1 and task.text == heading).first()
#         print(heading_task)
#         heading_labels = [heading['text'] for heading in headings]
#         if heading not in heading_labels:  # TODO change this line
#             raise Exception("Heading '{}' does not exist".format(heading))
#         cat_tasks = get_categorized_tasks()
#         num_tasks = len(cat_tasks[heading])
#     move_before(order_id, heading_task.order_id + num_tasks + 1)


def log(s):
    print(s)


def err(s):
    print(s)


@db_session
def test_method():
    tasks = list(map(Task.to_dict, Task.select()))
    db.execute("UPDATE Task SET order_id=order_id*2")
    task_to_move = select(task for task in Task if task.order_id == 6).first()
    task_to_move.order_id = 4


@db_session
def test_method2():
    execute_sql("UPDATE Task SET order_id=order_id*2")
    task_to_move = select(
        task for task in Task if task.order_id == 6).first()
    task_to_move.order_id = 1
    Task.select()[:]


if __name__ == '__main__':
    # pprint(get_all_tasks_with_headings())
    # test_method2()
    pass