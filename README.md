# Timeline

Point it at your files, and it generates a timeline of your life. The timeline is a simple static website. See your photos, videos, calendar events, diary entries, geolocation history and bank transactions day by day. Scroll through your data the same way you scroll through your photos.

![Screenshot of the timeline](https://nicolasbouliane.com/images/timeline-1.png)

This project does the same thing as the [old timeline](https://github.com/nicbou/timeline-old), but it's simpler, lighter and easier to run. It's meant to be used by other humans.

**[Introduction to this project](https://nicolasbouliane.com/projects/new-timeline)**

## Installation

### 1. Install the timeline

To install the latest released version, run `pip install timeline-ssg`.

To install the latest development build, run `pip install -e /path/to/this/repository`.

Once it's installed, run `timeline --help` to see how to generate a timeline.

### 2. Install ffmpeg (optional)

Timeline uses ffmpeg to generate thumbnails and previews for videos. You must install it separately. If you don't install it, video files will not appear on the timeline.

For example, you can run `apt install ffmpeg` or `brew install ffmpeg`.

### 3. Build your timeline

Call `timeline /path/to/your/files -o /path/to/generated/timeline` to build a timeline. See [usage instructions](#usage) for more details.

The `timeline` command generates a static website. Use the `-o /timeline/output/path` argument to choose where to put the files. Look at the logs to see where the files go.

### 4. Serve your timeline

The `timeline` generates a website. You must serve that website somehow.

There are 3 ways to do this:

- **Use the test server** (run `timeline -s` or `timeline -s 8080`) to preview the timeline website. This server is not secure, and it's not meant for production.
- **Use Caddy or nginx** to serve your timeline files. You can find an example Caddy config in this repository (`server/server/Caddyfile`).
- **Use Docker**. Find a `docker-compose.yml` and `Dockerfile` in this repository (in the `server` directory).

The docker image needs these environment variables:
```
SSL_DOMAIN=timeline.johndoe.com
SSL_EMAIL=contact@johndoe.com
WEB_USERNAME=jdoe
WEB_PASSWORD=hunter2
STATIC_SITE_PATH=/timeline/output/path
```

## Usage

To generate a timeline from a list of files, call `timeline /path/to/your/files`. It will be slow the first time, then much faster. Only new or modified files are processed.

Timeline will generate a static website. You can choose the destination with the `-o` argument. The log show where the generated website is saved.

To serve the website, you should use a static file server like Caddy or Nginx. Timeline can serve the website it generates (by calling `timeline -s`), but this is a test server. It's neither fast nor secure.

Call `timeline --help` for full usage instructions.

### Showing maps

To display a map of your photos, videos and other entries with geolocation on the timeline, you need a [Google Maps API key](https://developers.google.com/maps/documentation/javascript/get-api-key). If you don't supply an API key, the map will not be displayed.

Use the `--maps-key` command line argument to supply an API key.

### Dating and locating files

The tool tries to guess the dates and location of files. It uses metadata (like EXIF data on photos), file modification dates, and file names.

If a file name ends with a date, that date will be used:

```
# Simple dates are supported
/journal-2023-09-10.md
/2023-09-10.md
/test-2023-09-10.journal.md
/2023-09-10.journal.md

# Dates with times are supported
/files/test-2023-09-10T2330.md
/files/2023-09-10T2330.md
/files/test-2023-09-10T2330.journal.md
/files/2023-09-10T2330.journal.md

# Date ranges are supported
/files/test 2023-09-10 to 2023-10-12.md
/files/2023-09-10 to 2023-10-12.md
/files/test 2023-09-10T2330 to 2023-10-12T0504.md
/files/2023-09-10T2330 to 2023-10-12.md

# Date that are not at the end of the name are ignored
/files/2023-09-10T2330 to 2023-09-11T2330 test.md
/files/2023-09-10 to 2023-09-11 test.md
/files/2023-09-10T2330 test.md
/files/2023-09-10 test.md
/files/2023-09 test.md
/files/2023 test.md

# Simple years are ignored
/files/summary 2023.md
/files/2023.md

# Invalid dates are ignored
/files/test-1800-10-01.md
/files/test-9999-10-01.md
/files/test-2023-13-01.md
/files/test-2023-09-1.md
/files/test-2023-9-10.md
/files/test-2023-9.md
/files/2023-09-10T2430.md
```

### Special file extensions

Some file extensions hint at files that have a special purpose on the timeline.

- `.journal.md` marks a Markdown file as a journal entry. Those are displayed more prominently on the timeline.
- `.n26.csv` marks a CSV file as an N26 bank transaction export. Each line will be added to the timeline as a bank transaction.
- `.searches.csv` marks a CSV file as a log of internet searches. It has 3 columns: `date` (an ISO-8601 date), `query` (the search query) and `url` (the optional URL of the search results)