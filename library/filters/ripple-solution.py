#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Fabrizio Colonna <colofabrix@tin.it> - 02/09/2016
#

import six
import json
from urlparse import urlparse
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

    # Data specific to the host and not the service endpoint which can be
    # different (See the attribute use_url)
    value['host_data'] = {
       'use_https': value['use_https'],
       'protocol': value['protocol'],
       'host': value['host'],
       'port': value['port'],
       'address': value['address'],
       'url': value['url']
    }

    # Using a given URL
    if value.get('use_url', '') != '':
        url = urlparse(value['use_url'])
        value.update({
           'use_https': (url.scheme == 'https'),
           'protocol': url.scheme,
           'host': url.hostname,
           'port': url.port,
           'address': url.netloc,
           'url': value['use_url']
        })

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
    value['crt_file'] = "%s.crt" % value['crt_prefix']
    value['key_file'] = "%s.key" % value['crt_prefix']

    # Return
    return value


def list_encrypted_rc_passwords(secrets_json):
    """
    Creates a list of encrypted passwords from the JSON loaded from secrets.json.
    This is related to Ripple Connect.
    The output sequence is: [database, rabbitmq, external credentials]
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


def list_clear_rc_passwords(key, database=None, rmq=None, partners=[]):
    """
    Creates a list of cleartext passwords from the available data.
    This is related to Ripple Connect.
    The output sequence is: [database, rabbitmq, external_credentials...]
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


def list_encrypted_ilp_passwords(config_ilp_json):
    """
    Creates a list of encrypted passwords from the JSON loaded from config-ilp.json
    This is related to all other componets but Ripple Connect.
    The output sequence is: [validator_db_uri, validator_ed25519_key, fx_connector_db_uri,
    fx_connector_quote_hmac_key, ledgers_db_uri...]
    """
    output = []
    try:
        config_ilp_json = json.loads(config_ilp_json)
    except:
        config_ilp_json = {}

    # Extract first level
    ilp_validator = config_ilp_json.get('validator', {})
    fx_connector = config_ilp_json.get('connector', {})
    ilp_ledgers = []
    for key in sorted([k for k in config_ilp_json.keys()]):
        if key.startswith('ledger'):
            ilp_ledgers.append(config_ilp_json[key])

    # ILP Validator DB URI
    output.append({
        'key': ilp_validator.get('ENCRYPTED_VALIDATOR_DB_URI_DECRYPTION_KEY', ''),
        'string': ilp_validator.get('ENCRYPTED_VALIDATOR_DB_URI', '')
    })
    # ILP Validator ED25519 secret key
    output.append({
        'key': ilp_validator.get('ENCRYPTED_VALIDATOR_ED25519_SECRET_KEY_DECRYPTION_KEY', ''),
        'string': ilp_validator.get('ENCRYPTED_VALIDATOR_ED25519_SECRET_KEY', '')
    })

    # FX Connector DB URI
    output.append({
        'key': fx_connector.get('ENCRYPTED_CONNECTOR_DB_URI_DECRYPTION_KEY', ''),
        'string': fx_connector.get('ENCRYPTED_CONNECTOR_DB_URI', '')
    })
    # FX Connector Quote HMAC key
    output.append({
        'key': fx_connector.get('ENCRYPTED_CONNECTOR_QUOTE_HMAC_KEY_DECRYPTION_KEY', ''),
        'string': fx_connector.get('ENCRYPTED_CONNECTOR_QUOTE_HMAC_KEY', '')
    })

    # Ledgers DB URI
    for ledger in ilp_ledgers:
        output.append({
            'key': ledger.get('ENCRYPTED_LEDGER_DB_URI_DECRYPTION_KEY', ''),
            'string': ledger.get('ENCRYPTED_LEDGER_DB_URI', '')
        })

    return output


def list_clear_ilp_passwords(key, ilpv_info, ilpv_ed25519, fxc_info, fxc_hmac, ledgers_info):
    """
    Creates a list of cleartext passwords from the available data.
    This is related to all other componets but Ripple Connect.
    The output sequence is: [validator_db_uri, validator_ed25519_key, fx_connector_db_uri,
    fx_connector_quote_hmac_key, ledgers_db_uri...]
    """
    output = []

    # ILP Validator DB URI
    output.append({'key': key, 'string': ilpv_info['db_string']})
    # ILP Validator ED25519 secret key
    output.append({'key': key, 'string': ilpv_ed25519})

    # ILP Validator DB URI
    output.append({'key': key, 'string': fxc_info['db_string']})
    # ILP Validator Quote HMAC key
    output.append({'key': key, 'string': fxc_hmac})

    # Ledgers DB URI
    for ledger in ledgers_info:
        output.append({'key': key, 'string': ledger['db_string']})

    return output

from ansible.errors import AnsibleFilterError
from ansible.module_utils.six.moves.urllib.parse import urlsplit
from ansible.utils import helpers

def split_url(value, query='', alias='urlsplit'):
    """
    This same function will be available from Ansible 2.4 with this same interface.
    For more information see:
    https://docs.ansible.com/ansible/devel/playbooks_filters.html#url-split-filter
    """
    url = urlsplit(value)
    results = {
        'hostname': url.hostname,
        'netloc': url.netloc,
        'username': url.username,
        'password': url.password,
        'path': url.path,
        'port': url.port,
        'scheme': url.scheme,
        'query': url.query,
        'fragment': url.fragment
    }

    if query:
        if query not in results:
            raise AnsibleFilterError(alias + ': unknown URL component: %s' % query)
        return results[query]
    else:
        return results


class FilterModule(object):
    """ Ansible jinja2 filters """

    def filters(self):
        return {
            'build_ripple_extra': build_ripple_extra,
            'list_encrypted_rc_passwords': list_encrypted_rc_passwords,
            'list_clear_rc_passwords': list_clear_rc_passwords,
            'list_encrypted_ilp_passwords': list_encrypted_ilp_passwords,
            'list_clear_ilp_passwords': list_clear_ilp_passwords,
            'urlsplit': split_url
        }

# vim: ft=python:ts=4:sw=4