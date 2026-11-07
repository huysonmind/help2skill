---
name: sqlite-utils
description: "Use sqlite-utils to create, query and transform SQLite databases."
---

<!-- help2skill:begin program=sqlite-utils max-chars=30000 (generated from the CLI; edit outside this block) -->
## `sqlite-utils [OPTIONS] COMMAND [ARGS]...`

Commands for interacting with a SQLite database

Options:
- `--version`: Show the version and exit.

Default command: `query`. When the first argument is not a command name, `sqlite-utils ARGS...` runs `sqlite-utils query ARGS...`.

Commands (all levels):
- `sqlite-utils add-column`: Add a column to the specified table
- `sqlite-utils add-foreign-key`: Add a new foreign key constraint to an existing table
- `sqlite-utils add-foreign-keys`: Add multiple new foreign key constraints to a database
- `sqlite-utils add-geometry-column`: Add a SpatiaLite geometry column to an existing table.
- `sqlite-utils analyze`: Run ANALYZE against the whole database, or against specific named indexes and tables
- `sqlite-utils analyze-tables`: Analyze the columns in one or more tables
- `sqlite-utils bulk`: Execute parameterized SQL against the provided list of documents.
- `sqlite-utils convert`: Convert columns using Python code you supply.
- `sqlite-utils create-database`: Create a new empty database file
- `sqlite-utils create-index`: Add an index to the specified table for the specified columns
- `sqlite-utils create-spatial-index`: Create a spatial index on a SpatiaLite geometry column.
- `sqlite-utils create-table`: Add a table with the specified columns.
- `sqlite-utils create-view`: Create a view for the provided SELECT query
- `sqlite-utils disable-fts`: Disable full-text search for specific table
- `sqlite-utils disable-wal`: Disable WAL for database files
- `sqlite-utils drop-index`: Drop an index by index name from the specified table
- `sqlite-utils drop-table`: Drop the specified table
- `sqlite-utils drop-view`: Drop the specified view
- `sqlite-utils dump`: Output a SQL dump of the schema and full contents of the database
- `sqlite-utils duplicate`: Create a duplicate of this table, copying across the schema and all row data.
- `sqlite-utils enable-counts`: Configure triggers to update a _counts table with row counts
- `sqlite-utils enable-fts`: Enable full-text search for specific table and columns
- `sqlite-utils enable-wal`: Enable WAL for database files
- `sqlite-utils extract`: Extract one or more columns into a separate table
- `sqlite-utils index-foreign-keys`: Ensure every foreign key column has an index on it
- `sqlite-utils indexes`: Show indexes for the whole database or specific tables
- `sqlite-utils insert`: Insert records from FILE into a table, creating the table if it does not already exist.
- `sqlite-utils insert-files`: Insert one or more files using BLOB columns in the specified table
- `sqlite-utils install`: Install packages from PyPI into the same environment as sqlite-utils
- `sqlite-utils memory`: Execute SQL query against an in-memory database, optionally populated by imported data
- `sqlite-utils migrate`: Apply pending database migrations.
- `sqlite-utils optimize`: Optimize all full-text search tables and then run VACUUM - should shrink the database file
- `sqlite-utils plugins`: List installed plugins
- `sqlite-utils populate-fts`: Re-populate full-text search for specific table and columns
- `sqlite-utils query` (default command): Execute SQL query and return the results as JSON
- `sqlite-utils rebuild-fts`: Rebuild all or specific full-text search tables
- `sqlite-utils rename-table`: Rename this table.
- `sqlite-utils reset-counts`: Reset calculated counts in the _counts table
- `sqlite-utils rows`: Output all rows in the specified table
- `sqlite-utils schema`: Show full schema for this database or for specified tables
- `sqlite-utils search`: Execute a full-text search against this table
- `sqlite-utils tables`: List the tables in the database
- `sqlite-utils transform`: Transform a table beyond the capabilities of ALTER TABLE
- `sqlite-utils triggers`: Show triggers configured in this database
- `sqlite-utils uninstall`: Uninstall Python packages from the sqlite-utils environment
- `sqlite-utils upsert`: Upsert records based on their primary key.
- `sqlite-utils vacuum`: Run VACUUM against the database
- `sqlite-utils views`: List the views in the database

Full reference for every command: [references/commands.md](references/commands.md). Read only the section of the command you need.
<!-- help2skill:end -->
