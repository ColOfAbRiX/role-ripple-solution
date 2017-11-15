# ripple-solution

Ansible role to install and configure a complete [Ripple Solution](https://ripple.com/) environment.

The role can configure all the Ripple Solution components (Ripple Connect, ILP Ledgers, FX Connector, ILP Validator) independently and:

 - it can configure a machine as liquidity provider or liquidity consumer;
 - it can configure one or more components per machine;
 - it supports scenarios with a load balancer and/or a reverse proxy;
 - it can create a simple set of certificates for the simplest setups;
 - it can encrypt all the sensitive data of the configuration files if needed.

The role does not:

 - open and manage firewall ports;
 - configure DNS overrides to redirect the traffic from the reverse proxy.
 - create advanced SSL configurations (like using Alternative Subjects);

Known bugs and limitations:

 - the roles supports Ripple Solution versions `3.0.x`, `3.1.x`, `3.2.x`;
 - it supports only PostgreSQL as DB backend (but it's ready for extensions);

## Requirements

The role requires RHEL/CentOS 7 to work.

Although not strictly necessary, it is highly recommended to use the role [role-ssl-certs](https://github.com/ColOfAbRiX/role-ssl-certs) to create and manage the SSL certificates in complex scenarios, like with a load balancer and reverse proxy, and the role [role-bind](https://github.com/ColOfAbRiX/role-bind) to create DNS overrides in setups with a reverse proxy.

The role comes with a custom set of Python filters, [ripple-solution.py](library/filters/ripple-solution.py), used by the role for several configuration steps.
The python file must be copied in the Ansible home path `${ANSIBLE_HOME}` or inside the library path defined by the variable [filter_plugins](https://docs.ansible.com/ansible/latest/intro_configuration.html#filter-plugins) of the ansible.cfg configuration file. If the file is missing, Ansible will complain throwing a "`no filter named xxx`" error.

## Role Variables

The roles has an extensive documentation of the variables in the [default configuration](defaults/main.yml) file, including their default values and some examples. A full set of examples is given in the [examples/](examples) directory.

Just as a quick summary, there are 5 sets of variables used to configure each component:

 - **Ripple Solution** (`ripple_solution*`): Values generic to all the project;
 - **Ripple Connect** (`ripple_connect*`): Values to configure Ripple Connect;
 - **ILP Ledgers** (`ilp_ledgers*`): Values to configure ILP Ledgers;
 - **ILP Validator** (`ilp_validator*`): Values to configure ILP Validator;
 - **FX Connector** (`fx_connector*`): Values to configure FX Connector.

## Dependencies

No dependencies, although using the roles [role-ssl-certs](https://github.com/ColOfAbRiX/role-ssl-certs) and [role-bind](https://github.com/ColOfAbRiX/role-bind) is highly recommended.

## Examples

### Example playbook

This example shows how to use the role together with the two other recommended roles [role-ssl-certs](https://github.com/ColOfAbRiX/role-ssl-certs) and [role-bind](https://github.com/ColOfAbRiX/role-bind). Note that when clustering Ripple Solution, the role ssl-certs must be run with `serial: 1`.

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

**NOTE:** examples are still work in progress.

The [examples/](examples) directory contains the configuration for several scenarios and there is a full description of the configuration in there:

 * Basic configuration
    - One liquidity provider with one currency
    - No reverse proxy
    - No load balancers
 * Reverse proxy configuration
    - One liquidity provider with one currency
    - One reverse proxy per component for public access
    - No load balancers
 * Load balancer configuration
    - One redundant liquidity provider (2 instances) with one currency
    - No reverse proxy
    - One load balancer per component
 * Partner connectivity
    - One liquidity provider with 2 currencies
    - One liquidity consumer with 2 currencies
    - No reverse proxy
    - No load balancers
 * Multiple providers
    - First liquidity provider with 1 currency
    - Second liquidity provider with 1 currencies
    - One liquidity consumer with 2 currencies
    - No reverse proxy
    - No load balancers
 * Full production example
    - One redundant liquidity provider (2 instances) with 2 currencies
    - One redundant liquidity consumer (2 instances) with 2 currencies
    - One reverse proxy per component for public access
    - One load balancer per component

The examples are meant to be run on AWS using [Terraform](https://www.terraform.io) to create the instances, but the machines can be created by any other mean as long as they are present and:

 - the machines are reachable via SSH using the names present in the inventory;
 - the user `ansible` is present on the machines;
 - the user `ansible` is able to sudo to `root` without a password.

## Internal steps

Ripple is a complex system and it is really useful to understand the steps that the role will undertake because there are many possible cases and behaviours. This allows an easier configuration and troubleshooting of the system too.

Each of these high level steps are performed by one YAML file in the [tasks/](tasks/) so that it's easier to identify the problem.

### [Data structures](tasks/00-datastructs.yml)

This step is responsible of:

 - gathering information for the components from various sources;
 - process the information (build additional information, filter existing data, present data in a different format) depending on their purpose;
 - build uniform datastructures.

The final datastructures are then accessed using loops or other control structures across the role. This is one of the most important step because it creates the data used by everything else.

### [Sanity checks](tasks/01-checks.yml)

This step checks that all the required information is available before the role starts actioning the tasks and it provide an early fail for errors.

### [Installation](tasks/02-install.yml)

This step install the Ripple Solution package and performs other system operation like configuring systemd (when present), log rotation, installation of custom scripts and more.

### DB Reset

If requested setting the variable `ripple_solution_reset_db` to `True`, this task will completely erase the data and drop all the database so that a fresh installation can be performed.

The file that is loaded depends on the chosen RDBMS.

### DB Pre-configuration

This step initializes the database with operations like creating schemas, users, assigning permissions, hardening the DB and so on.

The file that is loaded depends on the chosen RDBMS.

### [Schema installation](tasks/05-databases.yml)

This step initializes the actual database content using the SQL files provided with the Ripple package itself.

The step has a built-in check so that the initialisation happens only once.

### DB Post-configuration

Similar to the pre-configuration step, this step performs post installation steps like granting permissions to users on the objects created on the previous step.

The file that is loaded depends on the chosen RDBMS.

### [Certificates](tasks/07-certificates.yml)

This step is responsible of working with SSL certificates used by Ripple.

The tasks in the file first copy existing certificates and keys from the local Ansible repository to the target machine. When this step is done they'll create the missing items.

The role will always create certificates using a Root CA.

When creating new certificates, the step will first create a Root CA and then it will use the latter to create all the other certificates. If the Root CA is missing but the other certificates are present, the role will discard them and create new ones with the Root CA it just generated.

### [Keys](tasks/08-keys.yml)

This step takes care of the keys used by the various components. It creates the missing keys or it can use the keys provided with variables.

### [Encryption and Hashing](tasks/09-encryption.yml)

This file takes care of encrypting the values that go into the configuration files, but only if necessary.

The Ripple script `encrypt_string.js` creates different outputs every time it's run for the same password and this makes the file `secrets.json` to change. A change in a configuration file prompts Ansible to restart Ripple but this is usually not a desired behaviour. The tasks of the step takes care of recognising when a real change of configuration requires an update of the configuration and a restart.

The step also creates the hashes that will go in the `secrets.json` file.

### [Configuration](tasks/10-config.yml)

The configuration files used by Ripple are created in this step, putting together and in a JSON format the information available in Ansible.

### [Initialisation](tasks/11-init.yml)

This step has the important task of making sure the all the Ripple Solution services are up and running and to restart them only when necessary.

### [Ledger Accounts](tasks/12-accounts.yml)

The last step creates the accounts on the ledgers configured on the system.

As an additional feature the step directly modifies the DB to make sure that updated fingerprints and information are set correctly. Bypassing the Ripple API in this way is very important when a change happens and you need to make sure your installation reflects it.

## License

MIT

## Author Information

[Fabrizio Colonna](mailto:colofabrix@tin.it)
