import config from './google-map.js';

export default Vue.component('entry-map', {
  props: ['entries',],
  computed: {
    markers: function() {
      return this.entries.filter(e => e.data.location).map(e => {
        return {
          lat: e.data.location.latitude,
          lng: e.data.location.longitude,
        };
      });
    },
  },
  template: `
    <google-map class="entry-map" :markers="markers" v-if="markers.length"></google-map>
  `
});