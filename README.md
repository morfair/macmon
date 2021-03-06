# macmon
Store MAC-address learned by your L2-switches in database and get alarm from Zabbix.

### Dependencies:
 - PostgreSQL 9.6;
 - PostgreSQL contrib (https://www.postgresql.org/docs/9.6/static/contrib.html);
 - PostgREST (https://postgrest.com/);
 - PostgreSQL JWT (https://github.com/michelp/pgjwt);
 - python3;
 - SNMPTT (http://snmptt.sourceforge.net/);
 - Snmptrapd (http://net-snmp.sourceforge.net/docs/man/snmptrapd.html);

## Screenshots
![alt text](https://raw.githubusercontent.com/morfair/macmon/master/doc/mac_list.png)

## Database
Use PostgreSQL database with PostgREST HTTP REST API . Use PostgREST documentation for installation. Note you may want to use Nginx as front-end.

Create database and roles:
```
CREATE DATABASE mac_address;
CREATE ROLE common;
```
`common` is a simple user, your may use other. Change database connection to `mac_address`  and continue:
```
CREATE SCHEMA api_mac_address;
ALTER SCHEMA api_mac_address OWNER TO common;
```

Install `pgjwt` module from https://github.com/michelp/pgjwt.

First we’ll need a table to keep track of our users:
```
CREATE SCHEMA basic_auth;
ALTER SCHEMA basic_auth OWNER TO common;

CREATE TABLE basic_auth.users (
    id serial,
    email text NOT NULL,
    pass text NOT NULL,
    role name NOT NULL,
    CONSTRAINT users_email_check CHECK ((email ~* '^.+@.+\..+$'::text)),
    CONSTRAINT users_pass_check CHECK ((length(pass) < 512)),
    CONSTRAINT users_role_check CHECK ((length((role)::text) < 512))
);
```
We would like the role to be a foreign key to actual database roles, owever PostgreSQL does not support these constraints against the `pg_roles` table. We’ll use a trigger to manually enforce it.
```
CREATE FUNCTION basic_auth.check_role_exists() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  if not exists (select 1 from pg_roles as r where r.rolname = new.role) then
    raise foreign_key_violation using message =
      'unknown database role: ' || new.role;
    return null;
  end if;
  return new;
end
$$;

CREATE CONSTRAINT TRIGGER ensure_user_role_exists AFTER INSERT OR UPDATE ON basic_auth.users NOT DEFERRABLE INITIALLY IMMEDIATE FOR EACH ROW EXECUTE PROCEDURE basic_auth.check_role_exists();
```
Next we’ll use the pgcrypto extension and a trigger to keep passwords safe in the `users` table.
```
CREATE EXTENSION IF NOT EXISTS pgcrypto;
COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';

CREATE FUNCTION basic_auth.encrypt_pass() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  if tg_op = 'INSERT' or new.pass <> old.pass then
    new.pass = crypt(new.pass, gen_salt('bf'));
  end if;
  return new;
end
$$;

CREATE TRIGGER encrypt_pass BEFORE INSERT OR UPDATE ON basic_auth.users FOR EACH ROW EXECUTE PROCEDURE basic_auth.encrypt_pass();
```
It returns the database role for a user if the email and password are correct:
```
CREATE FUNCTION basic_auth.user_role(email text, pass text) RETURNS name
    LANGUAGE plpgsql
    AS $$
begin
  return (
  select role from basic_auth.users
   where users.email = user_role.email
     and users.pass = crypt(user_role.pass, users.pass)
  );
end;
$$;
```
Create public user interface for Log-In:
```
CREATE EXTENSION pgjwt;
```
```
CREATE TYPE basic_auth.jwt_token AS (
  token text
);
```
and then:
```
CREATE FUNCTION api_mac_address.login(email text, pass text) RETURNS basic_auth.jwt_token
    LANGUAGE plpgsql
    AS $$
declare
  _role name;
  result basic_auth.jwt_token;
begin
  -- check email and password
  select basic_auth.user_role(email, pass) into _role;
  if _role is null then
    raise invalid_password using message = 'invalid user or password';
  end if;

  select sign(
      row_to_json(r), current_setting('app.jwt_secret')
    ) as token
    from (
      select _role as role, login.email as email,
         extract(epoch from now())::integer + 60*60 as exp
    ) r
    into result;
  return result;
end;
$$;
ALTER FUNCTION api_mac_address.login(email text, pass text) OWNER TO common;
```
Set permissions:
```
CREATE ROLE web_anon;
CREATE ROLE authenticator WITH LOGIN NOINHERIT;
GRANT web_anon TO authenticator;
GRANT common TO authenticator;

GRANT USAGE ON SCHEMA api_mac_address TO authenticator;
GRANT USAGE ON SCHEMA api_mac_address TO web_anon;
GRANT USAGE ON SCHEMA basic_auth TO web_anon;
GRANT USAGE ON SCHEMA basic_auth TO authenticator;
GRANT ALL ON FUNCTION api_mac_address.login(email text, pass text) TO authenticator;
GRANT SELECT ON TABLE basic_auth.users TO web_anon;
GRANT SELECT ON TABLE basic_auth.users TO authenticator;
GRANT SELECT ON TABLE pg_catalog.pg_authid TO web_anon;
```

Your JWT secret is stored as a property of the database `app.jwt_secret`. For update:
```
ALTER DATABASE mac_address SET "app.jwt_secret" TO 'reallyreallyreallyreallyverysafe';
```

Front-end user add:
```
INSERT INTO basic_auth.users (email, pass, role) VALUES ('admin@local.domain', 'SuperPass', 'common');
```

Next create our app-table:
```
CREATE TABLE api_mac_address.macs (
    id serial,
    mac macaddr NOT NULL,
    host inet NOT NULL,
    host_vendor character varying(255),
    vlan integer,
    port character varying(24),
    datetime timestamp without time zone DEFAULT now() NOT NULL,
    "desc" text,
    status integer DEFAULT 0 NOT NULL
);
ALTER TABLE api_mac_address.macs OWNER TO common;
```
## PostgREST
This is `postgrest.conf` file:
```
db-uri = "postgres://authenticator:pass@pgsql-server.local.domain:5432/mac_address"
db-schema = "api_mac_address"
db-anon-role = "web_anon"
db-pool = 10

# server-host = "*4"
server-host = "127.0.0.1"

server-port = 5000

## base url for swagger output
# server-proxy-uri = ""

## choose a secret to enable JWT auth
## (use "@filename" to load from separate file)
jwt-secret = "reallyreallyreallyreallyverysafe"
# secret-is-base64 = false
# jwt-aud = "your_audience_claim"

## limit rows in response
# max-rows = 1000

## stored proc to exec immediately after auth
# pre-request = "stored_proc_name"
```
Start it:
```
root@webserver:/opt/postgrest# ./postgrest postgrest.conf 
Listening on port 5000
Attempting to connect to the database...
Connection successful

```
Then you can proxy it with nginx:
```
location /rpc/ {
 proxy_pass      http://127.0.0.1:5000;
}

location /macs {
 proxy_pass      http://127.0.0.1:5000;
}
```

## SNMPTT
Install  SNMPTT, for Debian:
```
apt-get install snmptt
```
Copy `snmp.conf*` files from snmptt repo folder to `/etc/snmp` (for Debian). Copy scripts to `/opt/snmptt_mac_notification` directory. If your choose another scripts diretory, edit `snmp.conf*` files.
Edit `snmptt.ini` according it's manual. Some settings:
```
net_snmp_perl_enable = 1
date_time_format = %H:%M:%S %Y/%m/%d

snmptt_conf_files = <<END
/etc/snmp/snmptt.conf
/etc/snmp/snmptt.conf.dlink
/etc/snmp/snmptt.conf.cisco
END
```
In `dlink_mac_notification_parse.py` script change PostgREST API server settings.

## SNMPTRAPD
Install SNMPTRAPD, for Debian:
```
apt-get install snmptrapd
```
Edit `/etc/snmp/snmptrapd.conf` file:
```
disableAuthorization yes
traphandle default /usr/sbin/snmptt
```
Then restart service:
```
/etc/init.d/snmptrapd restart
```

## Switches
### D-Link
For *DES-3200* in web-interface go Configuration - MAC Notification Settings - MAC Notification Global Settings - Enable, MAC Notification Port Settings - Enable on all ports.

### Cisco
For *Cisco Catalyst 3750* in console:
```
snmp-server enable traps mac-notification change move threshold
snmp-server host 192.168.0.2 public mac-notification snmp
mac address-table notification change
interface range GigabitEthernet 1/0/1-24
! (config-if-range):
 snmp trap mac-notification change added
```
