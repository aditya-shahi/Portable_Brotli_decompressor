# Brotli S3 Viewer

A small tool for opening Brotli-compressed (`.br`) text and JSON files stored on S3. Paste a `decom` URL, and the tool takes the S3 link after `s3link=`, downloads it, decompresses it and shows the result in the browser.

## Contents

| File | Purpose |
|---|---|
| `brotli_viewer.html` | The front end (the page you use in the browser). |
| `brotli_local.py` | Local helper server. Fetches the link on your computer (so no CORS limits, and a login can be sent), decompresses it and serves the page. |

## How it works

Given a URL such as:

```
http://forage-internal.datables.ai/forage-fi2depress/decom?s3link=https://forage-caching.s3.amazonaws.com/urlchecker/.../file.json.br
```

1. Everything after the first `s3link=` is extracted. If it is percent-encoded (`https%3A%2F%2F…`), it is decoded.
2. The extracted S3 link is fetched. The `forage-internal` address is **not** contacted, so a broken `decom` service doesn't matter.
3. The data is Brotli-decompressed. If the server already decoded it (`Content-Encoding: br`), the text is used as-is.
4. The text is shown on the page. JSON is pretty-printed (this can be switched off).

## Run it on your local system

### What you need

- **Python 3.8 or newer.** Check with `python --version` (Windows) or `python3 --version` (macOS/Linux). If it isn't installed, get it from <https://www.python.org/downloads/>. On Windows, tick **Add Python to PATH** in the installer.
- A modern browser (Chrome, Edge, Firefox or Safari).
- Network access from your computer to the S3 link (the same access you have when you open it in your browser).

### Steps

1. **Create a folder** for the tool, for example `brotli-viewer`, and put both files in it:
   - `brotli_local.py`
   - `brotli_viewer.html`

   Both files must be in the same folder.

2. **Open a terminal in that folder.**
   - Windows: open the folder in File Explorer, click the address bar, type `cmd` and press Enter. (Or use PowerShell.)
   - macOS: right-click the folder and choose *New Terminal at Folder*, or open Terminal and run `cd path/to/brotli-viewer`.
   - Linux: open a terminal and run `cd path/to/brotli-viewer`.

3. **(Optional, recommended) Create a virtual environment**, so the install stays inside this folder.

   Windows:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
   macOS / Linux:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Install the one dependency:**
   ```
   pip install brotli
   ```
   (Use `pip3` if `pip` isn't found. You only do this once.)

5. **Start the helper:**
   ```
   python brotli_local.py
   ```
   (Use `python3` on macOS/Linux outside a virtual environment.) You should see:
   ```
   Open http://localhost:8765  (Ctrl+C to stop)
   ```
   Leave this terminal window open while you use the tool.

6. **Open the page.** Go to <http://localhost:8765> in your browser.

7. **Use it.** Paste the full URL into the box and click **Decompress** (or press Enter). If the link asks for a username and password, enter them in the Login box and click Decompress again. The result appears below.

8. **Stop it** when you're finished: go back to the terminal and press `Ctrl+C`.

### Starting it again later

Open a terminal in the same folder, activate the virtual environment if you made one (step 3, second command only), then run `python brotli_local.py` and open <http://localhost:8765>. You don't need to install anything again.

### Using a different port

If port 8765 is taken, choose another:
```
python brotli_local.py --port 9000
```
then open <http://localhost:9000>.

### Optional: standalone page (no helper)

You can also double-click `brotli_viewer.html` to open it directly. It loads a Brotli decoder (WebAssembly) from a public CDN, so it needs internet access, and it only works when the S3 bucket allows cross-origin requests (CORS). If it doesn't, the page says so; use the helper instead.

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
- **`?url=` parameter**: opening `http://localhost:8765/?url=<full url>` runs immediately.

## Troubleshooting

### Running the helper

| Problem | Fix |
|---|---|
| `python` is not recognized / command not found | Install Python and reopen the terminal. On Windows, tick *Add Python to PATH*. On macOS/Linux, use `python3`. |
| `Missing dependency. Install it with: pip install brotli` | Run `pip install brotli` in the same terminal (and the same virtual environment) you use to start the helper. |
| `pip` is not found | Use `python -m pip install brotli` (or `python3 -m pip install brotli`). |
| `externally-managed-environment` error on pip | Use a virtual environment (step 3), or add `--break-system-packages` to the pip command. |
| `Address already in use` | Another program is using the port. Start with `--port 9000` (or any free port). |
| The page shows "brotli_viewer.html must be in the same folder" | Move both files into the same folder and restart the helper from there. |
| `localhost` page doesn't load | Check the terminal still shows the helper running and that you used the same port. |

### Using the page

| Message | Likely cause and fix |
|---|---|
| "No s3link= found in that URL" | The pasted URL doesn't contain `s3link=`. Paste the full URL. |
| "The browser couldn't fetch that link" / "blocked even with a login" | You are using the standalone page and the server doesn't allow requests from a web page (CORS). Use the local helper, or download the file and drop it on the page. |
| "This link needs a login (HTTP 401)" | Enter the username and password in the Login box and click Decompress. |
| "That username or password was rejected" | Check the login. Use **Forget login** and enter it again. |
| HTTP 400 from an S3 link | Usually a login was sent to S3, which refuses it. Click **Forget login**, clear the fields, and use the latest `brotli_local.py`. |
| HTTP 403 | Access denied, or the presigned link expired. A plain S3 address with no signing parameters only works if the object is public. Get a fresh presigned link. |
| HTTP 404 | The file doesn't exist at that path. Check the link. |
| "The data is not valid Brotli" | The file isn't actually Brotli-compressed, or the download was cut short. |

## Security notes

- The local helper listens only on `127.0.0.1` and rejects requests from other websites and hosts.
- Saved logins are stored **in plain text** in your browser's local storage. Use the remember option only on a computer you trust, and use **Forget login** when you're done.
- A login is sent only to the host of the link you paste, and never to `amazonaws.com`.
- Files are limited to 512 MB in the local helper.
