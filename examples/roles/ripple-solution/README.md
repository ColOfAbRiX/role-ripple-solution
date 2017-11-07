Role Name
=========

Ripple Solution installation and configuration

Role Variables
--------------

See the defaults/main.yml file, all variables are toroughly documented.

Dependencies
------------

No dependencies, although using the role ssl-certs instead of the internal management is highly recommended.

Example Playbook
----------------

    - hosts: servers
      roles:
         - role: ripple-solution

License
---------------------------------

MIT

Author Information
------------------

Fabrizio Colonna <colofabrix@tin.it>.
