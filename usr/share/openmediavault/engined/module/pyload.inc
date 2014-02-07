<?php

/**
 * Copyright (C)      2013 OpenMediaVault Plugin Developers
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

require_once "openmediavault/module.inc";
require_once "openmediavault/config.inc";
require_once "openmediavault/error.inc";
require_once "openmediavault/util.inc";
require_once "openmediavault/initscript.inc";

class OMVModulePyload extends OMVModuleServiceAbstract
    implements OMVINotifyListener, OMVIModuleServiceStatus {

    public function getName() {
        return "PyLoad";
    }

    public function getStatus() {
        global $xmlConfig;
        $xpath  = "//services/pyload";
        $object = $xmlConfig->get($xpath);
        if (is_null($object))
                        throw new OMVException(OMVErrorMsg::E_CONFIG_GET_OBJECT_FAILED, $xpath);

        $cmd = "/etc/init.d/pyload status";
        $this->exec($cmd, $output);
        return array(
            "name"    => $this->getName(),
            "title"   => gettext("PyLoad"),
            "enabled" => boolval($object['enable']),
            "running" => (strpos($output[0], 'is running') > 0)
        );
    }

    public function startService() {
        global $xmlConfig;
        $xpath  = "//services/pyload";
        $object = $xmlConfig->get($xpath);
        if (is_null($object))
                        throw new OMVException(OMVErrorMsg::E_CONFIG_GET_OBJECT_FAILED, $xpath);

        if(FALSE === boolval($object['enable']))
            return;

                $initd = new OMVSysVInitScript("pyload", TRUE);
                $initd->exec();
    }

    public function stopService() {
        global $xmlConfig;
        $xpath  = "//services/pyload";
        $object = $xmlConfig->get($xpath);
        if (is_null($object))
                        throw new OMVException(OMVErrorMsg::E_CONFIG_GET_OBJECT_FAILED, $xpath);

        if(TRUE === boolval($object['enable']))
            return;

                $initd = new OMVSysVInitScript("pyload", FALSE);
                $initd->exec();
    }

    public function bindListeners(OMVNotifyDispatcher $dispatcher) {
        $dispatcher->addListener(
            OMV_NOTIFY_MODIFY,
            "org.openmediavault.services.pyload",
            array($this, "setDirty"));
    }
}

// Register module
$moduleMgr = &OMVModuleMgr::getInstance();
$moduleMgr->registerModule(new OMVModulePyload());