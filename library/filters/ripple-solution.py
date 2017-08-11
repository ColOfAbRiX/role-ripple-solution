#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Fabrizio Colonna <colofabrix@tin.it> - 02/09/2016
#

import six
import json
from distutils.util import strtobool

def build_ripple_extra(value, rdbms='postgres', extra_vars={}):
    """
    Build some useful values from the raw configuration data. This allows to use
    uniform data structures that can be accessed with loops and that are more
    generic. See tasks/datastructs.yml
    """

    # Extra custom values in the root of the dictionary
    for e_key, e_value in extra_vars.iteritems():
        value[e_key] = e_value

    # Service name
    if value['name'] == 'ilp_ledger':
        value['name'] = "%s_%s" % (value['name'], value['currency'].lower())
        value['description'] = "%s %s" % (value['description'], value['currency'].upper())

    # HTTPS Enabled
    use_https = value.get('config', {}).get('use_https', False)
    if isinstance(use_https, six.string_types):
        use_https = bool(strtobool(str(use_https.lower())))
    value['use_https'] = use_https

    # Protocol
    service_protocol = "http"
    default_port = 80
    if use_https:
        service_protocol += "s"
        default_port = 443
    value['protocol'] = service_protocol

    # Address
    service_address = value['host']
    if value['port'] != default_port:
        service_address = "%s:%s" % (service_address, value['port'])
    value['address'] = service_address

    # Full URL
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

    # Return
    return value


def list_encrypted_passwords(secrets_json):
    """
    Creates a list of encrypted passwords from the JSON loaded from secrets.json
    """
    output = []
    try:
        secrets_json = json.loads(secrets_json)
    except:
        secrets_json = {}

    # Database password
    output.append({
        'key': secrets_json.get('encrypted_database_password_key', ''),
        'password': secrets_json.get('encrypted_database_password', '')
    })

    # RabbitMQ
    output.append({
        'key': secrets_json.get('encrypted_mq_password_key', ''),
        'password': secrets_json.get('encrypted_mq_password', '')
    })

    # External credentials
    credentials_key = secrets_json.get('external_credentials_password_key', '')
    for k, v in secrets_json.get('external_credentials', {}).iteritems():
        output.append({
            'key': credentials_key,
            'password': v.get('encrypted_password', '')
        })

    return output


def list_clear_passwords(key, database=None, rmq=None, partners=[]):
    """
    Creates a list of cleartext passwords from the available data
    """
    output =[]

    # Database password
    output.append({'key': key, 'password': database})

    # RabbitMQ
    output.append({'key': key,'password': rmq})

    # External credentials
    for v in partners:
        output.append({'key': key,'password': v['password']})

    return output


class FilterModule(object):
    """ Ansible jinja2 filters """

    def filters(self):
        return {
            'build_ripple_extra': build_ripple_extra,
            'list_encrypted_passwords': list_encrypted_passwords,
            'list_clear_passwords': list_clear_passwords
        }

# vim: ft=python:ts=4:sw=4