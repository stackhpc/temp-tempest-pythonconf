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

from config_tempest.services.base import VersionedService
import json


class LoadBalancerService(VersionedService):
    def set_versions(self):
        super(LoadBalancerService, self).set_versions(top_level=False)

    def set_default_tempest_options(self, conf):
        conf.set('load_balancer', 'enable_security_groups', 'True')
        conf.set('load_balancer', 'admin_role', 'admin')
        conf.set('load_balancer', 'RBAC_test_type', 'owner_or_admin')

    @staticmethod
    def get_service_type():
        return ['load-balancer']

    @staticmethod
    def get_codename():
        return 'octavia'

    def list_drivers(self):
        """List lbaas drivers"""
        body = self.do_get(self.service_url + '/v2/lbaas/providers')
        body = json.loads(body)
        names = [
            '{p[name]}:{p[description]}'.format(p=i) for i in body['providers']
        ]
        return names

    def post_configuration(self, conf, is_service):
        if not conf.has_option('auth', 'tempest_roles') \
                or conf.get('auth', 'tempest_roles') in ['', None]:
            conf.set('load_balancer', 'member_role', 'member')
        else:
            conf.set('load_balancer', 'member_role',
                     conf.get('auth', 'tempest_roles').split(',')[0])
        conf.set('load_balancer', 'region', conf.get('identity', 'region'))
        conf.set('load_balancer',
                 'enabled_provider_drivers',
                 ','.join(self.list_drivers()))
