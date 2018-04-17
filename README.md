# macmon
Store MAC-address learned by your L2-switches

### Dependencies:
 - PostgreSQL;
 - PostgREST (https://postgrest.com/);
 - PostgreSQL JWT (https://github.com/michelp/pgjwt);
 - python3;
 - SNMPTT (http://snmptt.sourceforge.net/);
 - Snmptrapd (http://net-snmp.sourceforge.net/docs/man/snmptrapd.html);


## Database
Use PostgreSQL database with PostgREST HTTP REST API . Use PostgREST documentation for installation. Note yoy may want to use Nginx in add-on.

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
COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';

-- https://github.com/michelp/pgjwt
CREATE EXTENSION IF NOT EXISTS pgjwt;
COMMENT ON EXTENSION pgjwt IS 'JSON Web Token API for Postgresql';

CREATE TYPE public.jwt_token AS (
 token text
);

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

CREATE TABLE api_mac_address.macs (
    id integer NOT NULL,
    mac macaddr NOT NULL,
    host inet NOT NULL,
    unit integer NOT NULL,
    port integer NOT NULL,
    datetime timestamp without time zone DEFAULT now() NOT NULL,
    "desc" text,
    status integer DEFAULT 0 NOT NULL
);
ALTER TABLE api_mac_address.macs OWNER TO common;

CREATE TABLE basic_auth.users (
    email text NOT NULL,
    pass text NOT NULL,
    role name NOT NULL,
    id integer NOT NULL,
    CONSTRAINT users_email_check CHECK ((email ~* '^.+@.+\..+$'::text)),
    CONSTRAINT users_pass_check CHECK ((length(pass) < 512)),
    CONSTRAINT users_role_check CHECK ((length((role)::text) < 512))
);
ALTER TABLE basic_auth.users OWNER TO common;


CREATE TRIGGER encrypt_pass BEFORE INSERT OR UPDATE ON basic_auth.users FOR EACH ROW EXECUTE PROCEDURE basic_auth.encrypt_pass();

```
