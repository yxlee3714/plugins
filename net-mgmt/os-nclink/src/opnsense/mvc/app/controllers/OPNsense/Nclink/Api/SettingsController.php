<?php

namespace OPNsense\Nclink\Api;

use OPNsense\Base\ApiMutableModelControllerBase;

class SettingsController extends ApiMutableModelControllerBase
{
    protected static $internalModelName = 'nclink';
    protected static $internalModelClass = '\OPNsense\Nclink\Nclink';
}
