==============
Default values
==============

``python-tempestconf`` defines some options by default in order to simplify
general executions, because not so many options need to be defined in each
run of ``python-tempestconf``, for example in CI.

Here is the list of tempest options, which are set by default:

.. code-block:: ini

    [DEFAULT]
    debug = true
    use_stderr = false
    log_file = tempest.log

    [identity]
    username = demo
    password = secrete
    project_name = demo
    alt_username = alt_demo
    alt_password = secrete
    alt_project_name = alt_demo
    disable_ssl_certificate_validation = true

    [scenario]
    img_dir = etc

    [auth]
    tempest_roles = _member_
    admin_username = admin
    admin_project_name = admin
    admin_domain_name = Default

    [object-storage]
    reseller_admin_role = ResellerAdmin

    [oslo-concurrency]
    lock_path = /tmp

    [compute-feature-enabled]
    # Default deployment does not use shared storage
    live_migration = false
    live_migrate_paused_instances = true
    preserve_ports = true

    [network-feature-enabled]
    ipv6_subnet_attributes = true
