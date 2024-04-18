"use strict";

import { initGoogleMaps } from './../services/googlemaps.js';
import config from './../config.js';

export default Vue.component('google-map', {
  props: ['markers'],
  data: function() {
    return {
      map: null,
      polyline: null,
      polylineShadow: null,
      endMarker: null,
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
        this.polylineShadow.setMap(null);
      }

      this.polylineShadow = new google.maps.Polyline({
        path: this.markers,
        geodesic: true,
        strokeOpacity: 0.7,
        strokeColor: '#fff',
        strokeWeight: 6,
        map: this.map,
      });
      this.polyline = new google.maps.Polyline({
        path: this.markers,
        geodesic: true,
        strokeOpacity: 1,
        strokeColor: '#64719c',
        strokeWeight: 3,
        map: this.map,
      });

      if (this.endMarker) {
        this.endMarker.setMap(null);
      }
      this.endMarker = new google.maps.Marker({
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          fillColor: '#64719c',
          fillOpacity: 1,
          strokeWeight: 1.5,
          strokeColor: '#fff',
          strokeOpacity: 0.9,
          scale: 5,
        },
        map: this.map,
        position: this.markers[this.markers.length - 1],
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
