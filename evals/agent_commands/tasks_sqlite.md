Write the exact `sqlite-utils` command (sqlite-utils version 4.2.1) for each task. The database file is data.db unless stated. One command per task.

1. Insert people.csv into table "people" with primary key "id", replacing rows whose id already exists, and keeping every column as TEXT (no type detection).
2. In table "orders": rename column "amt" to "amount", make it FLOAT, and drop column "tmp". Only print the SQL that would run; do not change the database.
3. Move the columns "country" and "region" of table "places" into a new lookup table named "locations", with the foreign key column in "places" named "location_id".
4. Enable FTS5 full-text search on the "title" and "body" columns of table "articles", using the porter tokenizer, with triggers that keep the index up to date.
5. Show at most 10 rows of table "events" whose status equals a named parameter s="failed" (use a parameter, not string interpolation), only the columns "id" and "created", newest "created" first, as a formatted table.
6. Load a.csv and b.csv into an in-memory database, run "select * from a join b on a.id = b.id", and also save that in-memory database to out.db.
7. Uppercase the "title" column of table "posts" with Python code, writing the result to a new column "title_upper" instead of overwriting, and only preview the result on the first rows without changing anything.
8. Create a unique index named "idx_users_email" on users(email) that does nothing if it already exists.
