import config from './../config.js';

const GMAPS_CALLBACK_NAME = 'gmapsCallback';

let googleMapsIsInitialised = !!window.google;
let resolveGMapsInitPromise;
let rejectGMapsInitPromise;

const initGMapsPromise = new Promise((resolve, reject) => {
  resolveGMapsInitPromise = resolve;
  rejectGMapsInitPromise = reject;
});

export function initGoogleMaps() {
  if (googleMapsIsInitialised) return initGMapsPromise;

  googleMapsIsInitialised = true;
  // The callback function is called by
  // the Google Maps script if it is
  // successfully loaded.
  window[GMAPS_CALLBACK_NAME] = () => resolveGMapsInitPromise(window.google);

  // We inject a new script tag into
  // the `<head>` of our HTML to load
  // the Google Maps script.
  const script = document.createElement('script');
  script.async = true;
  script.defer = true;
  script.src = `https://maps.googleapis.com/maps/api/js?key=${config.googleMapsApiKey}&libraries=places&callback=${GMAPS_CALLBACK_NAME}`;
  script.onerror = rejectGMapsInitPromise;
  document.querySelector('head').appendChild(script);

  return initGMapsPromise;
}
