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

from unittest import mock

from config_tempest.services.octavia import LoadBalancerService
from config_tempest.tests.base import BaseServiceTest


class TestOctaviaService(BaseServiceTest):
    def setUp(self):
        super(TestOctaviaService, self).setUp()
        self.conf = self._get_conf("v2", "v3")
        self.clients = self._get_clients(self.conf)
        self.Service = LoadBalancerService("ServiceName",
                                           "ServiceType",
                                           self.FAKE_URL + "v2.0/",
                                           self.FAKE_TOKEN,
                                           disable_ssl_validation=False)
        self.Service.client = self.FakeServiceClient(
            services={"services": [{"name": "octavia", "enabled": True}]}
        )
        self.conf.set("identity", "region", "regionOne")
        self._fake_service_do_get_method(self.FAKE_LBAAS_PROVIDERS)

    def test_list_drivers(self):
        expected_resp = [
            "amphora:The Octavia Amphora driver.",
            "octavia:Deprecated alias of the Octavia driver.",
        ]
        providers = self.Service.list_drivers()
        self.assertCountEqual(providers, expected_resp)

    @mock.patch("config_tempest.services.services.Services.is_service")
    def test_octavia_service_post_configuration(self, mock_is_service):
        mock_is_service.return_value = True
        self.Service.post_configuration(self.conf, mock_is_service)
        self.assertEqual(self.conf.get("load_balancer", "member_role"),
                         "member")
        self.assertEqual(self.conf.get("load_balancer", "region"),
                         "regionOne")
        self.assertEqual(self.conf.get("load_balancer",
                                       "enabled_provider_drivers"),
                         ("amphora:The Octavia Amphora driver.,"
                          "octavia:Deprecated alias of the Octavia driver."),
                         )
