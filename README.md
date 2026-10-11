# Comments

A Django + Vue discussion app with guest posting, user accounts, nested replies,
quotes, attachments, up/down voting, and sorting by date, author, email, or popularity.
Comments are paginated by 25 root discussions, keeping replies together.

Hosted version: [dzen-code-comments.online](https://dzen-code-comments.online/).

## How it works

- **Vue** renders the interface and sends HTTP requests to **Django**, served by Uvicorn.
- **WebSockets** notify open pages when comments, replies, or votes change. Vue
  refreshes the current page without clearing drafts or changing the selected sort.
  Connections reconnect automatically and fetch any missed updates.
- **PostgreSQL** stores accounts, comments, votes, and a database copy of sessions.
- **Redis** distributes WebSocket notifications between workers, caches sessions,
  and counts failed login attempts. Sessions last seven
  days; five failed login attempts block that username until the five-minute counter expires.
- Login issues a five-minute **JWT**, kept in browser memory and renewed using an
  HttpOnly session cookie. Signed-in comments use the account's saved identity.
  Account emails are unique; guests cannot use registered usernames or emails.
- **Nginx** serves built frontend assets and uploads, forwarding other requests to
  Django. In production, the existing external **Caddy** handles HTTPS.

## Deploy locally

Install Docker with the Compose plugin. Run all commands from the project root.
Create `.env` for first-time setup, preserving an existing file:

```bash
test -f .env || cp .env.example .env
```

Set a long random `SECRET_KEY` and a strong `POSTGRES_PASSWORD` in `.env`.
Keep `.env` private. Database name and user default to `comments` in Compose.

```bash
docker compose -f compose.yaml -f compose.local.yaml up -d --build
```

Docker assigns an available host port automatically. Find it after startup:

```bash
docker compose -f compose.yaml -f compose.local.yaml port nginx 8002
```

For example, if it prints `127.0.0.1:49153`, open **http://localhost:49153**.
Use the port actually printed on your machine. The published port is bound to
loopback; PostgreSQL and Redis stay inside Docker. Nginx and Django use port
`8002` internally, independent of the assigned host port.

Docker builds Vue; the app runs migrations and collects static files on startup.
Local mode enables `DEBUG` and skips CAPTCHA.

To test live updates, open the discussion in two tabs and post a comment or vote
in one: the other updates automatically. `/ws/comments/` shares the normal site
port through Nginx and Caddy; no extra public port or Caddy route is needed.
For development outside Docker, use Uvicorn (plain Django `runserver` does not
serve this WebSocket endpoint), with PostgreSQL and Redis available:

```bash
cd SPA
uv run uvicorn SPA.asgi:application --reload --port 8002
```

Build Vue with `npm run build --prefix frontend` from the project root. Uvicorn
does not serve development static files; use the Docker/Nginx setup above to
test the complete UI, or arrange a separate static-file server.

## Deploy to the server

Prepare `.env` as above and set `RECAPTCHA_SITE_KEY` and `RECAPTCHA_SECRET_KEY`
for reCAPTCHA v3, with `dzen-code-comments.online` allowed in its configuration.
`RECAPTCHA_MIN_SCORE` is optional; it is used in reCAPTCHA v2, and defaults to `0.5`.

Point the domain's DNS to the server and allow incoming HTTP/HTTPS traffic to Caddy.
Start the production configuration, which disables debug mode and requires HTTPS,
then find the assigned port:

```bash
docker compose up -d --build
docker compose port nginx 8002
```

Manually put the printed host port into your existing Caddyfile. For example,
if Docker prints `127.0.0.1:49153`, use:

```caddyfile
dzen-code-comments.online {
    reverse_proxy 127.0.0.1:49153
}
```

Caddy must run on the host or use Docker host networking to reach this address.
After editing the Caddyfile, reload Caddy (for a container named `caddy`):

```bash
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

**The host port can change when the Nginx container is recreated.** After updates
or redeployment, check `docker compose port nginx 8002` again. If it changed, you
must manually update the Caddyfile and reload Caddy; this app does not do it for you.
See [Docker's port command](https://docs.docker.com/reference/cli/docker/compose/port/)
for details on looking up the published port.

## Maintenance

After pulling updated code, repeat the appropriate deployment command above.
Check the assigned port afterward and update Caddy if needed. Back up before
updates; migrations run automatically. Useful commands:

```bash
docker compose ps                                 # Container status
docker compose port nginx 8002                    # Current host address and port
docker compose logs --tail=100 -f app nginx       # Application/proxy logs; Ctrl+C exits
docker compose exec app python manage.py createsuperuser
docker compose exec app python manage.py clearsessions
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

The administrator signs in at `/admin/`. Run `clearsessions` periodically to remove
expired database sessions. In `psql`, use `\dt` to list tables and `\q` to exit.

Back up PostgreSQL and uploaded files to the current directory:

```bash
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup.sql
docker compose exec -T app tar -czf - -C /srv/media . > uploads.tar.gz
```

Store dated copies securely off the server. Database and uploads use persistent
Docker volumes; `docker compose down` keeps them, but `down --volumes` deletes them.
If an upgrade reports duplicate account emails, give those accounts distinct
addresses before retrying the migration.


## Database Schema

MySQL model can be found in `db_models/MySQL_model.mwb`, which can be opened with MySQL Workbench.

If you want to work with PostgreSQL, which is an original version, you can `db_models/schema-postgresql.sql`, which is a plain SQL script,
containing the schema definition.
