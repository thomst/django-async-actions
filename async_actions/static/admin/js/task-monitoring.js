(function($) {

    var interval = 800;
    var error_msg = '[ERROR][task_by_ids]:';
    var baseurl = window.location.protocol + '//'
                + window.location.host
                + '/async_actions/tasks_by_ids/?';

    function getActionTasks (url) {
        $.getJSON(url, updateActionTasks).fail(ajaxFailure).done(run)
    }

    function updateActionTasks(tasks) {
        $.each(tasks, function(task_id, html) {
            $('#' + task_id).replaceWith(html);
            if ($(html).hasClass('FAILURE')) {
                $('#' + task_id).parents('tr.item-message').addClass('error').removeClass('info', 'success', 'debug', 'warning')
            }
        })
    }

    function ajaxFailure(response) {
        console.log(error_msg + response.status + ':' + response.statusText);
    }

    function run() {
        // FIXME: What about custom task-states?
        var tasks = {};
        $('span.actiontask.PENDING,span.actiontask.STARTED').each(
            function(i, e) {tasks[$(e).attr('id')] = $(e).data('hash')}
        );
        if (!$.isEmptyObject(tasks)) {
            var url = baseurl + $.param(tasks);
            window.setTimeout(getActionTasks, interval, url);
        }
    }

    $(document).ready(run);
})($);
