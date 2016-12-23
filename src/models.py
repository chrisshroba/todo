from peewee import *
from playhouse.shortcuts import model_to_dict

from datetime import datetime
from collections import OrderedDict
import os

DB_PATH = '/Users/christophershroba/Developer/projects/todo/database.sqlite'
DB_PATH = os.path.join(os.path.dirname(
    os.path.dirname(__file__)), 'database.sqlite')

db = SqliteDatabase(DB_PATH)


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


db.connect()
db.create_tables([Task], safe=True)


class TaskController(object):
    """
    Manage tasks
    """

    def create_task(self,
                    text,
                    heading=0,
                    create_timestamp=None,
                    done_timestamp=None,
                    order_id=None,
                    silent=False):
        """
        Create a new text
        :param text: Text of task
        :param heading: 0 if normal, 1 if heading
        :param create_timestamp: When the task was created.  Leave None for now
        :param done_timestamp: When the task was marked done.  None by default
        :param order_id: Where this task should be placed
        :param silent: Whether to log this creation
        :return: Task created
        """
        if not silent:
            log("Creating task '{}', heading={}".format(text, heading))
        if not create_timestamp:
            create_timestamp = datetime.now()
        if order_id is None:
            order_id = self.get_max_order_id() + 1
        task = Task(
            text=text,
            heading=heading,
            create_timestamp=create_timestamp,
            done_timestamp=done_timestamp,
            order_id=order_id
        )

        task.save()

        return task.to_dict()

    def get_all_tasks(self):
        """
        Get all tasks
        :return: list of tasks
        """
        tasks = Task.select().order_by(Task.order_id)
        tasks_dicts = list(map(model_to_dict, tasks))
        return tasks_dicts

    def get_home_tasks(self):
        """
        Get all home tasks

        Note: "Home tasks" refers to all tasks that are
        either not done or have been marked as done today.
        :return: list of home tasks
        """
        tasks = self.get_home_tasks_query()
        tasks_dicts = list(map(model_to_dict, tasks))
        return tasks_dicts

    def get_home_tasks_query(self):
        """
        Get home task query
        :return: Query for home tasks
        """
        now = datetime.now()
        today_midnight = datetime(now.year, now.month, now.day)
        tasks = Task.select().where(
            (Task.done_timestamp > today_midnight) | (
                Task.done_timestamp.is_null())
        ).order_by(Task.order_id)
        return tasks

    def get_task(self, item_id):
        """
        Return task or None if task does not exist
        :param item_id: ID of task to fetch
        :return: Task fetched
        """
        try:
            return model_to_dict(
                Task.select().where(id=item_id).get()
            )
        except DoesNotExist:
            return None

    def update_task_text(self, item_id, text):
        """
        Update the text of a task
        :param item_id: ID of task to update
        :param text: Task text
        :return: task or None if task not found
        """
        try:
            task = Task.select().where(Task.id == item_id).get()
            log("Updating task {} text from '{}' to '{}'".format(item_id,
                                                                 task.text,
                                                                 text))
            task.text = text
            task.save()
            return model_to_dict(task)
        except DoesNotExist:
            err("Updating task {} text to '{}', but task not found".format(
                item_id,
                text))
            # TODO Make this raise the exception instead of returning None
            return None

    def remove_task(self, item_id):
        """
        Delete a task
        :param item_id: ID of task to delete
        :return: whether task was deleted.
        """
        try:
            task = Task.select().where(Task.id == item_id).get()
            log("Removing task {} with text {}".format(item_id, task.text))
            task.delete_instance()
            return True
        except DoesNotExist:
            err("Removing task {}, but task not found".format(item_id))
            return False

    def complete_task(self, item_id, completion_time=None):
        """
        Mark task as done.
        :param item_id: ID of task to mark as done
        :param completion_time: Completion time; if None, completion time is now
        """
        try:
            task = Task.select().where(Task.id == item_id).get()
            task.done_timestamp = completion_time or datetime.now()
            task.save()
            log("Marking task {} with text '{}' as done".format(item_id,
                                                                task.text))
            self.move_to_end_of_heading(task.order_id, "Done")
            return True
        except DoesNotExist:
            # TODO make this raise the exception
            err("Tried marking task {} as done, but task not found".format(
                item_id))
            return False

    def get_max_order_id(self):
        """
        Return the maximum of all order_id's
        :return:
        """
        max_order_id = Task.select(fn.MAX(Task.order_id)).scalar()
        if max_order_id is None:
            return -1
        return int(max_order_id)

    def fix_order(self):
        """
        Condense the order_id's to all be sequential, retaining order
        """
        tasks = self.get_home_tasks()
        for index, task in enumerate(tasks):
            task['order_id'] = index
        self.delete_home_tasks()
        self.create_from_list(tasks, silent=True)

    def move_before(self, id_to_move, next_id):
        """
        Move task to be before another task
        :param id_to_move: Order ID of task to move
        :param next_id: Order ID of task before which to move the task
        :return: Moved task
        """
        log("Moving task {} to be before task {}".format(id_to_move, next_id))
        task_id = Task.select().where(Task.order_id == id_to_move).get().id

        now = datetime.now()
        today_midnight = datetime(now.year, now.month, now.day)

        # Double all order_id's
        Task.update(order_id=Task.order_id * 2).where(
            (Task.done_timestamp > today_midnight) | (
                Task.done_timestamp.is_null())
        ).execute()

        task_to_move = Task.select().where(
            Task.order_id == id_to_move * 2).get()
        task_to_move.order_id = next_id * 2 - 1
        task_to_move.save()
        self.fix_order()
        return Task.select().where(Task.id == task_id).get().to_dict()

    def delete_all_tasks(self):
        """
        Remove all tasks
        """
        log('Deleting ALL tasks')
        Task.delete().execute()

    def delete_home_tasks(self):
        """
        Remove all home tasks
        """
        log('Deleting ALL tasks')
        now = datetime.now()
        today_midnight = datetime(now.year, now.month, now.day)
        Task.delete().where(
            (Task.done_timestamp > today_midnight) | (
                Task.done_timestamp.is_null())
        ).execute()

    def create_from_list(self, l, silent=False):
        """
        Create many tasks from the list l
        :param l: list to create tasks from
        :param silent: do not log if True
        """
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

    def get_headings(self, include_uncategorized=True):
        """
        Get all heading tasks
        Uncategorized refers to the tasks before the first heading
        :param include_uncategorized: Include the pseudo-heading "Uncategorized"
        :return: heading tasks
        """
        tasks = Task.select().where(Task.heading == 1)
        tasks_dicts = list(map(model_to_dict, tasks))
        if include_uncategorized and tasks_dicts[0]['order_id'] != 0:
            tasks_dicts = [{
                'text': "Uncategorized",
                'heading': 1
            }] + tasks_dicts
        return tasks_dicts

    def get_categorized_tasks(self):
        """
        Return a map from category names to list of tasks under that category
        :return: ^
        """
        tasks = self.get_all_tasks()
        categories = [task['text'] for task in self.get_headings()]
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

    def move_to_end_of_heading(self, order_id, heading):
        """
        Move a task to the end of the category with name `heading`
        :param order_id: Order ID of task to move
        :param heading: Heading to move task to the end of
        :return: Moved task
        """
        headings = self.get_headings()
        heading_task = Task.select().where(
            (Task.heading == 1) & (Task.text == heading)).get()
        print(heading_task)
        heading_labels = [heading['text'] for heading in headings]
        if heading not in heading_labels:  # TODO fix this line
            raise Exception("Heading '{}' does not exist".format(heading))
        cat_tasks = self.get_categorized_tasks()
        num_tasks = len(cat_tasks[heading])
        return self.move_before(order_id, heading_task.order_id + num_tasks + 1)

    def move_task_to_today(self, task_id):
        """
        Move task to the end of today heading
        :param task_id: ID of task to move
        :return: Move task to the end of "Today" Heading
        """
        order_id = Task.select().where(Task.id == task_id).get().order_id
        return self.move_to_end_of_heading(order_id, "Today")


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
