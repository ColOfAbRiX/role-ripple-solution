#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Fabrizio Colonna <colofabrix@tin.it> - 02/09/2016
#

import six
import json

from urlparse import urlparse
from distutils.util import strtobool
from ansible.module_utils.six.moves.urllib.parse import urlsplit


def extract_url_info(data_dict, url_type):
    """
    Extract URL information from a key in a dictionary that contains a URL. It
    then builds another key containing the split information.
    """
    url_key = "%s_url" % url_type
    data_key = "%s_data" % url_type
    data_dict = data_dict.copy()

    if data_dict.get(url_key, '') != '':
        url = urlparse(data_dict[url_key])

        use_https = (url.scheme == 'https')
        port = 80 if not use_https else 443
        if url.port is not None:
            port = url.port

        data_dict[data_key] = {
           'use_https': use_https,
           'protocol': url.scheme,
           'host': url.hostname,
           'port': port,
           'address': url.netloc,
           'url': data_dict[url_key]
        }
        data_dict.update(data_dict[data_key])

    else:
        data_dict[url_key] = ''
        data_dict[data_key] = {}

    return data_dict


def build_ripple_extra(value, rdbms='postgres', extra_vars={}):
    """
    Build some useful values from the raw configuration data. This allows to use
    uniform data structures that can be accessed with loops and that are more
    generic. See tasks/datastructs.yml
    """

    # Extra custom values in the root of the dictionary. The actual value on "value"
    # takes precedence
    for e_key, e_value in extra_vars.iteritems():
        if not e_key in value:
            value[e_key] = e_value

    # Add the currency name to the ledgers
    if 'ledger' in value['name'].lower():
        value['name'] = "ilp_ledger_%s" % value['currency'].lower()
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
    value['host_url'] = "%s://%s" % (service_protocol, service_address)

    # Extract and save the host specific data
    value = extract_url_info(value, 'host')
    # Using a given Load Balancer. It has priority over the host data
    value = extract_url_info(value, 'load_balancer')
    # Using a given Reverse Proxy. It has priority over the load balancer data
    value = extract_url_info(value, 'reverse_proxy')

    # Deciding if HOST_MAP is needed and what values to assign
    value['map_component'] = {}
    if value['reverse_proxy_url'] != '':
        # Map the reverse proxy url to the host url
        if value['reverse_proxy_url'] != value['host_url']:
            value['map_component'].update({
                'from': value['reverse_proxy_data'],
                'to': value['host_data']
            })

        # If the load balancer is present, it must be used instead of the host data
        if value['load_balancer_url'] != '' and value['reverse_proxy_url'] != value['load_balancer_url']:
            value['map_component'].update({
                'from': value['reverse_proxy_data'],
                'to': value['load_balancer_data']
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


def ripple_connect_ledgers(local_ledgers, rc_ledger_user, remote_ledgers):
    """
    Incorporates together local and remote ledgers so that they always fall in
    the same currency on the configuration file.
    """
    def add_entry(result, currency, address, account):
        entry = {'address': address, 'account': account}
        currency = currency.upper()

        if currency not in ledgers:
            result.update({currency: [entry]})
        else:
            result[currency].append(entry)

    ledgers = {}

    # Add local ledgers
    for ledger in local_ledgers:
        if not ledger['enabled'] or not ledger.get('install_local', False):
            continue
        currency = ledger['currency']
        address = "%s.%s" % (currency.lower(), ledger['host'])
        account = "%s/account/%s" % (ledger['url'], rc_ledger_user)
        add_entry(ledgers, currency, address, account)

    # Add remote ledgers
    for ledger in remote_ledgers:
        add_entry(ledgers, ledger['currency'], ledger['url'], ledger['account'])

    return ledgers


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


def reduce_or(values, start=0):
    """
    Used to check if a JSON comma is needed at the end of a section
    """
    if start > len(values) - 1:
        return False
    return reduce(lambda x, y: x or y, values[start:], False)


class FilterModule(object):
    """ Ansible jinja2 filters """

    def filters(self):
        return {
            'build_ripple_extra': build_ripple_extra,
            'list_encrypted_rc_passwords': list_encrypted_rc_passwords,
            'list_clear_rc_passwords': list_clear_rc_passwords,
            'list_encrypted_ilp_passwords': list_encrypted_ilp_passwords,
            'list_clear_ilp_passwords': list_clear_ilp_passwords,
            'ripple_connect_ledgers': ripple_connect_ledgers,
            'reduce_or': reduce_or,
            'urlsplit': split_url
        }

# vim: ft=python:ts=4:sw=4