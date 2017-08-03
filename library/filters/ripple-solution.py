#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Fabrizio Colonna <colofabrix@tin.it> - 02/09/2016
#

import six
from distutils.util import strtobool

def build_ripple_extra(value, rdbms='postgres', extra_vars={}):
    """
    Build some useful values from the raw configuration data
    """

    # Service URL
    default_port = 80
    service_protocol = "http"
    use_https = value.get('config', {}).get('use_https', False)
    if isinstance(use_https, six.string_types):
        use_https = bool(strtobool(str(use_https.lower())))
    if use_https:
        service_protocol += "s"
        default_port = 443

    service_address = value['host']
    if value['port'] != default_port:
        service_address = "%s:%s" % (service_address, value['port'])

    value['address'] = service_address
    value['protocol'] = service_protocol
    value['url'] = "%s://%s" % (service_protocol, service_address)

    # DB string
    db_string = "%s://%s:%s@%s:%s/%s" % (
        rdbms,
        value['db_user'],
        value['db_pass'],
        value['db_host'],
        value['db_port'],
        value['db_name']
    )
    value['db_string'] = db_string

    # DB administrator string
    db_admin_string = "%s://%s:%s@%s:%s/%s" % (
        rdbms,
        value['db_admin_user'],
        value['db_admin_pass'],
        value['db_host'],
        value['db_port'],
        value['db_name']
    )
    value['db_admin_string'] = db_admin_string

    # SSL certs names
    value['crt_file'] = "%s-crt.pem" % value['crt_prefix']
    value['key_file'] = "%s-key.pem" % value['crt_prefix']

    # Extra custom values in the root of the dictionary
    for e_key, e_value in extra_vars.iteritems():
        value[e_key] = e_value

    # Return
    return value


class FilterModule(object):
    """ Ansible jinja2 filters """

    def filters(self):
        return {
            'build_ripple_extra': build_ripple_extra
        }

# vim: ft=python:ts=4:sw=4