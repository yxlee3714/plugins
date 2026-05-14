#!/usr/local/bin/php
<?php

// NC-Link Daemon - Standalone implementation
// Does not depend on OPNsense BaseModel framework

class Logger {
    private $name;

    public function __construct($name) {
        $this->name = $name;
        openlog($name, LOG_PID, LOG_DAEMON);
    }

    public function __destruct() {
        closelog();
    }

    public function info($message, array $context = array()) {
        $this->log(LOG_INFO, $message, $context);
    }

    public function error($message, array $context = array()) {
        $this->log(LOG_ERR, $message, $context);
    }

    private function log($priority, $message, array $context) {
        // FIX #6: openlog/closelog moved to constructor/destructor
        syslog($priority, $message . ($context ? ' ' . json_encode($context, JSON_UNESCAPED_SLASHES) : ''));
    }
}

class NclinkConfig {
    private $port = 8088;
    private $uuid = 'test-device-001';
    private $version = '1.0';

    public function __construct() {
        $this->loadFromConfig();
    }

    private function loadFromConfig() {
        $configFile = '/conf/config.xml';
        if (!file_exists($configFile)) {
            return;
        }

        try {
            $xml = @simplexml_load_file($configFile);
            if ($xml && isset($xml->OPNsense->nclink->general)) {
                $general = $xml->OPNsense->nclink->general;
                if (isset($general->listen_port)) {
                    $this->port = (int)$general->listen_port;
                }
                if (isset($general->device_uuid)) {
                    $this->uuid = (string)$general->device_uuid;
                }
                if (isset($general->protocol_version)) {
                    $this->version = (string)$general->protocol_version;
                }
            }
        } catch (Exception $e) {
            // FIX #1: log config errors instead of silently ignoring
            error_log('nclink: config load failed: ' . $e->getMessage());
        }
    }

    public function getPort() {
        return $this->port;
    }

    public function getUUID() {
        return $this->uuid;
    }

    public function getVersion() {
        return $this->version;
    }
}

class Agent {
    private $uuid;
    private $version;
    private $values = array();

    public function __construct($uuid, $version) {
        $this->uuid = $uuid;
        $this->version = $version;
        $this->values = $this->defaultValues();
    }

    public function handlePDU(array $pdu) {
        $verb = $this->detectVerb($pdu);
        switch ($verb) {
            case 'register':
                return $this->register($pdu);
            case 'terminal_probe':
                return $this->terminalProbe($pdu);
            case 'version':
                return $this->versionCheck($pdu);
            case 'query':
                return $this->query($pdu);
            case 'set':
                return $this->setData($pdu);
            case 'sample':
                return $this->sample($pdu);
            default:
                return $this->errorResponse($pdu, 'unsupported_interface', 'unsupported NC-Link PDU');
        }
    }

    private function detectVerb(array $pdu) {
        // FIX #4: exact field matching instead of substring search
        $iface  = strtolower(isset($pdu['interface']) ? $pdu['interface'] : '');
        $type   = strtolower(isset($pdu['type'])      ? $pdu['type']      : '');
        $method = strtolower(isset($pdu['method'])    ? $pdu['method']    : '');

        $verbs = array('register', 'terminal_probe', 'version', 'query', 'set', 'sample');
        foreach ($verbs as $verb) {
            if ($iface === $verb || $type === $verb || $method === $verb) {
                return $verb;
            }
        }
        return '';
    }

    private function ok(array $request, array $payload = array()) {
        return array_merge(array(
            'code'      => 'OK',
            'msg_id'    => isset($request['msg_id']) ? $request['msg_id'] : null,
            'timestamp' => date(DATE_ATOM)
        ), $payload);
    }

    public function errorResponse($request, $reason, $message) {
        return array(
            'code'      => 'NG',
            'reason'    => $reason,
            'message'   => $message,
            'msg_id'    => is_array($request) && isset($request['msg_id']) ? $request['msg_id'] : null,
            'timestamp' => date(DATE_ATOM)
        );
    }

    private function register(array $pdu) {
        return $this->ok($pdu, array('dev_uuid' => $this->uuid));
    }

    private function terminalProbe(array $pdu) {
        return $this->ok($pdu, array('adapters' => array(array(
            'dev_uuid'   => $this->uuid,
            'version'    => $this->version,
            'name'       => 'OPNsense NC-Link Agent',
            'interfaces' => array('Register', 'Probe', 'Version', 'Query', 'Set', 'Sample')
        ))));
    }

    private function versionCheck(array $pdu) {
        return $this->ok($pdu, array(
            'dev_uuid' => $this->uuid,
            'version'  => $this->version,
            'matched'  => true
        ));
    }

    private function query(array $pdu) {
        // FIX #7: use $this->values instead of hard-coded literals
        $data = array();
        foreach ($this->values as $k => $v) {
            $data[] = array('id' => $k, 'value' => $v);
        }
        return $this->ok($pdu, array(
            'dev_uuid' => $this->uuid,
            'data'     => $data
        ));
    }

    private function setData(array $pdu) {
        return $this->ok($pdu, array('dev_uuid' => $this->uuid, 'result' => array()));
    }

    private function sample(array $pdu) {
        // FIX #7: use $this->values instead of hard-coded literals
        $sample = array();
        foreach ($this->values as $k => $v) {
            $sample[] = array('id' => $k, 'value' => $v);
        }
        return $this->ok($pdu, array(
            'dev_uuid'    => $this->uuid,
            'sample'      => $sample,
            'sample_time' => date(DATE_ATOM)
        ));
    }

    private function defaultValues() {
        return array('status' => 'online');
    }
}

// ─── Main daemon ──────────────────────────────────────────────────────────────

$logger = new Logger('NC-Link-Daemon');
$config = new NclinkConfig();
$port       = $config->getPort();
$uuid       = $config->getUUID();
$version    = $config->getVersion();
$statusFile = '/var/run/nclink.status.json';

const CLIENT_BUFFER_MAX = 65536; // FIX #2: 64 KB per-client buffer cap

$server = @stream_socket_server(
    sprintf('tcp://0.0.0.0:%d', $port),
    $errno,
    $errstr,
    STREAM_SERVER_BIND | STREAM_SERVER_LISTEN
);

if ($server === false) {
    $logger->error('listen failed', array('errno' => $errno, 'error' => $errstr));
    exit(1);
}

stream_set_blocking($server, false);
$clients = array();
$buffers = array();
$agent   = new Agent($uuid, $version);
$logger->info('NC-Link agent started', array('port' => $port, 'uuid' => $uuid));

$writeStatus = function () use (&$clients, $port, $statusFile) {
    @file_put_contents($statusFile, json_encode(array(
        'running'     => true,
        'port'        => $port,
        'connections' => count($clients),
        'updated_at'  => date(DATE_ATOM)
    ), JSON_UNESCAPED_SLASHES));
};

$writeStatus();
register_shutdown_function(function () use ($statusFile) {
    @file_put_contents($statusFile, json_encode(array(
        'running'     => false,
        'connections' => 0,
        'updated_at'  => date(DATE_ATOM)
    ), JSON_UNESCAPED_SLASHES));
});

while (true) {
    $read   = array_merge(array($server), $clients);
    $write  = null;
    $except = null;

    // FIX #5: guard against empty $read array before calling stream_select
    if (empty($read)) {
        sleep(1);
        continue;
    }

    if (@stream_select($read, $write, $except, 2) === false) {
        continue;
    }

    foreach ($read as $socket) {
        if ($socket === $server) {
            $client = @stream_socket_accept($server, 0);
            if ($client !== false) {
                stream_set_blocking($client, false);
                $id             = (int)$client;
                $clients[$id]   = $client;
                $buffers[$id]   = '';
                $logger->info('client connected', array('id' => $id));
                $writeStatus();
            }
            continue;
        }

        $id   = (int)$socket;
        $data = @fread($socket, 8192);

        if ($data === '' || $data === false) {
            if (feof($socket)) {
                fclose($socket);
                unset($clients[$id], $buffers[$id]);
                $logger->info('client disconnected', array('id' => $id));
                $writeStatus();
            }
            continue;
        }

        $buffers[$id] .= $data;

        // FIX #2: disconnect clients that overflow the per-client buffer cap
        if (strlen($buffers[$id]) > CLIENT_BUFFER_MAX) {
            fclose($socket);
            unset($clients[$id], $buffers[$id]);
            $logger->error('client buffer overflow, disconnected', array('id' => $id));
            $writeStatus();
            continue;
        }

        $lines      = explode("\n", $buffers[$id]);
        $buffers[$id] = array_pop($lines);

        foreach ($lines as $line) {
            $line = trim($line);
            if ($line === '') {
                continue;
            }

            $request = json_decode($line, true);
            if (!is_array($request)) {
                $response = $agent->errorResponse(null, 'bad_request', 'invalid json');
            } else {
                try {
                    $response = $agent->handlePDU($request);
                } catch (Exception $e) {
                    $logger->error('PDU failed', array('error' => $e->getMessage()));
                    $response = $agent->errorResponse($request, 'internal_error', $e->getMessage());
                }
            }

            // FIX #3: check fwrite return value and log failures
            $out     = json_encode($response, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n";
            $written = @fwrite($socket, $out);
            if ($written === false || $written < strlen($out)) {
                $logger->error('write failed', array('id' => $id, 'expected' => strlen($out), 'written' => $written));
            }
        }
    }
}