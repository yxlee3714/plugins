<?php

namespace OPNsense\Nclink;

use OPNsense\Base\IndexController as BaseIndexController;

class IndexController extends BaseIndexController
{
    public function indexAction()
    {
        $this->view->pick('OPNsense/Nclink/index');
    }
}
