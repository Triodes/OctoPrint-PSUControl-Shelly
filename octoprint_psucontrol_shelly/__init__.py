# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import requests
from .backends import LocalGen1Backend, LocalGen2Backend, CloudV1Backend, CloudV2Backend

class PSUControl_Shelly(
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.RestartNeedingPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.SettingsPlugin,
):

    def __init__(self):
        self.config = dict()
        self.transition = False

    def get_settings_defaults(self):
        return dict(
            backend = 'local_gen2',
            server_address = '',
            auth_key = '',
            device_id = '',
            local_address = '',
            enable_auth = False,
            username = '',
            password = '',
            output = 0,
        )

    def on_settings_initialized(self):
        self.reload_settings()

    def reload_settings(self):
        for k, v in self.get_settings_defaults().items():
            if type(v) is str:
                v = self._settings.get([k])
            elif type(v) is int:
                v = self._settings.get_int([k])
            elif type(v) is float:
                v = self._settings.get_float([k])
            elif type(v) is bool:
                v = self._settings.get_boolean([k])

            self.config[k] = v
            self._logger.debug("{}: {}".format(k, v))

    def on_startup(self, host, port):
        psucontrol_helpers = self._plugin_manager.get_helpers("psucontrol")
        if not psucontrol_helpers or 'register_plugin' not in psucontrol_helpers.keys():
            self._logger.warning("The version of PSUControl that is installed does not support plugin registration.")
            return

        self._logger.debug("Registering plugin with PSUControl")
        psucontrol_helpers['register_plugin'](self)

    def send(self, url, data=None, auth=None, json=None):
        response = None
        try:
            if data or json:
                response = requests.post(url, auth=auth, data=data, json=json)
            else:
                response = requests.get(url, auth=auth)
        except (
                requests.exceptions.InvalidURL,
                requests.exceptions.ConnectionError
        ):
            self._logger.error("Unable to communicate with server. Check settings.")
        except Exception:
            self._logger.exception("Exception while making API call")
        else:
            # if data:
            #     self._logger.debug("url={}, data={}, status_code={}, text={}".format(url, data, response.status_code, response.text))
            # else:
            #     self._logger.debug("url={}, status_code={}, text={}".format(url, response.status_code, response.text))
            self._logger.debug("url={}, status_code={}, text={}".format(url, response.status_code, response.text))

            if response.status_code == 401:
                self._logger.warning("Server returned 401 Unauthorized. Check username/password or API key.")
                response = None
            elif response.status_code == 400:
                self._logger.warning("Server returned 400 Bad Request. Check Device ID.")
                response = None

        return response

    def _get_backend(self):
        backend_type = self.config.get('backend')

        match backend_type:
            case 'cloud':
                return CloudV1Backend(self)
            case 'cloud_v2':
                return CloudV2Backend(self)
            case 'local_gen2':
                return LocalGen2Backend(self)
            case 'local_gen1':
                return LocalGen1Backend(self)
            case _:
                raise ValueError(f"Unknown backend type: {backend_type}")

    def change_psu_state(self, state):
        if self.transition:
            # This one is mostly for the Shelly Cloud API which is rather slow.
            self._logger.info("Still in transition between sending and receiving change, not sending command.")
            return

        backend = self._get_backend()
        if not backend:
            self._logger.error("Invalid backend selected.")
            return

        sensing_method = self._settings.global_get(['plugins', 'psucontrol', 'sensingMethod'])
        sensing_plugin = self._settings.global_get(['plugins', 'psucontrol', 'sensingPlugin'])
        if sensing_method == "PLUGIN" and sensing_plugin == "psucontrol_shelly":
            self._logger.debug("PSUControl is using us for sensing")
            self.transition = True

        backend.set_state(state)

    def turn_psu_on(self):
        self._logger.debug("Switching PSU On")
        self.change_psu_state(True)

    def turn_psu_off(self):
        self._logger.debug("Switching PSU Off")
        self.change_psu_state(False)

    def get_psu_state(self):
        self.transition = False
        backend = self._get_backend()
        if not backend:
            self._logger.error("Invalid backend selected.")
            return False

        status = backend.get_state()

        if status == None:
            self._logger.error("Unable to determine status. Check settings.")
            status = False

        return status

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.reload_settings()

    def get_settings_version(self):
        return 2

    def on_settings_migrate(self, target, current=None):
        if current is None or current < 2:
            use_cloud = self._settings.get_boolean(['use_cloud'])
            ng_device = self._settings.get_boolean(['ng_device'])

            if use_cloud:
                backend = 'cloud'
            elif ng_device:
                backend = 'local_gen2'
            else:
                backend = 'local_gen1'

            self._settings.set(['backend'], backend)

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def get_update_information(self):
        return dict(
            psucontrol_shelly=dict(
                displayName="PSU Control - Shelly",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="Triodes",
                repo="OctoPrint-PSUControl-Shelly",
                current=self._plugin_version,

                # update method: pip w/ dependency links
                pip="https://github.com/Triodes/OctoPrint-PSUControl-Shelly/archive/{target_version}.zip"
            )
        )

__plugin_name__ = "PSU Control - Shelly"
__plugin_pythoncompat__ = ">=3,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PSUControl_Shelly()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
