export function hasGeolocation(entry) {
  return (
    entry.data.location
    && entry.data.location.latitude
    && entry.data.location.longitude
  );
}