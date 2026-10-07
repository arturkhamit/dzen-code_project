# Vue frontend

`src/App.vue` handles the discussion table, sorting, and pagination.
`CommentCard.vue` is reused for saved comments, replies, and preview.
`CommentForm.vue` owns the draft and submission. `FileViewer.vue` opens image
and TXT attachments in a native dialog. `lib/` contains the shared markup,
URL, and upload checks. State lives in the components that use it.

From the repository root, with Node.js 22.12+:

```bash
npm ci --prefix frontend
npm run build --prefix frontend
```

Vite writes `comments.js` and `comments.css` to
`SPA/comments/static/comments/dist/`. Django's staticfiles app serves them.
Run the build before `collectstatic` when deploying. Generated assets and
`node_modules` are ignored; `package-lock.json` pins the dependencies.
`npm run dev --prefix frontend` watches and rebuilds; refresh the Django page
after changes.

The Django view renders the page shell at `/` with these context values:

```python
{
    "page_data": serialize_comment_page(get_comment_page(page_number, sort)),
    "sort": sort,
    "list_url": "/",
    "form_action": "/comments/create/",
    "recaptcha_site_key": "your-public-site-key",
}
```

The view uses `render(request, ...)` so Django supplies the CSRF token. The shell embeds
data through `json_script`; Vue never compiles comments as template source.
`rendered_text` must come from the server markup serializer or the client's
XHTML validator before `CommentCard` displays it with `v-html`.

`GET /` returns HTML for navigation and JSON for
`Accept: application/json`. `serialize_comment_page()` now returns this shape:

```json
{"comments": [], "page": 1, "pages": 1, "count": 0}
```

Each root in `comments` includes a flat `thread` array with depth, username,
timestamp, avatar, quote, attachment, and vote data. The service paginates 25
roots and includes their complete reply threads. Sorting accepts `newest`
(default), `oldest`, `username_asc`, `username_desc`, `email_asc`, `email_desc`.

`POST /comments/create/` receives multipart form data and an `X-CSRFToken` header:
`username`, `email`, optional `homepage`, `text`, optional `attachment`,
`parent_id`, `quoted_comment_id`, `sort`, and `g-recaptcha-response`.
It returns status 201 with `{"list_url": "/?page=1&sort=newest", "comment_id": 123}`,
or status 400 with `{"errors": {"text": ["Explain the validation failure."]}}`.
For replies, the URL locates the page containing their root. `?comment=<id>`
also locates that thread in the requested sort, returning 404 if absent. These JSON
responses replace the old HTML-fragment updates.

The views enforce CSRF and verify CAPTCHA through the CAPTCHA service. A request
serializer reads only public input fields; `save_comment()` validates and stores
the comment and upload together. That service owns its transaction; do not wrap
it in another `atomic()` block. Author IDs, votes, and timestamps from submitted
data are ignored. Reference errors appear in the form's general error area.

Runserver serves stored attachments at `/media/` when `DEBUG=True`. Set
`RECAPTCHA_TEST_MODE=1` for local Google test keys, or configure real keys as
described in the root README. Google test keys are never enabled with
`DEBUG=False`. Browser tests exercise the real views and mock Google's external
widget and verification HTTP response. WebSocket live updates remain future work.
