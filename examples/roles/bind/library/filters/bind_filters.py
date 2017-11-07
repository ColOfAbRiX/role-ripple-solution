#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Filters used by the BIND role
#
# Fabrizio Colonna <colofabrix@tin.it> - 15/03/2017
#

import re


def indent(text, amount=4, ch=' '):
    padding = amount * ch
    return ''.join(padding + line for line in text.splitlines(True))


def compute_config(data, termination=True):
    output = ""
    for item in data:

        # Comment for the user, always on a separate line and on its own
        if 'comment' in item and termination:
            output += "\n// {0}\n".format(item['comment'])
            continue

        # Statement name, first element of a line
        if 'name' in item:
            output += "{0} ".format(item['name'])

        # Value, a text that is printed after the name
        if 'value' in item:
            output += "{0} ".format(item['value'])

        # List of values (computed recursively) separated by a whitespace
        if 'inline' in item:
            res = [compute_config([d], False) for d in item['inline']]
            output += "{0} ".format(' '.join(res))

        # List of options (statement either present or absent) separated by a whitespace
        if 'options' in item:
            res = [compute_config([{'value': d}], False) for d in item['options']]
            output += "{0} ".format(' '.join(res))

        # List of values separated by semicolon
        if 'list' in item:
            res = [compute_config([{'value': d}], False) for d in item['list']]
            output += "{0} ".format(';\n'.join(res))

        # Block inside curly braces
        if 'block' in item:
            output += "{\n%s}" % indent(compute_config(item['block']))

        # Clean trailing whitespaces and manage line termination
        output = '\n'.join([l.rstrip() for l in output.split('\n')])
        if termination and output != '':
            output += ";\n"

    return output


def reverse_dotted_decimals(ipaddress):
    """
    Reverse the order of the decimals in the specified IP-address. E.g.
    "192.168.10" would become "10.168.192"
    """
    return '.'.join(ipaddress.split('.')[::-1])


def is_dns_fqdn(address):
    """
    Check if a DNS name respects the standard FQDN format, terminating witha dot
    """
    return address.endswith('.')


class FilterModule(object):
    """ Ansible core jinja2 filters """

    def filters(self):
        return {
            'reverse_dotted_decimals': reverse_dotted_decimals,
            'compute_config': compute_config,
            'is_dns_fqdn': is_dns_fqdn,
        }

# vim: ft=python:ts=4:sw=4