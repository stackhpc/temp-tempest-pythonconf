# Copyright 2013 Red Hat, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import requests
import urlparse

from base import VersionedService
from config_tempest.constants import LOG


class IdentityService(VersionedService):
    def __init__(self, name, service_url, token, disable_ssl_validation,
                 client=None):
        super(IdentityService, self).__init__(
            name, service_url, token, disable_ssl_validation, client)
        self.extensions_v3 = []
        version = ''
        if 'v2' in self.service_url:
            version = '/v2.0'
            url_parse = urlparse.urlparse(self.service_url)
            self.service_url = '{}://{}{}'.format(url_parse.scheme,
                                                  url_parse.netloc, version)

    def set_extensions(self):
        if 'v2' in self.service_url:
            body = self.do_get(self.service_url + '/extensions')
            body = json.loads(body)
            values = body['extensions']['values']
            self.extensions = map(lambda x: x['alias'], values)
            return
        # Keystone api changed in v3, the concept of extensions changed. Right
        # now, all the existing extensions are part of keystone core api, so,
        # there's no longer the /extensions endpoint. The extensions that are
        # stable, are enabled by default, the ones marked as experimental are
        # disabled by default. Checking the tempest source, there's no test
        # pointing to extensions endpoint, so I am very confident that this
        # will not be an issue. If so, we need to list all the /OS-XYZ
        # extensions to identify what is enabled or not. This would be a manual
        # check every time keystone change, add or delete an extension, so I
        # rather prefer to set empty list here for now.
        self.extensions = []

    def set_identity_v3_extensions(self):
        """Returns discovered identity v3 extensions

        As keystone V3 uses a JSON Home to store the extensions.
        This method implements a different discovery method.

        :param keystone_v3_url: Keystone V3 auth url
        :return: A list with the discovered extensions
        """
        try:
            r = requests.get(self.service_url,
                             verify=False,
                             headers={'Accept': 'application/json-home'})
        except requests.exceptions.RequestException as re:
            LOG.error("Request on service '%s' with url '%s' failed",
                      'identity', self.service_url)
            raise re
        ext_h = 'http://docs.openstack.org/api/openstack-identity/3/ext/'
        res = [x for x in json.loads(r.content)['resources'].keys()]
        ext = [ex for ex in res if 'ext' in ex]
        ext = [str(e).replace(ext_h, '').split('/')[0] for e in ext]
        self.extensions_v3 = list(set(ext))

    def set_versions(self):
        super(IdentityService, self).set_versions(top_level=False)

    def get_extensions(self):
        all_ext_lst = self.extensions + self.extensions_v3
        return list(set(all_ext_lst))

    def deserialize_versions(self, body):
        try:
            versions = []
            for v in body['versions']['values']:
                    # TripleO is in transition to v3 only, so the environment
                    # still returns v2 versions even though they're deprecated.
                    # Therefor pick only versions with stable status.
                if v['status'] == 'stable':
                    versions.append(v['id'])
            return versions
        except KeyError:
            return [body['version']['id']]

    def configure_keystone_feature_flags(self, conf):
        """Set keystone feature flags based upon version ID."""
        supported_versions = self.get_versions()
        if len(supported_versions) <= 1:
            return
        for version in supported_versions:
            major, minor = version.split('.')[:2]
            # Enable the domain specific roles feature flag.
            # For more information see:
            # https://developer.openstack.org/api-ref/identity/v3
            if major == 'v3' and int(minor) >= 6:
                conf.set('identity-feature-enabled',
                         'forbid_global_implied_dsr',
                         'True')