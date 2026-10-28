"use strict";

import { initGoogleMaps } from './../services/googlemaps.js';
import config from './../config.js';

export default Vue.component('country-map', {
  data() {
    return {
      visitedCountries: {},
      countryShapes: {},
      selectedCountry: null,
    };
  },
  async mounted() {
    const [google] = await Promise.all([
      initGoogleMaps(),
      this.loadVisitedCountries(),
      this.loadCountryShapes(),
    ]);

    const map = new google.maps.Map(this.$refs.mapEl, {
      zoom: 2,
      center: { lat: 25, lng: 10 },
      mapTypeId: 'roadmap',
      disableDefaultUI: true,
      zoomControl: true,
      gestureHandling: 'greedy',
    });

    for (const [countryCode, { countryName, ranges }] of Object.entries(this.visitedCountries)) {
      const paths = this.countryShapes[countryCode];
      if (!paths) continue;

      const polygon = new google.maps.Polygon({
        paths,
        strokeColor: '#ffffff',
        strokeWeight: 1,
        fillColor: '#64719c',
        fillOpacity: 0.6,
      });
      polygon.addListener('click', () => {
        this.selectedCountry = { countryCode, countryName, ranges };
      });
      polygon.setMap(map);
    }
  },
  computed: {
    sortedCountries() {
      return Object.entries(this.visitedCountries)
        .map(([countryCode, { countryName, ranges }]) => ({ countryCode, countryName, ranges }))
        .sort((a, b) => a.countryName.localeCompare(b.countryName));
    },
    rangesByYear() {
      if (!this.selectedCountry) return [];
      const groups = new Map();
      for (const [start, end] of this.selectedCountry.ranges) {
        const year = start.slice(0, 4);
        if (!groups.has(year)) groups.set(year, []);
        groups.get(year).push([start, end]);
      }
      return [...groups.entries()].map(([year, ranges]) => ({ year, ranges }));
    },
  },
  methods: {
    formatShortDate(isoDate) {
      const [y, m, d] = isoDate.split('-').map(Number);
      return new Date(y, m - 1, d).toLocaleDateString('en-US', { month: 'long', day: 'numeric' });
    },
    formatRange(start, end) {
      if (start === end) return this.formatShortDate(start);
      if (start.slice(0, 7) === end.slice(0, 7)) {
        return `${this.formatShortDate(start)}-${Number(end.slice(8, 10))}`;
      }
      return `${this.formatShortDate(start)} — ${this.formatShortDate(end)}`;
    },
    async loadVisitedCountries() {
      const response = await fetch(`${config.siteUrl}/entries/visited-countries.json`);
      this.visitedCountries = await response.json();
    },
    async loadCountryShapes() {
      const response = await fetch(`${config.siteUrl}/country-shapes.json`);
      const geojson = await response.json();
      const toLatLng = ([lng, lat]) => ({ lat, lng });
      const shapes = {};
      for (const feature of geojson.features) {
        const code = feature.properties.ISO_A2;
        const { type, coordinates } = feature.geometry;
        shapes[code] = type === 'Polygon'
          ? coordinates.map(ring => ring.map(toLatLng))
          : coordinates.flatMap(polygon => polygon.map(ring => ring.map(toLatLng)));
      }
      this.countryShapes = shapes;
    },
  },
  template: `
    <main class="country-map-page">
      <router-link class="country-map-back" :to="{ name: 'timeline' }">« Back to timeline</router-link>
      <div ref="mapEl" class="country-map"></div>
      <aside class="country-sidebar">
        <template v-if="selectedCountry">
          <a href="#" class="country-sidebar-back" @click.prevent="selectedCountry = null">« All countries</a>
          <h2>{{ selectedCountry.countryName }}</h2>
          <template v-for="group in rangesByYear">
            <h3 :key="group.year">{{ group.year }}</h3>
            <ul :key="group.year + '-list'">
              <li v-for="[start, end] in group.ranges" :key="start + end">
                <router-link :to="{ name: 'timeline', query: { date: start } }">
                  {{ formatRange(start, end) }}
                </router-link>
              </li>
            </ul>
          </template>
        </template>
        <template v-else>
          <h2>Visited countries</h2>
          <ul class="country-list">
            <li v-for="country in sortedCountries" :key="country.countryCode">
              <a href="#" @click.prevent="selectedCountry = country">{{ country.countryName }}</a>
            </li>
          </ul>
        </template>
      </aside>
    </main>
  `,
});
