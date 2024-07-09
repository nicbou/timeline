export default Vue.component('weather', {
  props: ['date', 'latitude', 'longitude'],
  data() {
    return {
      temperature: null,
      weatherCode: null,
    };
  },
  computed: {
    apiUrl() {
      if(!this.latitude || !this.longitude){
        return null;
      }

      return "https://archive-api.open-meteo.com/v1/archive?"
        + `latitude=${this.latitude}`
        + `&longitude=${this.longitude}`
        + `&start_date=${this.date.format('YYYY-MM-DD')}`
        + `&end_date=${this.date.format('YYYY-MM-DD')}`
        + "&daily=weather_code,temperature_2m_mean&timezone=auto"
    },
    weatherType(){
      return {
        "0": {
          description: "Sunny",
          image: "fas fa-sun"
        },
        "1": {
          description: "Mainly Sunny",
          image: "fas fa-sun"
        },
        "2": {
          description: "Partly Cloudy",
          image: "fas fa-cloud-sun"
        },
        "3": {
          description: "Cloudy",
          image: "fas fa-cloud"
        },
        "45": {
          description: "Foggy",
          image: "fas fa-water"
        },
        "48": {
          description: "Rime Fog",
          image: "fas fa-water"
        },
        "51": {
          description: "Light Drizzle",
          image: "fas fa-cloud-rain"
        },
        "53": {
          description: "Drizzle",
          image: "fas fa-cloud-rain"
        },
        "55": {
          description: "Heavy Drizzle",
          image: "fas fa-cloud-showers-heavy"
        },
        "56": {
          description: "Light Freezing Drizzle",
          image: "fas fa-cloud-showers-heavy"
        },
        "57": {
          description: "Freezing Drizzle",
          image: "fas fa-cloud-rain"
        },
        "61": {
          description: "Light Rain",
          image: "fas fa-cloud-showers-heavy"
        },
        "63": {
          description: "Rain",
          image: "fas fa-cloud-showers-heavy"
        },
        "65": {
          description: "Heavy Rain",
          image: "fas fa-cloud-showers-heavy"
        },
        "66": {
          description: "Light Freezing Rain",
          image: "fas fa-cloud-rain"
        },
        "67": {
          description: "Freezing Rain",
          image: "fas fa-cloud-showers-heavy"
        },
        "71": {
          description: "Light Snow",
          image: "far fa-snowflake"
        },
        "73": {
          description: "Snow",
          image: "far fa-snowflake"
        },
        "75": {
          description: "Heavy Snow",
          image: "far fa-snowflake"
        },
        "77": {
          description: "Snow Grains",
          image: "far fa-snowflake"
        },
        "80": {
          description: "Light Showers",
          image: "fas fa-cloud-showers-heavy"
        },
        "81": {
          description: "Showers",
          image: "fas fa-cloud-showers-heavy"
        },
        "82": {
          description: "Heavy Showers",
          image: "fas fa-cloud-showers-heavy"
        },
        "85": {
          description: "Light Snow Showers",
          image: "far fa-snowflake"
        },
        "86": {
          description: "Snow Showers",
          image: "far fa-snowflake"
        },
        "95": {
          description: "Thunderstorm",
          image: "fas fa-bolt"
        },
        "96": {
          description: "Light Thunderstorms With Hail",
          image: "fas fa-bolt"
        },
        "99": {
          description: "Thunderstorm With Hail",
          image: "fas fa-bolt"
        }
      }[this.weatherCode];
    },
  },
  watch: {
    apiUrl: {
      immediate: true,
      handler(newApiUrl){
        this.isLoading = true;
        if(newApiUrl){
          fetch(newApiUrl)
            .then(response => response.json())
            .then(json => {
              this.temperature = Math.round(json.daily.temperature_2m_mean[0]);
              this.weatherCode = json.daily.weather_code[0];
            });
        }
      }
    }
  },
  template: `
    <div class="weather" :title="weatherType?.description" v-if="weatherType && temperature">
      <i :class="weatherType?.image" :alt="weatherType?.description"></i> {{ temperature }}ºC
    </div>
  `
});