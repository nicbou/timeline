export default Vue.component('timeline-nav', {
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
    today: function(){
      return moment().startOf('day');
    },
    showTomorrow: function() {
      return moment(this.timelineDate).add('days', 1).diff(this.today) <= 0
    },
    showNextWeek: function() {
      return moment(this.timelineDate).add('weeks', 1).diff(this.today) <= 0
    },
    showNextMonth: function() {
      return moment(this.timelineDate).add('months', 1).diff(this.today) <= 0
    },
    showNextYear: function() {
      return moment(this.timelineDate).add('years', 1).diff(this.today) <= 0
    },
  },
  methods: {
    pickTimelineDate: function(date) {
      this.timelineDate = moment(date);
    },
    moveTimelineDate: function(quantity, unit) {
      this.timelineDate = moment(this.timelineDate).add(quantity, unit);
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