/**
 * Copyright (C) 2013 OpenMediaVault Plugin Developers
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
// require("js/omv/workspace/form/Panel.js")
// require("js/omv/data/Store.js")
// require("js/omv/data/Model.js")
// require("js/omv/form/plugin/LinkedFields.js")

Ext.define("OMV.module.admin.service.pyload.Settings", {
    extend   : "OMV.workspace.form.Panel",
    requires : [
        "OMV.data.Model",
        "OMV.data.Store"
    ],

    initComponent : function () {
        var me = this;

        me.on('load', function () {
            var checked = me.findField('enable').checked;
            var showtab = me.findField("showtab").checked;
            var parent = me.up('tabpanel');

            if (!parent)
                return;

            var managementPanel = parent.down('panel[title=' + _("Web Interface") + ']');

            if (managementPanel) {
                checked ? managementPanel.enable() : managementPanel.disable();
                showtab ? managementPanel.tab.show() : managementPanel.tab.hide();
            }
        });

        me.callParent(arguments);
    },

    rpcService   : "Pyload",
    rpcGetMethod : "getSettings",
    rpcSetMethod : "setSettings",

    plugins      : [{
        ptype        : "linkedfields",
        correlations : [{
            name       : [
                "port",
            ],
            properties : "!show"
        }]
    }],

    getFormItems : function() {
        var me = this;

        return [{
            xtype    : "fieldset",
            title    : "General settings",
            defaults : {
                labelSeparator : ""
            },
            items : [{
                xtype      : "checkbox",
                name       : "enable",
                fieldLabel : _("Enable"),
                checked    : false
            },{
                xtype      : "checkbox",
                name       : "showtab",
                fieldLabel : _("Show Tab"),
                boxLabel   : _("Show tab containing PyLoad web interface frame."),
                checked    : false
            },{
                xtype: "numberfield",
                name: "port",
                fieldLabel: _("Port"),
                vtype: "port",
                minValue: 1,
                maxValue: 65535,
                allowDecimals: false,
                allowBlank: true,
                value: 8888
            },{
                xtype   : "button",
                name    : "openpyload",
                text    : _("Pyload Web Interface"),
                scope   : this,
                handler : function() {
                    var me = this;
                    var port = me.getForm().findField("port").getValue();
                    var link = "http://" + location.hostname + ":" + port + "/";
                    window.open(link, "_blank");
                },
                margin : "0 0 5 0"
            },{
                border: false,
                html: "<br />"
            }]
        }];
    }
});

OMV.WorkspaceManager.registerPanel({
    id        : "settings",
    path      : "/service/pyload",
    text      : _("Settings"),
    position  : 10,
    className : "OMV.module.admin.service.pyload.Settings"
});