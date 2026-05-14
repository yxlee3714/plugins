<section class="page-content-main">
    <div class="content-box">
        <div class="col-md-12">
            <div class="alert alert-info" role="alert">NC-Link UI loaded</div>
        </div>
        <div class="col-md-7">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <h3 class="panel-title">NC-Link Settings</h3>
                </div>
                <div class="panel-body">
                    <form id="frm_GeneralSettings">
                        <div class="form-group">
                            <label>
                                <input id="nclink.general.enabled" type="checkbox" value="1">
                                Enable
                            </label>
                            <p class="help-block">Start the NC-Link TCP agent.</p>
                        </div>
                        <div class="form-group">
                            <label for="nclink.general.listen_port">Listen port</label>
                            <input class="form-control" id="nclink.general.listen_port" type="text" value="8088">
                            <p class="help-block">TCP port for JSON-lines NC-Link PDUs.</p>
                        </div>
                        <div class="form-group">
                            <label for="nclink.general.device_uuid">Device UUID</label>
                            <input class="form-control" id="nclink.general.device_uuid" type="text" value="test-device-001">
                            <p class="help-block">Default dev_uuid used by the bundled CNC model.</p>
                        </div>
                        <div class="form-group">
                            <label for="nclink.general.protocol_version">Model version</label>
                            <input class="form-control" id="nclink.general.protocol_version" type="text" value="1.0">
                            <p class="help-block">Version reported by Probe/Version and model probe responses.</p>
                        </div>
                        <div class="form-group">
                            <label for="nclink.general.default_model">Model JSON</label>
                            <textarea class="form-control" id="nclink.general.default_model" rows="10" style="font-family:monospace"></textarea>
                            <p class="help-block">Optional NC-Link machine model JSON. Leave empty to use the built-in standard-style sample model.</p>
                        </div>
                    </form>
                    <button class="btn btn-primary" id="save-settings" type="button">
                        <span class="fa fa-save"></span> Save
                    </button>
                </div>
            </div>
        </div>

        <div class="col-md-5">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <h3 class="panel-title">Service</h3>
                </div>
                <div class="panel-body">
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-success" id="service-start" type="button">
                            <span class="fa fa-play"></span> Start
                        </button>
                        <button class="btn btn-danger" id="service-stop" type="button">
                            <span class="fa fa-stop"></span> Stop
                        </button>
                        <button class="btn btn-info" id="service-restart" type="button">
                            <span class="fa fa-refresh"></span> Restart
                        </button>
                    </div>
                    <hr>
                    <dl class="dl-horizontal">
                        <dt>Status</dt>
                        <dd id="service-status">Loading...</dd>
                        <dt>Port</dt>
                        <dd id="service-port">8088</dd>
                        <dt>Connections</dt>
                        <dd id="service-connections">0</dd>
                    </dl>
                    <pre id="service-output" style="max-height:160px;overflow:auto"></pre>
                </div>
            </div>

            <div class="panel panel-default">
                <div class="panel-heading">
                    <h3 class="panel-title">Protocol Self Test</h3>
                </div>
                <div class="panel-body">
                    <select id="pdu-template" class="form-control">
                        <option value="probe">Terminal Probe</option>
                        <option value="version">Version Check</option>
                        <option value="model">Model Probe</option>
                        <option value="query">Data Query</option>
                        <option value="sample">Sample</option>
                        <option value="method">Method Call</option>
                        <option value="event">Event Register</option>
                    </select>
                    <textarea id="pdu-input" class="form-control" rows="10" style="margin-top:10px;font-family:monospace"></textarea>
                    <button class="btn btn-primary" id="pdu-send" type="button" style="margin-top:10px">
                        <span class="fa fa-paper-plane"></span> Send PDU
                    </button>
                    <pre id="pdu-output" style="margin-top:10px;max-height:260px;overflow:auto"></pre>
                </div>
            </div>
        </div>
    </div>
</section>

<script>
$(function() {
    "use strict";

    var templates = {
        probe:   {"msg_id":"ui-probe-1","interface":"Probe","action":"Terminal"},
        version: {"msg_id":"ui-version-1","interface":"Version","dev_uuid":"test-device-001","version":"1.0"},
        model:   {"msg_id":"ui-model-1","interface":"Model","action":"Probe","dev_uuid":"test-device-001"},
        query:   {"msg_id":"ui-query-1","interface":"Query","dev_uuid":"test-device-001","ids":[{"id":"010302"},{"id":"010303"}]},
        sample:  {"msg_id":"ui-sample-1","interface":"Sample","dev_uuid":"test-device-001","ids":[{"id":"010302"},{"id":"01031220"}]},
        method:  {"msg_id":"ui-method-1","interface":"Method","action":"Call","dev_uuid":"test-device-001","method_id":"method.reset_alarm","params":{}},
        event:   {"msg_id":"ui-event-1","interface":"Event","action":"Register","dev_uuid":"test-device-001","filter":{"level":"warning"}}
    };

    function pretty(data) {
        return JSON.stringify(data, null, 2);
    }

    function nclinkApi(path, payload, success) {
        ajaxCall('/api/nclink/' + path, payload, success);
    }

    function nclinkService(path, payload, success) {
        $.ajax({
            url: '/api/nclink/' + path,
            method: 'POST',
            data: payload,
            dataType: 'json',
            global: false
        }).done(success).fail(function(xhr) {
            $('#service-output').text('service request failed: ' + path + '\nHTTP ' + xhr.status + '\n' + (xhr.responseText || ''));
            // 请求失败时也要刷新真实状态
            refreshStatus();
        });
    }

    function statusLabel(running) {
        return running
            ? '<span class="label label-success">Running</span>'
            : '<span class="label label-default">Stopped</span>';
    }

    function refreshStatus() {
        nclinkApi('service/status', {}, function(data) {
            var status = data.status || {};
            $('#service-status').html(statusLabel(status.running));
            $('#service-port').text(status.port || 8088);
            $('#service-connections').text(status.connections || 0);
        });
    }

    function loadTemplate() {
        $('#pdu-input').val(pretty(templates[$('#pdu-template').val()]));
    }

    function modelValue(data, key, fallback) {
        if (data.nclink && data.nclink.general && data.nclink.general[key] !== undefined) {
            return data.nclink.general[key];
        }
        return fallback;
    }

    function loadSettings() {
        nclinkApi('settings/get', {}, function(data) {
            $('#nclink\\.general\\.enabled').prop('checked', modelValue(data, 'enabled', '0') === '1');
            $('#nclink\\.general\\.listen_port').val(modelValue(data, 'listen_port', '8088'));
            $('#nclink\\.general\\.device_uuid').val(modelValue(data, 'device_uuid', 'test-device-001'));
            $('#nclink\\.general\\.protocol_version').val(modelValue(data, 'protocol_version', '1.0'));
            $('#nclink\\.general\\.default_model').val(modelValue(data, 'default_model', ''));
        });
    }

    function collectSettings() {
        return {
            nclink: {
                general: {
                    enabled: $('#nclink\\.general\\.enabled').is(':checked') ? '1' : '0',
                    listen_port: $('#nclink\\.general\\.listen_port').val(),
                    device_uuid: $('#nclink\\.general\\.device_uuid').val(),
                    protocol_version: $('#nclink\\.general\\.protocol_version').val(),
                    default_model: $('#nclink\\.general\\.default_model').val()
                }
            }
        };
    }

    $('#save-settings').on('click', function() {
        nclinkApi('settings/set', collectSettings(), function() {
            $('#service-output').text('settings saved');
            refreshStatus();
        });
    });

    var pollTimer = null;

    function startPolling() {
        if (pollTimer) return;
        pollTimer = setInterval(refreshStatus, 5000);
    }

    function stopPolling() {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    $('#service-start, #service-stop, #service-restart').on('click', function() {
        var action = this.id.replace('service-', '');

        // 禁用按钮防止重复点击
        $('#service-start, #service-stop, #service-restart').prop('disabled', true);

        // 乐观更新：立即反映预期状态
        if (action === 'stop') {
            // stop 后停止轮询，避免轮询覆盖 Stopped 状态
            stopPolling();
            $('#service-status').html(statusLabel(false));
        } else {
            $('#service-status').html('<span class="label label-warning">Starting...</span>');
        }

        nclinkService('service/' + action, {}, function(data) {
            $('#service-output').text(data.output || data.result || '');

            if (action === 'stop') {
                // stop 完成后只恢复按钮，不查询状态，不重启轮询
                $('#service-start, #service-stop, #service-restart').prop('disabled', false);
            } else {
                // start/restart 完成后延迟查询并恢复轮询
                setTimeout(function() {
                    refreshStatus();
                    startPolling();
                    $('#service-start, #service-stop, #service-restart').prop('disabled', false);
                }, 1000);
            }
        });
    });

    $('#pdu-template').on('change', loadTemplate);

    $('#pdu-send').on('click', function() {
        nclinkApi('service/pdu', {pdu: $('#pdu-input').val()}, function(data) {
            $('#pdu-output').text(pretty(data));
        });
    });

    loadSettings();
    loadTemplate();
    refreshStatus();
    startPolling();
});
</script>
