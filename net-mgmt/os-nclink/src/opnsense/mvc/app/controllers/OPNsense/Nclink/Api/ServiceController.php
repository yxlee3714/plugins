<?php

namespace OPNsense\Nclink\Api;

use OPNsense\Base\ApiControllerBase;
use OPNsense\Core\Backend;
use OPNsense\Nclink\Nclink;

class ServiceController extends ApiControllerBase
{
    public function startAction()
    {
        return $this->runBackend('nclink start');
    }

    public function stopAction()
    {
        return $this->runBackend('nclink stop');
    }

    public function restartAction()
    {
        return $this->runBackend('nclink restart');
    }

    public function statusAction()
    {
        $status = array('running' => false, 'connections' => 0, 'port' => 8088);
        $statusFile = '/var/run/nclink.status.json';
        if (is_readable($statusFile)) {
            $decoded = json_decode(file_get_contents($statusFile), true);
            if (is_array($decoded)) {
                $status = array_merge($status, $decoded);
            }
        }

        $model = new Nclink();
        $status['port'] = $model->getListenPort();
        return array('status' => $status);
    }

    public function pduAction()
    {
        $model = new Nclink();
        $agent = $model->getAgent();
        $payload = $this->request->getPost('pdu');
        $pdu = json_decode($payload === null ? '{}' : $payload, true);
        if (!is_array($pdu)) {
            return array('code' => 'NG', 'reason' => 'bad_request', 'message' => 'invalid JSON');
        }
        return $agent->handlePDU($pdu);
    }

    private function runBackend($action)
    {
        try {
            $backend = new Backend();
            $response = trim($backend->configdRun($action));
        } catch (\Throwable $e) {
            return array(
                'result' => 'failed',
                'output' => get_class($e) . ': ' . $e->getMessage()
            );
        }
        return array(
            'result' => stripos($response, 'failed') === false ? 'success' : 'failed',
            'output' => $response
        );
    }
}
