# Installing PostgreSQL on Raspbian
*Tested on Raspbian-Lite 2017.11.29*

First, update apt.

```
sudo apt update
```

Next, install the database.

```
sudo apt install postgresql libpq-dev postgresql-client postgresql-client-common -y
```

Now, backup the file `/etc/postgresql/9.6/main/pg_hba.conf` using the following command:

```
sudo cp /etc/postgresql/9.6/main/pg_hba.conf /etc/postgresql/9.6/main/pg_hba.conf.bak
```

(Your version information might differ, depending on the OS you're using.)

Then edit the file to allow for connections in the local network by adding the following line to the end of the file: (Note: Only do this if you want other IPs on the local network to have access to the database.)

```
host     all     all     192.168.0.0/24     md5
```

(Obviously, you'll need to change the IP as necessary to reflect your network configuration.)

Next, backup the file `/etc/postgresql/9.6/main/postgresql.conf` using the following command:

```
sudo cp /etc/postgresql/9.6/main/postgresql.conf /etc/postgresql/9.6/main/postgresql.conf.bak
```

Then edit `/etc/postgresql/9.6/main/postgresql.conf` and change the line

```
#listen_addresses = 'localhost'
```

to say

```
listen_addresses = '*'
```

This requires that you un-comment the line and change its value.

Now you'll have to restart the PostgreSQL service for these changes to take effect.

```
sudo service postgresql restart
```

Now, switch to the postgres user to configure the database.

```
sudo su postgres
```

Now create a user for the database.

```
createuser spider -P --interactive
```

When asked if the user should be a superuser, say no. When asked if they can create databases, say yes. Same for creating new roles; answer yes.

Now, go ahead and create the database for TorSpider to use.

```
createdb -O spider TorSpider
```

Now, we'll need to install the required libraries for Python to connect to the PostgreSQL server. First, drop out of the postgres user account with `ctrl-d`. Next, install psycopg2 using `pip3 install psycopg2`.
