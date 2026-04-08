<?php

namespace OPNsense\Nclink\Api;

use OPNsense\Base\ApiControllerBase;

class DeviceController extends ApiControllerBase
{
    public function listAction()
    {
        $output = shell_exec("/usr/local/opnsense/scripts/nclink_agent.py status");
        return json_decode($output, true);
    }

    public function startAction()
    {
        shell_exec("configctl nclink start");
        return ["status" => "started"];
    }

    public function stopAction()
    {
        shell_exec("configctl nclink stop");
        return ["status" => "stopped"];
    }
}
