# Copyright 2019 Red Hat, Inc.
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

from six.moves import configparser

from config_tempest.constants import LOG
from config_tempest.services.base import Service
from config_tempest.users import Users


class OrchestrationService(Service):

    @staticmethod
    def get_service_type():
        return ['orchestration']

    @staticmethod
    def get_codename():
        return 'heat'

    def set_default_tempest_options(self, conf):
        try:
            sec = 'heat_plugin'

            conf.set(sec, 'username', conf.get('identity', 'username'))
            conf.set(sec, 'password', conf.get('identity', 'password'))
            conf.set(sec, 'admin_username', conf.get('auth', 'admin_username'))
            conf.set(sec, 'admin_password', conf.get('auth', 'admin_password'))
            conf.set(sec, 'project_name', conf.get('identity', 'project_name'))
            admin_project_name = conf.get('auth', 'admin_project_name')
            conf.set(sec, 'admin_project_name', admin_project_name)
            conf.set(sec, 'region', conf.get('identity', 'region'))

            v = '3' if conf.get('identity', 'auth_version') == 'v3' else '2'
            if v == '3':
                conf.set(sec, 'auth_url', conf.get('identity', 'uri_v3'))
            else:
                conf.set(sec, 'auth_url', conf.get('identity', 'uri'))
            conf.set(sec, 'auth_version', v)

            domain_name = conf.get('auth', 'admin_domain_name')
            conf.set(sec, 'project_domain_name', domain_name)
            conf.set(sec, 'user_domain_name', domain_name)

            # should be set to True if using self-signed SSL certificates which
            # is a general case
            conf.set(sec, 'disable_ssl_certificate_validation', 'True')
        except configparser.NoOptionError:
            LOG.warning("Be aware that an option required for "
                        "heat_tempest_plugin cannot be set!")

        networks_client = self.client['networks']
        subnets_client = self.client['subnets']
        projects_client = self.client['projects']
        roles_client = self.client['roles']
        users_client = self.client['users']

        heat_network_name = "heat_tempestconf_network"
        heat_subnet_name = "heat_tempestconf_subnet"
        project = conf.get('identity', 'project_name')

        try:
            network_list = networks_client.list_networks()
            heat_network = [network for network in network_list['networks']
                            if network['name'] == heat_network_name]

            if not heat_network:
                project_id = projects_client.get_project_by_name(project)['id']
                heat_network = networks_client.create_network(
                    name=heat_network_name,
                    project_id=project_id)
                heat_network_id = heat_network['network']['id']
                subnets_client.create_subnet(
                    network_id=heat_network_id,
                    ip_version=4,
                    cidr="192.168.199.0/24",
                    name=heat_subnet_name)

            conf.set(sec, 'fixed_network_name', heat_network_name)
        except Exception:
            LOG.warning("Could not create network within the %s project "
                        "needed by heat tempest plugin!", project)

        try:
            users = Users(projects_client, roles_client, users_client, conf)
            username = conf.get('identity', 'username')
            users.give_role_to_user(username, "member")
        except Exception:
            LOG.warning("Could not assign role 'member' to user '%s'!",
                        username)

    def post_configuration(self, conf, is_service):
        if conf.has_section('compute'):
            compute_options = conf.options('compute')
            if 'flavor_ref' in compute_options:
                conf.set('heat_plugin', 'minimal_instance_type',
                         conf.get('compute', 'flavor_ref'))
            if 'flavor_ref_alt' in compute_options:
                conf.set('heat_plugin', 'instance_type',
                         conf.get('compute', 'flavor_ref_alt'))
            if 'image_ref' in compute_options:
                conf.set('heat_plugin', 'minimal_image_ref',
                         conf.get('compute', 'image_ref'))
            if 'image_ref_alt' in compute_options:
                conf.set('heat_plugin', 'image_ref',
                         conf.get('compute', 'image_ref_alt'))
        if conf.has_section('network'):
            network = conf.get('network', 'floating_network_name')
            conf.set('heat_plugin', 'network_for_ssh', network)
            conf.set('heat_plugin', 'floating_network_name', network)
