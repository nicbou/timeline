import config from './../config.js';
import GoogleMapComponent from './google-map.js';

export default Vue.component('entry-map', {
  props: ['entries',],
  data() {
    return { config: config };
  },
  computed: {
    markers() {
      return this.entries.filter(e => e.data.location && e.data.location.latitude && e.data.location.longitude).map(e => {
        return {
          lat: e.data.location.latitude,
          lng: e.data.location.longitude,
        };
      });
    },
  },
  template: `
    <google-map v-if="config.googleMapsApiKey && markers.length" class="entry-map" :markers="markers" v-show="markers.length"></google-map>
  `
});