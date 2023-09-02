"use strict";

import { initGoogleMaps } from './../services/googlemaps.js';
import config from './../config.js';

export default Vue.component('google-map', {
  props: ['markers'],
  data: function() {
    return {
      map: null,
      polyline: null,
      currentMapFeatures: [],
    };
  },
  watch: {
    markers: function() { this.updateFeaturesOnMap() },
    map: function() { this.updateFeaturesOnMap() },
  },
  methods: {
    updateFeaturesOnMap: function() {
      if (!this.map) { return }
      if (this.polyline) {
        this.polyline.setMap(null);
      }
      this.polyline = new google.maps.Polyline({
        path: this.markers,
        geodesic: true,
        strokeOpacity: 1.0,
        strokeWeight: 2,
        map: this.map,
      });

      const mapBounds = new google.maps.LatLngBounds();
      this.markers.forEach(marker => {
        mapBounds.extend(new google.maps.LatLng(marker.lat, marker.lng));
      });

      // Prevent excessive zoom when all the markers are really close
      google.maps.event.addListenerOnce(
        this.map, 'bounds_changed', () => this.map.setZoom(Math.min(15, this.map.getZoom()))
      );
      this.map.fitBounds(mapBounds);
    },
  },
  async mounted() {
    try {
      const google = await initGoogleMaps();
      this.map = new google.maps.Map(this.$el, {
        disableDefaultUI: true,
        mapTypeId: 'terrain',
      });
      this.updateFeaturesOnMap();
    } catch (error) {
      console.error(error);
    }
  },
  template: `<div class="google-map"></div>`,
})
