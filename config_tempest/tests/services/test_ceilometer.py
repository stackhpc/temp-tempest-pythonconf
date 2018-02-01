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

import ConfigParser

from config_tempest.services import ceilometer
from config_tempest.tempest_conf import TempestConf
from config_tempest.tests.base import BaseServiceTest


class TestCeilometerService(BaseServiceTest):
    def setUp(self):
        super(TestCeilometerService, self).setUp()
        self.conf = TempestConf()

    def test_check_ceilometer_service(self):
        client_service_mock = self.FakeServiceClient(services={})
        ceilometer.check_ceilometer_service(self.conf, client_service_mock)

        self._assert_conf_get_not_raises(ConfigParser.NoSectionError,
                                         "service_available",
                                         "ceilometer")

        client_service_mock = self.FakeServiceClient(services={
            'services': [
                {
                    "name": "ceilometer",
                    "enabled": True
                }
            ]
        })
        ceilometer.check_ceilometer_service(self.conf, client_service_mock)
        self.assertEqual(self.conf.get('service_available', 'ceilometer'),
                         'True')
