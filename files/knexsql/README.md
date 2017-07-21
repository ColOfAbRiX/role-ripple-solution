

## Make a test DB

```
# With postgres, a database is required.  Use 'postgres' when creating a new db.
export KNEXSQL_DB=postgres://client_user:client_password@postgres94.cojrajw6pfyj.us-west-2.rds.amazonaws.com:5432/postgres

echo "CREATE DATABASE test_db" | node index.js
```

```
export KNEXSQL_DB=mssql://client_user:client_password@mssql2012.cojrajw6pfyj.us-west-2.rds.amazonaws.com:1433

echo "CREATE DATABASE test_db" | node index.js
```

## Example command lines:

```
DEBUG=knexsql KNEXSQL_DB=postgres://client_user:client_password@postgres94.cojrajw6pfyj.us-west-2.rds.amazonaws.com:5432/test_db node index.js
```

```
DEBUG=knexsql KNEXSQL_DB=mssql://client_user:client_password@mssql2012.cojrajw6pfyj.us-west-2.rds.amazonaws.com:1433/test_db node index.js
```
