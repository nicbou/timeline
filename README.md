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