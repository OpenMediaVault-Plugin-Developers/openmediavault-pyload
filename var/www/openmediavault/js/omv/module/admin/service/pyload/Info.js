/**
 * Copyright (C) 2013-2014 OpenMediaVault Plugin Developers
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
// require("js/omv/WorkspaceManager.js")
// require("js/omv/workspace/panel/Panel.js")

Ext.define("OMV.module.admin.service.pyload.Info", {
    extend : "Ext.panel.Panel",

    initComponent : function() {
        var me = this;
        var link = 'http://' + location.hostname + ':8888/';

        me.html = "<ul>" +
                    "<li>" + _("Default username:  admin") + "</li>" +
                    "<li>" + _("Default password:  openmediavault") + "</li>" +
                  "</ul>" +
                  "<ul>" +
                    "<li><a href='" + link + "' target='_blank'>" +
                    _("Open in a new window") + "</a></li>" +
                  "</ul>";

        me.callParent(arguments);
    }
});

OMV.WorkspaceManager.registerPanel({
    id        : "info",
    path      : "/service/pyload",
    text      : _("Information"),
    position  : 30,
    className : "OMV.module.admin.service.pyload.Info"
});
