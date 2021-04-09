# Copyright 2018 Red Hat, Inc.
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

from config_tempest import constants as C
from config_tempest.services.base import VersionedService

from tempest.lib import exceptions


class ShareService(VersionedService):

    def set_versions(self):
        url, top_level = self.no_port_cut_url()
        body = self.do_get(url, top_level=top_level)
        self.versions_body = json.loads(body)
        self.versions = self.deserialize_versions(self.versions_body)

    def get_share_pools(self, detail=False):
        url = self.service_url + '/scheduler-stats/pools'
        if detail:
            url += '/detail'
        body = self.do_get(url)
        body = json.loads(body)
        return body

    def set_default_tempest_options(self, conf):
        if 'v2' in self.service_url:
            m_vs = self.filter_api_microversions()
            conf.set('share', 'min_api_microversion', m_vs['min_microversion'])
            conf.set('share', 'max_api_microversion', m_vs['max_microversion'])

        try:
            pools = self.get_share_pools(detail=True)['pools']
        except exceptions.Forbidden:
            C.LOG.warning("User has no permissions to list back-end storage "
                          "pools - storage back-ends can't be discovered.")
            return
        if pools:
            backends = set()
            enable_protocols = set()
            dhss = set()
            capability_snapshot_support = set()
            capability_create_share_from_snapshot_support = set()
            for pool in pools:
                backends.add(pool['backend'])
                pool_capabilities = pool['capabilities']
                protocol = pool_capabilities['storage_protocol'].lower()
                enable_protocols.update(protocol.split('_'))
                dhss.add(pool_capabilities['driver_handles_share_servers'])
                capability_snapshot_support.add(
                    pool_capabilities['snapshot_support'])
                capability_create_share_from_snapshot_support.add(
                    pool_capabilities['create_share_from_snapshot_support'])

            conf.set('share', 'backend_names', ','.join(backends))
            conf.set('share', 'enable_protocols', ','.join(enable_protocols))

            # NOTE(gouthamr): manila tests can be run with
            # driver_handles_share_servers set to either True or False,
            # not both at the same time. Lets err on the side of caution and
            # set this to True if any DHSS=True backend is present.
            conf.set('share', 'multitenancy_enabled', str(any(dhss)))

            # Optional capabilities/features:
            conf.set('share', 'run_snapshot_tests',
                     str(any(capability_snapshot_support)))
            conf.set('share', 'capability_snapshot_support',
                     str(any(capability_snapshot_support)))
            conf.set('share', 'capability_create_share_from_snapshot_support',
                     str(any(capability_create_share_from_snapshot_support)))

            if len(backends) > 1:
                conf.set('share', 'multi_backend', 'True')

    def get_unversioned_service_type(self):
        return 'share'

    @staticmethod
    def get_codename():
        return 'manila'

    def get_feature_name(self):
        return 'share'

    @staticmethod
    def get_service_type():
        return ['share', 'sharev2']
