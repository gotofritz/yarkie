# yarkie

Tool to manage YT videos locally. Inspired by yark

<!-- trivial to force a push -->

## Code organisation

The top level structure is

```bash
├── data    # db, videos, thumbnails
├── dist    # generated ui, html + js
├── scripts # scripts to manage data, python
└── ui      # src for the ui, react + ts
```

## Working with data

### Accessing the DB from a web interface

The source data can be found in a db, `data/yarkie.db`. The recommended way to browse it is with [datasette](https://docs.datasette.io/en/stable/index.html). You can load up a web interface with

```bash
❯ datasette serve data/yarkie.db --cors
INFO:     Started server process [31054]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
```

(note the `--cors` option, which allow you to fetch it from the UI web server)

### JSON rest endpoint

Datasette will also offer a REST endpoint, accessible as <http://localhost:8001/yarkie/videos.json?_shape=objects&_sort_desc=view_count>. The returned rows are paginated; the 'next_url' property contains the link to the next page
