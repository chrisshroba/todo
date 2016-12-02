from datetime import timedelta

from flask import *
from src.models import *

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=0)


@app.route('/')
def root():
    return redirect('/static/home.html')


@app.route('/api/task', methods=['GET', 'POST'])
def task():
    if request.method == 'GET':
        return jsonify(get_all_tasks())
    elif request.method == 'POST':
        text = request.form.get('text', None)
        header = request.form.get('header', None) or 0
        task = create_task(text, heading=header)
        return jsonify(task)


@app.route('/api/task/<int:item_id>', methods=['GET', 'DELETE'])
def single_item(item_id):
    if request.method == 'GET':
        task = get_task(item_id)
        return jsonify(task)
    elif request.method == 'DELETE':
        return string_from_success_bool(remove_task(item_id))


@app.route('/api/task/<int:item_id>/update_text', methods=['POST'])
def update_text(item_id):
    text = request.form.get('text', None)
    task = update_task_text(item_id, text)
    return jsonify(task)


@app.route('/api/task/move', methods=['POST'])
def move_item():
    from_index = int(request.form.get('from'))
    to_index = int(request.form.get('to'))

    if to_index < from_index:
        move_before(from_index, to_index)
    elif to_index == from_index:
        pass
    else:
        move_before(from_index, to_index + 1)

    return 'Success'


@app.route('/api/task/<int:item_id>/complete', methods=['POST'])
def complete_item(item_id):
    return string_from_success_bool(complete_task(item_id))


def string_from_success_bool(success):
    return 'Success' if success else 'Failure'

# def render(filename, data):
#     template_path = os.path.join(app.root_path, 'templates', filename)
#     with open(template_path) as file:
#         file_data = file.read()
#         return pystache.render(file_data, context=data)
