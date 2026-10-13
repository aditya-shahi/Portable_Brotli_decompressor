# Brotli S3 Viewer

A small toolkit for opening Brotli-compressed (`.br`) text and JSON files stored on S3. Paste a `decom` URL, and the tool takes the S3 link after `s3link=`, downloads it, decompresses it and shows the result in the browser.

## Contents

| File | Purpose |
|---|---|
| `brotli_viewer.html` | The front end. Works on its own, or served by the local helper. |
| `brotli_local.py` | Local helper server. Fetches the link on your computer (so no CORS limits, and a login can be sent), decompresses it and serves the page. |
| `brotli_s3.py` | Command-line tool. Downloads and decompresses one or more links or local `.br` files. |

## How it works

Given a URL such as:

```
http://forage-internal.datables.ai/forage-fi2depress/decom?s3link=https://forage-caching.s3.amazonaws.com/urlchecker/.../file.json.br
```

1. Everything after the first `s3link=` is extracted. If it is percent-encoded (`https%3A%2F%2F…`), it is decoded.
2. The extracted S3 link is fetched. The `forage-internal` address is **not** contacted, so a broken `decom` service doesn't matter.
3. The data is Brotli-decompressed. If the server already decoded it (`Content-Encoding: br`), the text is used as-is.
4. The text is shown on the page. JSON is pretty-printed (this can be switched off).

## Quick start (recommended): local helper

This works for links that don't allow browser requests (CORS) or that need a login.

```bash
pip install brotli
python brotli_local.py              # default port 8765
python brotli_local.py --port 9000  # optional: another port
```

Keep `brotli_viewer.html` in the same folder as `brotli_local.py`. Then open <http://localhost:8765>, paste the URL and click **Decompress**.

## Standalone page (no install)

Open `brotli_viewer.html` directly in a browser. It loads a Brotli decoder (WebAssembly) from a public CDN, so it needs internet access.

It only works when the S3 bucket allows cross-origin requests (CORS). If it doesn't, the page says so. Use the local helper, or the file fallback below.

## Page features

- **URL box**: paste the full URL (press Enter or click Decompress).
- **Login**: username and password fields for links that require basic auth.
  - After a successful login, the login is saved in this browser's local storage, per host, and filled in next time. Untick **Remember** to prevent that.
  - **Forget login** clears the saved login for the current host.
  - Logins are never sent to `amazonaws.com` hosts when using the local helper (S3 doesn't use basic auth and answers HTTP 400 if it receives one).
- **Pretty-print JSON**: toggle formatting of valid JSON.
- **Copy**: copies the displayed text.
- **Download**: saves the result as a file (the `.br` extension is dropped from the name).
- **Open in new tab**: opens the result in a new tab and displays it in the browser without downloading. Valid JSON opens as a JSON document, anything else as plain text. If the browser blocks the tab, allow pop-ups for the page.
- **Choose or drop a file**: decompresses a `.br` file you downloaded yourself. This runs locally in the browser and works regardless of CORS or login.
- **`?url=` parameter**: opening `brotli_viewer.html?url=<full url>` (or `http://localhost:8765/?url=…`) runs immediately.

## Command-line tool

```bash
pip install brotli                  # optional: pip install boto3 for s3:// links

python brotli_s3.py "https://bucket.s3.amazonaws.com/path/file.json.br"
python brotli_s3.py URL -o out.json          # choose the output file
python brotli_s3.py URL --print              # print to the terminal
python brotli_s3.py URL1 URL2 -d out/        # several files into a folder
python brotli_s3.py s3://bucket/path/file.json.br   # uses your AWS credentials
python brotli_s3.py downloaded.json.br       # a local file
```

- Files are decompressed as a stream, so large files don't need to fit in memory.
- Presigned query strings are kept out of the log lines.
- The tool takes an S3 link directly, not the `decom` URL. Pass the part after `s3link=`.

## Troubleshooting

| Message | Likely cause and fix |
|---|---|
| "No s3link= found in that URL" | The pasted URL doesn't contain `s3link=`. Paste the full URL. |
| "The browser couldn't fetch that link" / "blocked even with a login" | The server doesn't allow requests from a web page (CORS). Use the local helper, or download the file and drop it on the page. |
| "This link needs a login (HTTP 401)" | Enter the username and password in the Login box and click Decompress. |
| "That username or password was rejected" | Check the login. Use **Forget login** and enter it again. |
| HTTP 400 from an S3 link | Usually a login was sent to S3, which refuses it. Click **Forget login**, clear the fields, and use the latest `brotli_local.py`. |
| HTTP 403 | Access denied, or the presigned link expired. A plain S3 address with no signing parameters only works if the object is public. Get a fresh presigned link. |
| HTTP 404 | The file doesn't exist at that path. Check the link. |
| "The data is not valid Brotli" | The file isn't actually Brotli-compressed, or the download was cut short. |
| "Missing dependency" when starting a Python script | Run `pip install brotli`. |

## Security notes

- The local helper listens only on `127.0.0.1` and rejects requests from other websites and hosts.
- Saved logins are stored **in plain text** in your browser's local storage. Use the remember option only on a computer you trust, and use **Forget login** when you're done.
- A login is sent only to the host of the link you paste, and never to `amazonaws.com`.
- Files are limited to 512 MB in the local helper.

## Requirements

- Python 3.8 or newer with the `brotli` package (local helper and command-line tool).
- A modern browser (Chrome, Edge, Firefox or Safari).
- Internet access for the standalone page, which loads its decoder from `cdn.jsdelivr.net`.
