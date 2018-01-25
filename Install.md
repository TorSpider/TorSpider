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

Switch to the postgres user to configure the database.

```
sudo su postgres
```

Now create a user for the database. Creating a user named after an existing account automatically grants them access to the database.

```
createuser pi -P --interactive
```

When asked if the user should be a superuser, say no. When asked if they can create databases, say yes. Same for creating new roles; answer yes.

Now, we'll need to install the required libraries for Python to connect to the PostgreSQL server. First, drop out of the postgres user account with `ctrl-d`. Next, install psycopg2 using `pip3 install psycopg2`.

Finally, we'll need to modify the script so that it reflects the remote database and user.
