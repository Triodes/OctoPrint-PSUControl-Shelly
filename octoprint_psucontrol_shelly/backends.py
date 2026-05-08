# coding=utf-8
import re as regex
import json
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

class ShellyBackend:
    def __init__(self, plugin):
        self._plugin = plugin

    @property
    def _config(self):
        return self._plugin.config

    @property
    def _logger(self):
        return self._plugin._logger

    def set_state(self, state):
        raise NotImplementedError

    def get_state(self):
        raise NotImplementedError

class LocalGen1Backend(ShellyBackend):
    def set_state(self, state):
        output = self._config['output']
        url = self._config['local_address'] + '/relay/' + str(output) + '?turn=' + ("on" if state else "off")
        url = url if regex.match(r'^http[s]*://', url) else 'http://' + url

        auth = None
        if self._config['enable_auth']:
            auth = HTTPBasicAuth(self._config['username'], self._config['password'])

        self._plugin.send(url=url, auth=auth)

    def get_state(self):
        output = self._config['output']
        url = self._config['local_address'] + '/relay/' + str(output)
        url = url if regex.match(r'^http[s]*://', url) else 'http://' + url

        auth = None
        if self._config['enable_auth']:
            auth = HTTPBasicAuth(self._config['username'], self._config['password'])

        response = self._plugin.send(url=url, auth=auth)
        if not response:
            return False

        try:
            json_data = response.json()
            return json_data.get('ison')
        except Exception:
            self._logger.exception("Error while parsing status response")
            return None

class LocalGen2Backend(ShellyBackend):
    def set_state(self, state):
        output = self._config['output']
        url = self._config['local_address'] + '/rpc/Switch.Set?id=' + str(output) + '&on=' + str(state).lower()
        url = url if regex.match(r'^http[s]*://', url) else 'http://' + url

        auth = None
        if self._config['enable_auth']:
            auth = HTTPDigestAuth(self._config['username'], self._config['password'])

        self._plugin.send(url=url, auth=auth)

    def get_state(self):
        output = self._config['output']
        url = self._config['local_address'] + '/rpc/Switch.GetStatus?id=' + str(output)
        url = url if regex.match(r'^http[s]*://', url) else 'http://' + url

        auth = None
        if self._config['enable_auth']:
            auth = HTTPDigestAuth(self._config['username'], self._config['password'])

        response = self._plugin.send(url=url, auth=auth)
        if not response:
            return False

        try:
            json_data = response.json()
            return json_data.get('output')
        except Exception:
            self._logger.exception("Error while parsing status response")
            return None

class CloudV1Backend(ShellyBackend):
    def set_state(self, state):
        output = self._config['output']
        url = self._config['server_address'] + '/device/relay/control'
        url = url if regex.match(r'^http[s]*://', url) else 'https://' + url

        data = dict(
            auth_key = self._config['auth_key'],
            id = self._config['device_id'],
            turn = ("on" if state else "off"),
            channel = str(output),
        )

        self._plugin.send(url=url, data=data)

    def get_state(self):
        output = self._config['output']
        url = self._config['server_address'] + '/device/status'
        url = url if regex.match(r'^http[s]*://', url) else 'https://' + url

        data = dict(
            auth_key = self._config['auth_key'],
            id = self._config['device_id'],
        )

        response = self._plugin.send(url=url, data=data)
        if not response:
            return False

        try:
            json_data = response.json()
            return json_data['data']['device_status']['switch:' + str(output)]['output']
        except Exception:
            self._logger.exception("Error while parsing status response")
            return None

class CloudV2Backend(ShellyBackend):
    def set_state(self, state):
        output = self._config['output']
        url = self._config['server_address'] + '/v2/devices/api/set/switch'
        url = url if regex.match(r'^http[s]*://', url) else 'https://' + url

        data = dict(
            auth_key = self._config['auth_key'],
            id = self._config['device_id'],
            channel = output,
            on = state,
        )

        self._plugin.send(url=url, json=data)

    def get_state(self):
        output = self._config['output']
        url = self._config['server_address'] + '/v2/devices/api/get'
        url = url if regex.match(r'^http[s]*://', url) else 'https://' + url

        data = dict(
            auth_key = self._config['auth_key'],
            ids = [self._config['device_id']],
            select = ["status"],
            pick = {
                "status": ["switch:" + str(output)]
            }
        )

        response = self._plugin.send(url=url, json=data)
        if not response:
            return False

        try:
            json_data = response.json()
            return json_data[0]['status']['switch:' + str(output)]['output']
        except Exception:
            self._logger.exception("Error while parsing status response")
            return None