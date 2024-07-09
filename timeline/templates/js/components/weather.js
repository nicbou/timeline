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
          image: "http://openweathermap.org/img/wn/01d@2x.png"
        },
        "1": {
          description: "Mainly Sunny",
          image: "http://openweathermap.org/img/wn/01d@2x.png"
        },
        "2": {
          description: "Partly Cloudy",
          image: "http://openweathermap.org/img/wn/02d@2x.png"
        },
        "3": {
          description: "Cloudy",
          image: "http://openweathermap.org/img/wn/03d@2x.png"
        },
        "45": {
          description: "Foggy",
          image: "http://openweathermap.org/img/wn/50d@2x.png"
        },
        "48": {
          description: "Rime Fog",
          image: "http://openweathermap.org/img/wn/50d@2x.png"
        },
        "51": {
          description: "Light Drizzle",
          image: "http://openweathermap.org/img/wn/09d@2x.png"
        },
        "53": {
          description: "Drizzle",
          image: "http://openweathermap.org/img/wn/09d@2x.png"
        },
        "55": {
          description: "Heavy Drizzle",
          image: "http://openweathermap.org/img/wn/09d@2x.png"
        },
        "56": {
          description: "Light Freezing Drizzle",
          image: "http://openweathermap.org/img/wn/09d@2x.png"
        },
        "57": {
          description: "Freezing Drizzle",
          image: "http://openweathermap.org/img/wn/09d@2x.png"
        },
        "61": {
          description: "Light Rain",
          image: "http://openweathermap.org/img/wn/10d@2x.png"
        },
        "63": {
          description: "Rain",
          image: "http://openweathermap.org/img/wn/10d@2x.png"
        },
        "65": {
          description: "Heavy Rain",
          image: "http://openweathermap.org/img/wn/10d@2x.png"
        },
        "66": {
          description: "Light Freezing Rain",
          image: "http://openweathermap.org/img/wn/10d@2x.png"
        },
        "67": {
          description: "Freezing Rain",
          image: "http://openweathermap.org/img/wn/10d@2x.png"
        },
        "71": {
          description: "Light Snow",
          image: "http://openweathermap.org/img/wn/13d@2x.png"
        },
        "73": {
          description: "Snow",
          image: "http://openweathermap.org/img/wn/13d@2x.png"
        },
        "75": {
          description: "Heavy Snow",
          image: "http://openweathermap.org/img/wn/13d@2x.png"
        },
        "77": {
          description: "Snow Grains",
          image: "http://openweathermap.org/img/wn/13d@2x.png"
        },
        "80": {
          description: "Light Showers",
          image: "http://openweathermap.org/img/wn/09d@2x.png"
        },
        "81": {
          description: "Showers",
          image: "http://openweathermap.org/img/wn/09d@2x.png"
        },
        "82": {
          description: "Heavy Showers",
          image: "http://openweathermap.org/img/wn/09d@2x.png"
        },
        "85": {
          description: "Light Snow Showers",
          image: "http://openweathermap.org/img/wn/13d@2x.png"
        },
        "86": {
          description: "Snow Showers",
          image: "http://openweathermap.org/img/wn/13d@2x.png"
        },
        "95": {
          description: "Thunderstorm",
          image: "http://openweathermap.org/img/wn/11d@2x.png"
        },
        "96": {
          description: "Light Thunderstorms With Hail",
          image: "http://openweathermap.org/img/wn/11d@2x.png"
        },
        "99": {
          description: "Thunderstorm With Hail",
          image: "http://openweathermap.org/img/wn/11d@2x.png"
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
    <div class="weather" v-if="weatherType && temperature">
      <img :src="weatherType?.image" :alt="weatherType?.description"> {{ temperature }}ºC
    </div>
  `
});