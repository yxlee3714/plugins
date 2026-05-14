<?php

namespace OPNsense\Nclink;

use OPNsense\Base\BaseModel;

class Nclink extends BaseModel
{
    public function getListenPort()
    {
        $port = (string)$this->general->listen_port;
        return $port !== '' ? (int)$port : 8088;
    }

    public function getAgent()
    {
        return new Agent($this);
    }

    public function isEnabled()
    {
        return (string)$this->general->enabled === '1';
    }

    public function getDeviceUuid()
    {
        $uuid = trim((string)$this->general->device_uuid);
        return $uuid !== '' ? $uuid : 'test-device-001';
    }

    public function getProtocolVersion()
    {
        $version = trim((string)$this->general->protocol_version);
        return $version !== '' ? $version : '1.0';
    }

    public function getDefaultModel()
    {
        $configured = trim((string)$this->general->default_model);
        if ($configured !== '') {
            $decoded = json_decode($configured, true);
            if (is_array($decoded)) {
                return $decoded;
            }
        }

        return Agent::defaultMachineModel($this->getDeviceUuid(), $this->getProtocolVersion());
    }
}

class Agent
{
    private $model;
    private $devices = array();
    private $values = array();
    private $dynamicSamples = array();
    private $events = array();
    private $methods = array();

    public function __construct(Nclink $model)
    {
        $this->model = $model;
        $uuid = $model->getDeviceUuid();
        $this->devices[$uuid] = array(
            'uuid' => $uuid,
            'version' => $model->getProtocolVersion(),
            'model' => $model->getDefaultModel(),
            'registered_at' => date(DATE_ATOM)
        );
        $this->values = self::defaultValues();
    }

    public function handlePDU(array $pdu)
    {
        $verb = $this->detectVerb($pdu);
        switch ($verb) {
            case 'register':
                return $this->register($pdu);
            case 'terminal_probe':
                return $this->terminalProbe($pdu);
            case 'version':
                return $this->versionCheck($pdu);
            case 'model_probe':
                return $this->modelProbe($pdu);
            case 'model_set':
                return $this->modelSet($pdu);
            case 'query':
                return $this->query($pdu);
            case 'set':
                return $this->setData($pdu);
            case 'sample':
                return $this->sample($pdu);
            case 'status':
                return $this->statusNotify($pdu);
            case 'dynamic_sample_register':
                return $this->dynamicSampleRegister($pdu);
            case 'dynamic_sample_unregister':
                return $this->dynamicSampleUnregister($pdu);
            case 'dynamic_sample':
                return $this->dynamicSample($pdu);
            case 'method_call':
                return $this->methodCall($pdu);
            case 'method_control':
                return $this->methodControl($pdu);
            case 'event_register':
                return $this->eventRegister($pdu);
            case 'event_unregister':
                return $this->eventUnregister($pdu);
            case 'event_data':
                return $this->eventData($pdu);
            default:
                return self::errorResponse($pdu, 'unsupported_interface', 'unsupported NC-Link PDU');
        }
    }

    public static function errorResponse($request, $reason, $message)
    {
        return array(
            'code' => 'NG',
            'reason' => $reason,
            'message' => $message,
            'msg_id' => is_array($request) && isset($request['msg_id']) ? $request['msg_id'] : null,
            'timestamp' => date(DATE_ATOM)
        );
    }

    public static function defaultMachineModel($uuid, $version)
    {
        return array(
            'id' => '01',
            'type' => 'NC_LINK_ROOT',
            'name' => 'NC-Link CNC machine model',
            'version' => $version,
            'dev_uuid' => $uuid,
            'devices' => array(array(
                'type' => 'MACHINE',
                'id' => '0103',
                'name' => 'CNC machine',
                'description' => 'Default NC-Link machine model',
                'version' => $version,
                'configs' => array(
                    array('id' => '010301', 'type' => 'TYPE', 'name' => 'machine type', 'value' => 'cnc'),
                    array(
                        'id' => 'sample_channel0',
                        'type' => 'SAMPLE_CHANNEL',
                        'name' => 'basic sample channel',
                        'sampleInterval' => 2000,
                        'uploadInterval' => 2000,
                        'ids' => array(
                            array('id' => '010302'),
                            array('id' => '010303'),
                            array('id' => '010305'),
                            array('id' => '010306'),
                            array('id' => '010307'),
                            array('id' => '01031220')
                        )
                    )
                ),
                'dataItems' => array(
                    array('id' => '010302', 'name' => 'machine status', 'type' => 'STATUS'),
                    array('id' => '010303', 'name' => 'feed speed', 'type' => 'FEED_SPEED', 'units' => 'mm/min'),
                    array('id' => '010305', 'name' => 'feed override', 'type' => 'FEED_OVERRIDE', 'units' => '%'),
                    array('id' => '010306', 'name' => 'spindle override', 'type' => 'SPDL_OVERRIDE', 'units' => '%'),
                    array('id' => '010307', 'name' => 'part count', 'type' => 'PART_COUNT')
                ),
                'components' => array(
                    self::axis('X', '010308'),
                    self::axis('Y', '010309'),
                    self::axis('Z', '010310'),
                    array(
                        'type' => 'CONTROLLER',
                        'id' => '010312',
                        'name' => 'CNC controller',
                        'configs' => array(
                            array('id' => '01031201', 'type' => 'MODEL', 'name' => 'controller model'),
                            array('id' => '01031202', 'type' => 'MANUFACTURER', 'name' => 'controller manufacturer')
                        ),
                        'dataItems' => array(
                            array('id' => '01031217', 'type' => 'PROGRAM', 'name' => 'main program', 'dataType' => 'DICT'),
                            array('id' => '01031218', 'type' => 'SUBPROGRAM', 'name' => 'sub program', 'dataType' => 'DICT'),
                            array('id' => '01031219', 'type' => 'LINE_NUMBER', 'name' => 'line number'),
                            array('id' => '01031220', 'type' => 'WARNING', 'name' => 'alarm')
                        )
                    )
                ),
                'methods' => array(
                    array('id' => 'method.reset_alarm', 'name' => 'reset alarm', 'type' => 'METHOD'),
                    array('id' => 'method.start_cycle', 'name' => 'start cycle', 'type' => 'METHOD')
                )
            ))
        );
    }

    private static function axis($number, $id)
    {
        return array(
            'type' => 'AXIS',
            'number' => $number,
            'id' => $id,
            'name' => $number . ' axis',
            'configs' => array(
                array('id' => $id . '03', 'name' => 'axis type', 'type' => 'TYPE', 'value' => 'linear')
            ),
            'components' => array(array(
                'type' => 'SCREW',
                'id' => $id . '04',
                'name' => $number . ' screw',
                'dataItems' => array(
                    array('id' => $id . '0402', 'name' => 'actual position', 'type' => 'POSITION'),
                    array('id' => $id . '0404', 'name' => 'actual speed', 'type' => 'SPEED')
                )
            ))
        );
    }

    private static function defaultValues()
    {
        return array(
            '010302' => 'ready',
            '010303' => 1200,
            '010305' => 100,
            '010306' => 100,
            '010307' => 0,
            '0103080402' => 0.0,
            '0103080404' => 0.0,
            '0103090402' => 0.0,
            '0103090404' => 0.0,
            '0103100402' => 0.0,
            '0103100404' => 0.0,
            '01031217' => array('name' => 'O0001'),
            '01031218' => array('name' => ''),
            '01031219' => 1,
            '01031220' => array()
        );
    }

    private function detectVerb(array $pdu)
    {
        $text = strtolower(implode('/', array_filter(array(
            isset($pdu['interface']) ? $pdu['interface'] : null,
            isset($pdu['type']) ? $pdu['type'] : null,
            isset($pdu['method']) ? $pdu['method'] : null,
            isset($pdu['action']) ? $pdu['action'] : null,
            isset($pdu['name']) ? $pdu['name'] : null
        ))));

        $map = array(
            'dynamic_sample_register' => array('dynamic/register', 'dynamic_sample/register', 'sample/register'),
            'dynamic_sample_unregister' => array('dynamic/unregister', 'dynamic_sample/unregister', 'sample/unregister'),
            'dynamic_sample' => array('dynamic/sample', 'dynamic_sample/data'),
            'event_register' => array('event/register'),
            'event_unregister' => array('event/unregister'),
            'event_data' => array('event/data', 'event/notify'),
            'method_control' => array('method/control'),
            'method_call' => array('method/call', 'method/request'),
            'model_set' => array('model/set', 'probe/set'),
            'model_probe' => array('model/probe', 'model/request', 'probe/model'),
            'terminal_probe' => array('terminal/probe', 'probe/terminal', 'discover'),
            'version' => array('version'),
            'register' => array('register'),
            'query' => array('query', 'data/query'),
            'set' => array('data/set', 'set/request'),
            'sample' => array('sample/data', 'sample'),
            'status' => array('status')
        );

        foreach ($map as $verb => $needles) {
            foreach ($needles as $needle) {
                if (strpos($text, $needle) !== false) {
                    return $verb;
                }
            }
        }

        return '';
    }

    private function ok(array $request, array $payload = array())
    {
        return array_merge(array(
            'code' => 'OK',
            'msg_id' => isset($request['msg_id']) ? $request['msg_id'] : null,
            'timestamp' => date(DATE_ATOM)
        ), $payload);
    }

    private function uuid(array $pdu)
    {
        foreach (array('dev_uuid', 'device_uuid', 'uuid', 'guid') as $key) {
            if (!empty($pdu[$key])) {
                return (string)$pdu[$key];
            }
        }
        return $this->model->getDeviceUuid();
    }

    private function register(array $pdu)
    {
        $uuid = $this->uuid($pdu);
        $this->devices[$uuid] = array(
            'uuid' => $uuid,
            'version' => isset($pdu['version']) ? (string)$pdu['version'] : $this->model->getProtocolVersion(),
            'model' => isset($pdu['model']) && is_array($pdu['model']) ? $pdu['model'] : $this->model->getDefaultModel(),
            'registered_at' => date(DATE_ATOM)
        );
        return $this->ok($pdu, array('dev_uuid' => $uuid));
    }

    private function terminalProbe(array $pdu)
    {
        return $this->ok($pdu, array('adapters' => array(array(
            'dev_uuid' => $this->model->getDeviceUuid(),
            'version' => $this->model->getProtocolVersion(),
            'name' => 'OPNsense NC-Link Agent',
            'interfaces' => array(
                'Register', 'Probe', 'Version', 'Model', 'Query', 'Set', 'Sample',
                'Status', 'DynamicSample', 'Method', 'Event'
            )
        ))));
    }

    private function versionCheck(array $pdu)
    {
        $uuid = $this->uuid($pdu);
        $known = isset($this->devices[$uuid]) ? $this->devices[$uuid]['version'] : $this->model->getProtocolVersion();
        $incoming = isset($pdu['version']) ? (string)$pdu['version'] : $known;
        return $this->ok($pdu, array(
            'dev_uuid' => $uuid,
            'version' => $known,
            'matched' => $incoming === $known,
            'need_model' => $incoming !== $known
        ));
    }

    private function modelProbe(array $pdu)
    {
        $uuid = $this->uuid($pdu);
        $device = isset($this->devices[$uuid]) ? $this->devices[$uuid] : $this->devices[$this->model->getDeviceUuid()];
        return $this->ok($pdu, array('dev_uuid' => $uuid, 'model' => $device['model']));
    }

    private function modelSet(array $pdu)
    {
        if (empty($pdu['model']) || !is_array($pdu['model'])) {
            return self::errorResponse($pdu, 'bad_parameter', 'model object is required');
        }
        $uuid = $this->uuid($pdu);
        $this->devices[$uuid] = array(
            'uuid' => $uuid,
            'version' => isset($pdu['model']['version']) ? (string)$pdu['model']['version'] : $this->model->getProtocolVersion(),
            'model' => $pdu['model'],
            'registered_at' => date(DATE_ATOM)
        );
        return $this->ok($pdu, array('dev_uuid' => $uuid));
    }

    private function query(array $pdu)
    {
        $ids = $this->idsFromPdu($pdu);
        $items = array();
        foreach ($ids as $id) {
            $items[] = array(
                'id' => $id,
                'value' => array_key_exists($id, $this->values) ? $this->values[$id] : null,
                'quality' => array_key_exists($id, $this->values) ? 'good' : 'unknown',
                'timestamp' => date(DATE_ATOM)
            );
        }
        return $this->ok($pdu, array('dev_uuid' => $this->uuid($pdu), 'data' => $items));
    }

    private function setData(array $pdu)
    {
        $data = isset($pdu['data']) && is_array($pdu['data']) ? $pdu['data'] : array();
        if (isset($pdu['id'])) {
            $data[] = array('id' => $pdu['id'], 'value' => isset($pdu['value']) ? $pdu['value'] : null);
        }

        $result = array();
        foreach ($data as $item) {
            if (!isset($item['id'])) {
                continue;
            }
            $this->values[(string)$item['id']] = isset($item['value']) ? $item['value'] : null;
            $result[] = array('id' => (string)$item['id'], 'code' => 'OK');
        }

        return $this->ok($pdu, array('dev_uuid' => $this->uuid($pdu), 'result' => $result));
    }

    private function sample(array $pdu)
    {
        $ids = $this->idsFromPdu($pdu);
        if (empty($ids)) {
            $ids = array('010302', '010303', '010305', '010306', '010307', '01031220');
        }
        return $this->ok($pdu, array(
            'dev_uuid' => $this->uuid($pdu),
            'sample' => $this->sampleItems($ids),
            'sample_time' => date(DATE_ATOM)
        ));
    }

    private function statusNotify(array $pdu)
    {
        return $this->ok($pdu, array(
            'dev_uuid' => $this->uuid($pdu),
            'status' => isset($pdu['status']) ? $pdu['status'] : 'online'
        ));
    }

    private function dynamicSampleRegister(array $pdu)
    {
        $subscription = isset($pdu['subscription_id']) ? (string)$pdu['subscription_id'] : uniqid('sample_', false);
        $ids = $this->idsFromPdu($pdu);
        $this->dynamicSamples[$subscription] = array(
            'ids' => $ids,
            'interval' => isset($pdu['interval']) ? (int)$pdu['interval'] : 1000,
            'created_at' => date(DATE_ATOM)
        );
        return $this->ok($pdu, array('subscription_id' => $subscription));
    }

    private function dynamicSampleUnregister(array $pdu)
    {
        $subscription = isset($pdu['subscription_id']) ? (string)$pdu['subscription_id'] : '';
        unset($this->dynamicSamples[$subscription]);
        return $this->ok($pdu, array('subscription_id' => $subscription));
    }

    private function dynamicSample(array $pdu)
    {
        $subscription = isset($pdu['subscription_id']) ? (string)$pdu['subscription_id'] : '';
        $ids = isset($this->dynamicSamples[$subscription]) ? $this->dynamicSamples[$subscription]['ids'] : $this->idsFromPdu($pdu);
        return $this->ok($pdu, array('subscription_id' => $subscription, 'sample' => $this->sampleItems($ids)));
    }

    private function methodCall(array $pdu)
    {
        $callId = isset($pdu['call_id']) ? (string)$pdu['call_id'] : uniqid('method_', false);
        $this->methods[$callId] = array('state' => 'finished', 'progress' => 100, 'result' => 'accepted');
        return $this->ok($pdu, array(
            'call_id' => $callId,
            'progress' => array('percent' => 100, 'state' => 'finished'),
            'result' => array('code' => 'OK', 'value' => 'accepted')
        ));
    }

    private function methodControl(array $pdu)
    {
        $callId = isset($pdu['call_id']) ? (string)$pdu['call_id'] : '';
        return $this->ok($pdu, array('call_id' => $callId, 'state' => isset($pdu['control']) ? $pdu['control'] : 'ack'));
    }

    private function eventRegister(array $pdu)
    {
        $eventId = isset($pdu['event_id']) ? (string)$pdu['event_id'] : uniqid('event_', false);
        $this->events[$eventId] = array('filter' => isset($pdu['filter']) ? $pdu['filter'] : array());
        return $this->ok($pdu, array('event_id' => $eventId));
    }

    private function eventUnregister(array $pdu)
    {
        $eventId = isset($pdu['event_id']) ? (string)$pdu['event_id'] : '';
        unset($this->events[$eventId]);
        return $this->ok($pdu, array('event_id' => $eventId));
    }

    private function eventData(array $pdu)
    {
        return $this->ok($pdu, array(
            'event_id' => isset($pdu['event_id']) ? $pdu['event_id'] : 'event.default',
            'event' => isset($pdu['event']) ? $pdu['event'] : array('level' => 'info', 'message' => 'event accepted')
        ));
    }

    private function idsFromPdu(array $pdu)
    {
        if (isset($pdu['ids']) && is_array($pdu['ids'])) {
            return array_map(function ($item) {
                return is_array($item) && isset($item['id']) ? (string)$item['id'] : (string)$item;
            }, $pdu['ids']);
        }
        if (isset($pdu['data']) && is_array($pdu['data'])) {
            $ids = array();
            foreach ($pdu['data'] as $item) {
                if (is_array($item) && isset($item['id'])) {
                    $ids[] = (string)$item['id'];
                }
            }
            return $ids;
        }
        if (isset($pdu['id'])) {
            return array((string)$pdu['id']);
        }
        return array();
    }

    private function sampleItems(array $ids)
    {
        $items = array();
        foreach ($ids as $id) {
            $items[] = array(
                'id' => $id,
                'value' => array_key_exists($id, $this->values) ? $this->values[$id] : null,
                'timestamp' => date(DATE_ATOM),
                'quality' => array_key_exists($id, $this->values) ? 'good' : 'unknown'
            );
        }
        return $items;
    }
}

class Logger
{
    private $name;

    public function __construct($name)
    {
        $this->name = $name;
    }

    public function info($message, array $context = array())
    {
        $this->log(LOG_INFO, $message, $context);
    }

    public function error($message, array $context = array())
    {
        $this->log(LOG_ERR, $message, $context);
    }

    private function log($priority, $message, array $context)
    {
        openlog($this->name, LOG_PID, LOG_DAEMON);
        syslog($priority, $message . ($context ? ' ' . json_encode($context, JSON_UNESCAPED_SLASHES) : ''));
        closelog();
    }
}
