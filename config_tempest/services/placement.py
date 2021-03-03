# Copyright 2020 Red Hat, Inc.
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

from config_tempest.services.base import VersionedService


class PlacementService(VersionedService):
    def set_versions(self):
        super(PlacementService, self).set_versions(top_level=False)

    def set_default_tempest_options(self, conf):
        # set microversions
        m_versions = self.filter_api_microversions(max_version='max_version')
        conf.set(
            'placement', 'min_microversion', m_versions['min_microversion'])
        conf.set(
            'placement', 'max_microversion', m_versions['max_microversion'])

    @staticmethod
    def get_service_type():
        return ['placement']

    @staticmethod
    def get_codename():
        return 'placement'
