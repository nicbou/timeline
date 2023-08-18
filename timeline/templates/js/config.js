// The variables in this file are replaced by environment variables at build time.
// The new file is saved in a different place, but nginx serves it at the same address.
// If you change this file, you must rebuild the docker image for the changes to apply.
export default {
  googleMapsApiKey: "${GOOGLE_MAPS_API_KEY}",
  domain: "http://localhost:9000",
};
