# ripple-solution

Ansible role to install and configure a complete Ripple Solution environment.

The role can configure all the Ripple Solution components (Ripple Connect, ILP Ledgers, FX Connector, ILP Validator) indipendently and:

 - it can configure a machine as Liquidity Provider or Consumer;
 - it can configure one or more components per machine;
 - it supports the scenarion when using a load balancer;
 - it can create a simple set of certificates for the simplest setups.

The role does not:

 - open and manage firewall ports;
 - configure DNS overrides to redirect the traffic from the reverse proxy.
 - create advanced SSL configurations (like using Alternative Subjects);

## Requirements

The role requires RHEL/CentOS 7 to work.

Although not strictly necessary, it is highly recommended to use the [ColOfAbRiX/role-ssl-certs](https://github.com/ColOfAbRiX/role-ssl-certs) to create and manage the SSL certificate in complex scenarios, like with a load balancer, and [ColOfAbRiX/role-bind](https://github.com/ColOfAbRiX/role-bind) to create DNS overrides in setups with a reverse proxy.

The role comes with a custom set of Python filters, [ripple-solution.py](library/filters/ripple-solution.py), used by the role to build the BIND configuration.
The python file must be copied in the Ansible home path <code>${ANSIBLE_HOME}</code> or inside the library path defined by the variable [filter_plugins](https://docs.ansible.com/ansible/latest/intro_configuration.html#filter-plugins) of the [ansible.cfg](https://docs.ansible.com/ansible/latest/intro_configuration.html) configuration file. If the file is missing, Ansible will complain throwing a "<code>no filter named xxx</code>" error.

## Role Variables

The role uses several variables that is difficult to exmplain here.

The roles has an extensive documentation of the variables in the [default configuration](defaults/main.yml) file, including their default values and some examples, and a full set of examples is given in the [examples/](examples) directory.

There are 5 sets of variables used to configure each component:

 - **Ripple Solution** (`ripple_solution*`): Values generic to all the project;
 - **Ripple Connect** (`ripple_connect*`): Values to configure Ripple Connect;
 - **ILP Ledgers** (`ilp_ledgers*`): Values to configure ILP Ledgers;
 - **ILP Validator** (`ilp_validator*`): Values to configure ILP Validator;
 - **FX Connector** (`fx_connector*`): Values to configure FX Connector.

## Dependencies

No dependencies, although using the roles [ColOfAbRiX/role-ssl-certs](https://github.com/ColOfAbRiX/role-ssl-certs) and [ColOfAbRiX/role-bind](https://github.com/ColOfAbRiX/role-bind) is highly recommended.

## Examples

### Example plabook

```Yaml
- hosts: servers
  serial: 1
  roles:
     - role: ssl-certs

- hosts: servers
  roles:
     - role: bind
     - role: ripple-solution
```

### Configuration example

The [examples/](examples) directory contains the configuration for several scenarios:

 * Basic configuration
    - One provider with one currency
    - No reverse proxy
    - No load balancers
 * Reverse proxy configuration
    - One provider with one currency
    - One reverse proxy per component for public access
    - No load balancers
 * Load balancer configuration
    - One redundant provider (2 instances) with one currency
    - One load balancer per component
    - No reverse proxy
 * Partner connectivity
    - One conumer with 2 currencies
    - One provider with 2 currencies
    - No load balancers
 * Full production example
    - One redundant conumer (2 instances) with 2 currencies
    - One redundant provider (2 instances) with 2 currencies
    - One load balancer per component

The examples are mean to be run on AWS using [Terraform](https://www.terraform.io) to create the instances, but the machines can be created by any other mean as long as they are present and:

 - reachable via SSH with the names present in the inventory;
 - the user "ansible" is present on the machines and is able to sudo to root without a password.

## License

MIT

## Author Information

[Fabrizio Colonna](mailto:colofabrix@tin.it)
