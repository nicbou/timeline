# Timeline

Point it at your files, and it generates a timeline of your life as a static website. See your photos, videos, calendar events, diary entries, geolocation history and bank transactions day by day. Scroll through your data the same way you scroll through your photos.

This project does the same thing as the [old timeline](https://github.com/nicbou/timeline-old), but it's much simpler and lighter.

## Installation

To install the latest released version, run `pip install timeline-ssg`.

To install the latest development build, run `pip install -e /path/to/this/repository`.

### Docker

A `docker-compose.yml` file is supplied in the `/server` directory. You can use it to serve a fully functional, password-protected timeline.

It requires the following environment variables:
```
WEB_USERNAME=alice
WEB_PASSWORD=supersecret
STATIC_SITE_PATH=/path/to/your/generated/timeline
```

### Processing videos

Timeline relies on ffmpeg to generate video previews. If ffmpeg is not installed, the timeline will work, but videos will not be included.

To process videos, install `ffmpeg`. For example, you can run `apt install ffmpeg` or `brew install ffmpeg`.

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