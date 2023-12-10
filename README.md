# Timeline

Point it at your files, and it generates a timeline of your life as a static website. See your photos, videos, calendar events, diary entries, geolocation history and bank transactions day by day. Scroll through your data the same way you scroll through your photos.

This project does the same thing as the [old timeline](https://github.com/nicbou/timeline-old), but it's much simpler and lighter.

## Installation

To install the latest released version, run `pip install timeline-ssg`.

To install the latest development build, run `pip install -e /path/to/this/repository`.

### Processing videos

Timeline relies on ffmpeg to generate video previews. If ffmpeg is not installed, the timeline will work, but videos will not be included.

To process videos, install `ffmpeg`. For example, you can run `apt install ffmpeg` or `brew install ffmpeg`.

### Showing maps

To show a map of your photos, videos and other entries with geolocation, you need a [Google Maps API key](https://developers.google.com/maps/documentation/javascript/get-api-key). If you don't supply an API key, the map will not be displayed.

You can supply the Google Maps API key with the `--maps-key` command line argument.

## Usage

Call `timeline --help` for usage instructions. The simplest command is `timeline /path/to/your/files /path/to/more/files`.

Timeline will generate a static website. You can choose the destination with the `-o` argument. The log will show where the website is saved.

It will be slow the first time, then much faster. Files are only processed once unless they change.

To serve the website, you should use a static file server like Caddy or Nginx. Timeline comes with a web server (`timeline -s`), but it's neither fast nor secure.

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