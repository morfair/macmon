# macmon
Store MAC-address learned by your L2-switches

### Dependencies:
 - PostgREST (https://postgrest.com/);
 - python3;
 - SNMPTT (http://snmptt.sourceforge.net/);
 - Snmptrapd (http://net-snmp.sourceforge.net/docs/man/snmptrapd.html);


## Database
Use PostgreSQL database with PostgREST HTTP REST API . User PostgREST documentation for installation. Note yoy may want to use Nginx in add-on.

Create database and roles:
```
CREATE DATABASE mac_address;
CREATE ROLE common;
```
`common` is a simple user, your may use other. Change database connection to `mac_address`  and continue:
```
CREATE SCHEMA api_mac_address;
ALTER SCHEMA api_mac_address OWNER TO common;

CREATE SCHEMA basic_auth;
ALTER SCHEMA basic_auth OWNER TO common;

CREATE EXTENSION IF NOT EXISTS pgcrypto;


```
