from timeline.models import TimelineEntry
import reverse_geocode


def add_reverse_geolocation(entry: TimelineEntry):
    if (
        (location := entry.data.get('geolocation', {}))
        and (lat := location.get('latitude'))
        and (lng := location.get('longitude'))
    ):
        reverse_geolocation = reverse_geocode.search(((lat, lng),))[0]
        entry.data['location']['city'] = reverse_geolocation['city']
        entry.data['location']['country'] = reverse_geolocation['country']
    return entry
