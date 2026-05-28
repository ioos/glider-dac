# vsftpd Setup

Provides an example setup with vsftpd.

If PAM authentication against a PostgreSQL database with the User model is desired,
[pam-pgsql](https://github.com/pam-pgsql/pam-pgsql) must be installed and operational
within the PAM library paths.

If SELinux is enabled and set to enforcing on the target system, ensure that the desired
FTP directory has the appropriate SELinux type, of `public_content_rw_t` i.e.:
`ls -dZ /data/submission`

If it does not display the aforementioned type, as a superuser, run:
`chcon -R -t public_content_rw_t /data/submission`

You will also need to allow FTP to make database connections:

`setsebool -P ftpd_connect_db 1`

This directory provides the following files:

- `vsftpd.conf` - A minimal vsftpd configuration. It is highly recommended to uncomment and adapt the TLS portions if using in production settings.  Recommended path is `/etc/vsftpd/vsftpd.conf`
- `pam.d/vsftpd` - A vsftpd PAM configuration requiring `pam_postgres` PAM module.  Required to be loaded by PAM, and thus recommended path is `/etc/pam.d/vsftpd`.
- `pam_vsftpd.conf` - A configuration file containing the connection details to the PostgreSQL instance.  Path is referred to by the previously mentioned vsftpd file and by default is `/etc/pa_vsftpd.conf`.
