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
    timelineDate(){
      return moment(this.$route.query.date, 'YYYY-MM-DD', true);
    },
    today(){
      return moment().startOf('day');
    },
    relativeTimelineDate() {
      const duration = this.timelineDate.diff(moment().startOf('day'));
      return duration !== 0 ? moment.duration(duration).humanize(true) : 'today';
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
    routerDateLink(quantity, unit) {
      return {
        name: 'timeline',
        query: {
          ...this.$route.query,
          date: moment(this.timelineDate).add(quantity, unit).format('YYYY-MM-DD'),
        },
      }
    },
    moveTimelineDate(quantity, unit){
      this.$router.push(this.routerDateLink(quantity, unit));
    },
    onKeydown(event) {
      if(event.key === 'd' || event.key === 'ArrowRight'){
        this.moveTimelineDate('days', 1);
      }
      else if(event.key === 'D' || event.key === 'ArrowLeft'){
        this.moveTimelineDate('days', -1);
      }
      else if(event.key === 'w'){
        this.moveTimelineDate('weeks', 1);
      }
      else if(event.key === 'W'){
        this.moveTimelineDate('weeks', -1);
      }
      else if(event.key === 'm'){
        this.moveTimelineDate('months', 1);
      }
      else if(event.key === 'M'){
        this.moveTimelineDate('months', -1);
      }
      else if(event.key === 'y'){
        this.moveTimelineDate('years', 1);
      }
      else if(event.key === 'Y'){
        this.moveTimelineDate('years', -1);
      }
    },
  },
  template: `
    <nav class="timeline-nav">
      <div class="controls back">
        <router-link title="Next year — Press 'Y'" :to="routerDateLink('years', -1)">Y</router-link>
        <router-link title="Next month — Press 'M'" :to="routerDateLink('months', -1)">M</router-link>
        <router-link title="Next week — Press 'W'" :to="routerDateLink('weeks', -1)">W</router-link>
        <router-link title="Tomorrow — Right arrow or 'D'" :to="routerDateLink('days', -1)">D</router-link>
      </div>
      <h1>
        <time>{{ timelineDate.format('LL') }}</time>
        <small>{{ timelineDate.format('dddd') }}, {{ relativeTimelineDate }}</small>
      </h1>
      <div class="controls forward">
        <router-link title="Last year — Shift + Y" :disabled="!showTomorrow" :to="routerDateLink('days', 1)">D</router-link>
        <router-link title="Last month — Shift + M" :disabled="!showNextWeek" :to="routerDateLink('weeks', 1)">W</router-link>
        <router-link title="Last week — Shift + W" :disabled="!showNextMonth" :to="routerDateLink('months', 1)">M</router-link>
        <router-link title="Yesterday — Left arrow or Shift + D" :disabled="!showNextYear" :to="routerDateLink('years', 1)">Y</router-link>
      </div>
    </nav>
  `
});