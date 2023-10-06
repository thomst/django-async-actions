(function($) {

    var interval = 800;
    var error_msg = '[ERROR][task_by_ids]:';
    var baseurl = window.location.protocol + '//'
                + window.location.host
                + '/async_actions/tasks_by_ids/?';

    class TaskMessage {
        constructor(msg) {
            this.html = msg;
            this.msg_id = $(msg).attr('id');
            this.task_id = $(msg).data('task_id');
            this.checksum = $(msg).data('checksum');
        }
        update() {
            $('#' + this.msg_id).replaceWith(this.html);
        }
    }


    function getTaskMessages (url) {
        $.getJSON(url, updateTaskMessages).fail(ajaxFailure).done(run)
    }

    function updateTaskMessages(msgs) {
        $.each(msgs, function(msg_id, msg_html) {
            var msg = new TaskMessage(msg_html);
            msg.update();
        })
    }

    function ajaxFailure(response) {
        console.log(error_msg + response.status + ':' + response.statusText);
    }

    function run() {
        var msgs = {};
        $('tr.item-message div.task-waiting,tr.item-message div.task-running').each(
            function(i, e) {msgs[$(e).data('task_id')] = new TaskMessage(e)}
        );
        if (!$.isEmptyObject(msgs)) {
            var url = baseurl + "msgs=" + encodeURIComponent(JSON.stringify(msgs));
            console.log(url);
            window.setTimeout(getTaskMessages, interval, url);
        }
    }

    $(document).ready(run);
})($);
