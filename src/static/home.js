var taskTexts = {};

$(go);

function go() {
    fetch_and_render_tasks();
    attach_new_task_listener();
    attach_body_key_listeners();
}

function setup_drag_and_drop() {
    var sort_config = {
        animation: 75, // ms, animation speed moving items when sorting, `0` — without animation
        // handle: ".handle", // Restricts sort start click/touch to the specified element
        draggable: ".draggable", // Specifies which items inside the element should be sortable
        fallbackTolerance: 1000,
        onUpdate: function (evt/**Event*/) {
            var item = evt.item; // the current dragged HTMLElement
        },
        onEnd: function (evt) {
            var from = evt.oldIndex;
            var to = evt.newIndex;
            console.log("From: " + from + ", to: " + to);
            postData = {
                from: from,
                to: to
            };

            $.post("/api/task/move", postData, function (response) {
                fetch_and_render_tasks();
            })
        }
    };
    var sort = Sortable.create(document.getElementById('list'), sort_config);

}

function fetch_and_render_tasks() {
    $.get('/api/task', function (response) {
        var tasks = response;
        render_tasks(tasks);
    })
}

function render_tasks(tasks) {

    tasks = tasks.map(function (task) {
        taskTexts[task.id] = task.text;
        task.text = prepareTaskText(task.text);
        task.heading = task.heading == 1;
        task.doneBool = task.done_timestamp != null;
        return task;
    });
    var data = {
        tasks: tasks
    };
    // var template = $('#template').html();
    $.get('/static/todo.mustache',
        function (template) {
            var rendered = Mustache.render(template, data)
            $("#list").html(rendered);
            setup_drag_and_drop()
            $(".draggable").hover(function () {
                $(this).toggleClass("draggable_hover");
            });
            attach_action_listeners();

        });

}

function prompt_for_task() {
    var task_text = prompt("Enter task");
    create_new_task(task_text);
}

function create_new_task(task_text) {
    var post_data = {
        text: task_text
    };
    $.post('/api/task', post_data, function (response) {
        fetch_and_render_tasks();
        scroll_to_bottom();
    })
}

function create_new_header(task_text) {
    var post_data = {
        text: task_text,
        header: 1
    };
    $.post('/api/task', post_data, function (response) {
        fetch_and_render_tasks();
        scroll_to_bottom()
    })
}

function scroll_to_bottom() {
    $("html, body").animate({ scrollTop: $(document).height() }, "fast");
}


function prepareTaskText(html) {
    var replace_fn2 = function (match, p1) {
        return "<a href='" + p1 + "'>" + p1 + "</a>";
    };
    var pattern3 = /((?:[^\[]|^)https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*))/; //Bare links
    html = html.replace(pattern3, replace_fn2);

    var pattern = /\[\[(.*?)\|(.*?)\]\]/; //Links with text
    var replace_fn = function (match, p1, p2) {
        return "<a href='" + p1 + "'>" + p2 + "</a>";
    };
    html = html.replace(pattern, replace_fn);

    var pattern2 = /\[\[(.*)\]\]/; //Bare links
    html = html.replace(pattern2, replace_fn2);


    return capitalizeFirstLetter(html);
}

function attach_new_task_listener() {
    $("#new-task-input").on('keyup', function (e) {
        if (e.keyCode == 13) {
            var task_text = $(this).val();
            if (e.shiftKey) {
                create_new_header(task_text);
            }
            else {
                create_new_task(task_text);
            }
            $(this).val("");
        }
    });
}

function attach_action_listeners() {
    $(".edit-icon").click(function (evt) {

        var li = $($(this).closest('li')[0]);
        var taskId = parseInt(li.data('taskid'));
        // var oldText = li.children('.task-text').html().trim();
        var oldText = taskTexts[taskId];
        var newText = prompt("Enter new text for task", oldText);
        if (newText == null) {
            return;
        }
        var postData = {text: newText}
        $.post('/api/task/' + taskId + "/update_text", postData, function (response) {
            fetch_and_render_tasks();
        });
    });

    $(".done-icon").click(function (evt) {
        var taskId = parseInt($($(this).closest('li')[0]).data('taskid'));
        $.post('/api/task/' + taskId + "/complete", {}, function (response) {
            fetch_and_render_tasks();
        });
    });

    $(".trash-icon").click(function (evt) {
        var taskId = parseInt($($(this).closest('li')[0]).data('taskid'));
        $.ajax({
            url: '/api/task/' + taskId,
            type: 'DELETE',
            success: function (result) {
                fetch_and_render_tasks()
            }
        });
    });


}

function attach_body_key_listeners() {
    $('body').keypress(function (e) {
        // if (e.which == 97) {
        //     console.log("add");
        $("#new-task-input").focus();
        // }
    });
}

function capitalizeFirstLetter(string) {
    if (!string.startsWith('http'))
        return string.charAt(0).toUpperCase() + string.slice(1);
    return string;
}