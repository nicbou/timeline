export default Vue.component('timeline-nav', {
  data() {
    return {
      keypressListener: null,
    };
  },
  mounted() {
    this.keypressListener = window.addEventListener('keydown', this.onKeydown);
  },
  destroyed(){
    window.removeEventListener(this.keypressListener);
  },
  computed: {
    timelineDate: {
      get() {
        return moment(this.$route.query.date, 'YYYY-MM-DD', true);
      },
      set(newDate) {
        const queryParams = { ...this.$route.query };
        queryParams.date = moment.min(newDate, this.today).format('YYYY-MM-DD');
        return this.$router.push({ name: 'timeline', query: queryParams });
      }
    },
    timelineDateIso: {
      get() {
        return this.$route.query.date;
      },
      set(newDate) {
        return this.timelineDate = moment(newDate, 'YYYY-MM-DD', true);
      }
    },
    today(){
      return moment().startOf('day');
    },
    showTomorrow() {
      return moment(this.timelineDate).add('days', 1).diff(this.today) <= 0
    },
    showNextWeek() {
      return moment(this.timelineDate).add('weeks', 1).diff(this.today) <= 0
    },
    showNextMonth() {
      return moment(this.timelineDate).add('months', 1).diff(this.today) <= 0
    },
    showNextYear() {
      return moment(this.timelineDate).add('years', 1).diff(this.today) <= 0
    },
  },
  methods: {
    pickTimelineDate(date) {
      this.timelineDate = moment(date);
    },
    moveTimelineDate(quantity, unit) {
      this.timelineDate = moment(this.timelineDate).add(quantity, unit);
    },
    onKeydown(event) {
      let timeUnit = 'days';
      if(event.altKey && event.shiftKey){
        timeUnit = 'years';
      }
      else if(event.altKey){
        timeUnit = 'months';
      }
      else if(event.shiftKey) {
        timeUnit = 'weeks';
      }

      if(event.key === "ArrowLeft"){
        this.moveTimelineDate(timeUnit, -1)
      }
      else if(event.key === "ArrowRight"){
        this.moveTimelineDate(timeUnit, +1)
      }
    },
  },
  template: `
    <nav class="input-group timeline-nav">
      <button class="minus-1-year year button" @click="moveTimelineDate('years', -1)">-1Y</button>
      <button class="minus-1-month month button" @click="moveTimelineDate('months', -1)">-1M</button>
      <button class="minus-1-week week button" @click="moveTimelineDate('weeks', -1)">-1W</button>
      <button class="minus-1-day day button" @click="moveTimelineDate('days', -1)">-1D</button>
      <input class="input" type="date" v-model="timelineDateIso" :max="today.format('YYYY-MM-DD')">
      <button class="plus-1-day day button" :disabled="!showTomorrow" @click="moveTimelineDate('days', 1)">+1D</button>
      <button class="plus-1-week week button" :disabled="!showNextWeek" @click="moveTimelineDate('weeks', 1)">+1W</button>
      <button class="plus-1-month month button" :disabled="!showNextMonth" @click="moveTimelineDate('months', 1)">+1M</button>
      <button class="plus-1-year year button" :disabled="!showNextYear" @click="moveTimelineDate('years', 1)">+1Y</button>
      <button class="today button" :disabled="!showTomorrow" @click="pickTimelineDate(today)">Today</button>
    </nav>
  `
});