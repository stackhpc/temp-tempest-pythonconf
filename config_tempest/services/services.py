# Copyright 2013, 2016, 2018 Red Hat, Inc.
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

import urlparse

from base import Service
import boto
import ceilometer
from compute import ComputeService
import config_tempest.constants as C
import horizon
from identity import IdentityService
from image import ImageService
from network import NetworkService
from object_storage import ObjectStorageService
import volume

service_dict = {'compute': ComputeService,
                'image': ImageService,
                'network': NetworkService,
                'object-store': ObjectStorageService,
                'volumev3': volume.VolumeService,
                'identity': IdentityService}


class Services(object):
    def __init__(self, clients, conf, creds):
        self._clients = clients
        self._conf = conf
        self._creds = creds
        self._ssl_validation = creds.disable_ssl_certificate_validation
        self._region = clients.identity_region
        self._services = []
        self.set_catalog_and_url()

        self.discover()

    def discover(self):
        token, auth_data = self._clients.auth_provider.get_auth()

        for entry in auth_data[self.service_catalog]:
            name = entry['type']
            url = self.parse_endpoints(self.get_endpoints(entry), name)

            service_class = self.get_service_class(name)
            service = service_class(name, url, token, self._ssl_validation,
                                    self._clients.get_service_client(name))
            # discover extensions of the service
            service.set_extensions()
            # discover versions of the service
            service.set_versions()

            # default tempest options
            service.set_default_tempest_options(self._conf)

            self._services.append(service)

        service_name = 'volume'
        versions = C.SERVICE_VERSIONS[service_name]['supported_versions']
        self.merge_exts_multiversion_service(service_name, versions)

    def merge_exts_multiversion_service(self, name, versions):
        """Merges extensions of a service given by its name

        Looking for extensions from all versions of the service
        defined by name and merges them to that provided service.

        :param name: Name of the service
        :type name: string
        :param versions: Supported versions
        :type versions: list
        """
        if not self.is_service(name):
            return
        s = self.get_service(name)
        services_lst = []
        for v in versions:
            if self.is_service(name + v):
                services_lst.append(self.get_service(name + v))
        services_lst.append(s)
        s.extensions = self.merge_extensions(services_lst)

    def get_endpoints(self, entry):
        for ep in entry['endpoints']:
            if self._creds.api_version == 3:
                if (ep['region'] == self._region and
                        ep['interface'] == 'public'):
                    return ep
            else:
                if ep['region'] == self._region:
                    return ep
        try:
            return entry['endpoints'][0]
        except IndexError:
            return []

    def set_catalog_and_url(self):
        if self._creds.api_version == 3:
            self.service_catalog = 'catalog'
            self.public_url = 'url'
        else:
            self.service_catalog = 'serviceCatalog'
            self.public_url = 'publicURL'

    def parse_endpoints(self, ep, name):
        """Parse an endpoint(s).

        :param ep: endpoint(s)
        :type ep: dict or list in case of no endpoints
        :param name: name of a service
        :type name: string
        :return: url
        :rtype: string
        """
        # endpoint list can be empty
        if len(ep) == 0:
            url = ""
            C.LOG.info("Service %s has no endpoints", name)
        else:
            url = ep[self.public_url]
        if 'identity' in url:
            url = self.edit_identity_url(ep[self.public_url])
        return url

    def edit_identity_url(self, url):
        """A port and identity version are added to url if contains 'identity'

        :param url: url address of an endpoint
        :type url: string
        :rtype: string
        """

        # self._clients.auth_provider.auth_url stores identity.uri(_v3) value
        # from TempestConf
        port = urlparse.urlparse(self._clients.auth_provider.auth_url).port
        if port is None:
            port = ""
        else:
            port = ":" + str(port)
        replace_text = port + "/identity/" + self._creds.identity_version
        return url.replace("/identity", replace_text)

    def get_service_class(self, name):
        """Returns class name by the service name

        :param name: Codename of a service
        :type name: string
        :return: Class name of the service
        :rtype: string
        """
        return service_dict.get(name, Service)

    def get_service(self, name):
        """Finds and returns a service object

        :param name: Codename of a service
        :type name: string
        :return: Service object
        """
        for service in self._services:
            if service.name == name:
                return service
        return None

    def is_service(self, name):
        """Returns true if a service is available, false otherwise

        :param name: Codename of a service
        :type name: string
        :rtype: boolean
        """
        if self.get_service(name) is None:
            return False
        return True

    def set_service_availability(self):
        # check if volume service is disabled
        if self._conf.has_option('services', 'volume'):
            if not self._conf.getboolean('services', 'volume'):
                C.SERVICE_NAMES.pop('volume')
                C.SERVICE_VERSIONS.pop('volume')
        # check availability of volume backup service
        volume.check_volume_backup_service(self._conf,
                                           self._clients.volume_client,
                                           self.is_service("volumev3"))

        ceilometer.check_ceilometer_service(self._conf,
                                            self._clients.service_client)

        boto.configure_boto(self._conf, s3_service=self.get_service("s3"))

        horizon.configure_horizon(self._conf)

        for service, codename in C.SERVICE_NAMES.iteritems():
            # ceilometer is still transitioning from metering to telemetry
            if service == 'telemetry' and self.is_service('metering'):
                service = 'metering'
            available = str(self.is_service(service))
            self._conf.set('service_available', codename, available)

        # TODO(arxcruz): Remove this once/if we get the following reviews
        # merged in all branches supported by tempestconf, or once/if
        # tempestconf do not support anymore the OpenStack release where
        # those patches are not available.
        # https://review.openstack.org/#/c/492526/
        # https://review.openstack.org/#/c/492525/

        if self.is_service('alarming'):
            self._conf.set('service_available', 'aodh', 'True')
            self._conf.set('service_available', 'aodh_plugin', 'True')

        # TODO(arxcruz): This should be set in compute service, not here,
        # however, it requires a refactor in the code, which is not our
        # goal right now
        self._conf.set('compute-feature-enabled',
                       'attach_encrypted_volume',
                       str(self.is_service('key-manager')))

    def set_supported_api_versions(self):
        # set supported API versions for services with more of them
        for service, service_info in C.SERVICE_VERSIONS.iteritems():
            service_object = self.get_service(service_info['catalog'])
            if service_object is None:
                supported_versions = []
            else:
                supported_versions = service_object.get_versions()
            section = service + '-feature-enabled'
            for version in service_info['supported_versions']:
                is_supported = any(version in item
                                   for item in supported_versions)
                self._conf.set(section, 'api_' + version, str(is_supported))

    def merge_extensions(self, service_objects):
        """Merges extensions from all provided service objects

        :param service_objects:
        :type service_objects: list
        :return: Merged extensions
        :rtype: list
        """
        extensions = []
        for o in service_objects:
            extensions += o.extensions
        return extensions

    def set_service_extensions(self):
        postfix = "-feature-enabled"
        keystone_v3_support = self._conf.get('identity' + postfix, 'api_v3')
        if keystone_v3_support:
            self.get_service('identity').set_identity_v3_extensions()

        for service, ext_key in C.SERVICE_EXTENSION_KEY.iteritems():
            if not self.is_service(service):
                continue
            service_object = self.get_service(service)
            if service_object is not None:
                extensions = ','.join(service_object.get_extensions())
            self._conf.set(service + postfix, ext_key, extensions)
