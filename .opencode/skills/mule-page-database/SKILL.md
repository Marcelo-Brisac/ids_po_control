---
name: mule-page-database
description: Manage a database attached to a dynamic Mule Page. Use when the user wants to build a Node.js web app that needs server-side persistence. Combines with the mule-pages skill, which handles publishing. Not for static pages or dynamic pages without a database.
---

# Mule Page Database

A dynamic Mule Page can be provisioned with a hosted MySQL-compatible database (TiDB). The connection string is injected into the page runtime as `process.env.DATABASE_URL` at publish time.

## Error Handling

If publish returns 400 `quota-exceeded` with `your plan does not include the database feature`, **stop using this skill entirely**. Call `suggest_subscription` with feature `mule-page-database` so the user sees a subscription hint, and tell the user the database feature requires a paid plan. Do not silently substitute another persistence approach — that's the user's decision, not the agent's.

If publish returns 400 `database feature is not configured`, the platform itself is misconfigured. Report and stop.

If publish returns 400 `code=database-not-ready`, the database is still provisioning. Wait and retry. Uncommon, since `publish.py --with-database` polls until ready before publishing.

## Workflow

1. Write the Node app (see **Code pattern**).
2. Publish via the `mule-pages` skill with `--with-database`. First publish takes 30–60s extra for provisioning.
3. Verify the URL.
4. Iterate by re-publishing. Publish is upsert; the database persists across re-deploys.

## No local preview

`DATABASE_URL` is injected only into the page runtime, and the database is reachable only from there. Running the server in the sandbox will throw on the missing variable. Use re-publish to iterate.

## Code pattern

The app creates its own schema at startup; the platform does not run migrations.

```javascript
const mysql = require('mysql2/promise');

const url = process.env.DATABASE_URL;
if (!url) throw new Error('DATABASE_URL is required');
const pool = mysql.createPool(url);

async function migrate() {
  await pool.execute(`
    CREATE TABLE IF NOT EXISTS todos (
      id INT AUTO_INCREMENT PRIMARY KEY,
      title VARCHAR(255) NOT NULL,
      done BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `);
}

(async () => {
  await migrate();
  // ... start HTTP server on 0.0.0.0
})();
```

Use `CREATE TABLE IF NOT EXISTS` for idempotency. For schema changes after the first deploy, a bare `ALTER TABLE` will fail on the second run; gate ALTERs or use a migration library.

## DATABASE_URL format

```
mysql://USER:PASS@HOST:PORT/DBNAME?ssl={"rejectUnauthorized":true}
```

Literal env-var value, not a shell-pasteable string. `mysql2` parses the `?ssl=` JSON. Redact the password when logging.

## Constraints

| | |
|---|---|
| Engine | TiDB (MySQL 8.0 compatible) |
| Provisioning | One cluster per user; one logical database per page |
| Isolation | Each page has its own logical database and credentials |
| Persistence | Survives cold starts and re-deploys |
| Access | Page runtime only, not from the sandbox |
| Libraries | mysql2, prisma, drizzle, knex, sequelize |
| Schema | Created by the app at startup |
