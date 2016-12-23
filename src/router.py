from datetime import timedelta

from flask import *
from src.models import *

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=0)


@app.before_request
def before_request():
    g.task_controller = TaskController()


@app.route('/')
def root():
    """
    Root Page: This is the home view for the app.
    Lists all home tasks and headers
    Note: "Home tasks" refers to all tasks that are
    either not done or have been marked as done today.
    """
    return redirect('/static/home.html')


@app.route('/favicon.ico')
def favicon():
    """
    Favicon
    """
    return redirect('/static/favicon.ico')


@app.route('/api/task', methods=['GET', 'POST'])
def task_route():
    """
    GET:
        returns all home tasks
    POST:
        Creates a new task
        Params:
         text: Task text
         header: 0 or 1 based on whether this should be a header task
    :return:
    """
    if request.method == 'GET':
        return jsonify(g.task_controller.get_home_tasks())
    elif request.method == 'POST':
        text = request.form.get('text', None)
        header = request.form.get('header', None) or 0
        task = g.task_controller.create_task(text, heading=header)
        return jsonify(task)


@app.route('/api/today_task', methods=['POST'])
def today_task():
    """
    Creates a new task and moves it the today section.  Same parameters
    as POST /api/task
    :return:
    """
    text = request.form.get('text', None)
    header = request.form.get('header', None) or 0
    task = g.task_controller.create_task(text, heading=header)
    updated_task = g.task_controller.move_to_end_of_heading(task['order_id'],
                                                            "Today")
    return jsonify(updated_task)


@app.route('/api/task/<int:item_id>', methods=['GET', 'DELETE'])
def single_item(item_id):
    """
    GET:
        Gets the details of a single task with id `item_id`
    DELETE:
        Deletes the task with the given id `item_id`
    :param item_id: ID of the task to fetch/delete
    """
    if request.method == 'GET':
        task = g.task_controller.get_task(item_id)
        return jsonify(task)
    elif request.method == 'DELETE':
        return string_from_success_bool(g.task_controller.remove_task(item_id))


@app.route('/api/task/<int:item_id>/update_text', methods=['POST'])
def update_text(item_id):
    """
    Updates the text of one task
    :param item_id: ID of task to update
    """
    text = request.form.get('text', None)
    task = g.task_controller.update_task_text(item_id, text)
    return jsonify(task)


@app.route('/api/task/move', methods=['POST'])
def move_item():
    """
    Moves (reorders) a task.
    Params:
     from: Order ID of task
     to: New order ID of task

    Note: This moves the task currently at the `to` Order ID to be
    AFTER the moved task
    """
    from_index = int(request.form.get('from'))
    to_index = int(request.form.get('to'))

    if to_index < from_index:
        g.task_controller.move_before(from_index, to_index)
    elif to_index == from_index:
        pass
    else:
        g.task_controller.move_before(from_index, to_index + 1)
    return 'Success'


@app.route('/api/task/<int:item_id>/complete', methods=['POST'])
def complete_item(item_id):
    """
    Mark a task as Done with the current timestamp
    :param item_id: ID of task to mark done
    """
    return string_from_success_bool(g.task_controller.complete_task(item_id))


@app.route('/api/task/<int:item_id>/move_to_today', methods=['POST'])
def move_to_today(item_id):
    """
    Move a task to the end of the "Today" Heading
    :param item_id: ID of task to move
    """
    return g.task_controller.move_task_to_today(item_id)


def string_from_success_bool(success):
    """
    :param success: a boolean
    :return: A string representing the boolean
    """
    return 'Success' if success else 'Failure'

# def render(filename, data):
#     template_path = os.path.join(app.root_path, 'templates', filename)
#     with open(template_path) as file:
#         file_data = file.read()
#         return pystache.render(file_data, context=data)
