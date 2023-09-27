import SpinnerComponent from './spinner.js';
import TimelineMap from './entry-map.js';
import TransactionsList from './transactions.js';
import TimelineNav from './timeline-nav.js';
import TimelineHtmlEntry from './entries/html.js';
import TimelineImageEntry from './entries/image.js';
import TimelineTextEntry from './entries/text.js';
import { RequestStatus } from './../models/requests.js';

function makeRouteValid(to, from, next) {
  // Enforce a valid current date in the route
  if (to.query.date) {
    const newDate = moment(to.query.date, 'YYYY-MM-DD', true);
    if(newDate.isValid()) {
      next();
      return;
    }
  }
  const queryParams = { ...to.query };
  queryParams.date = moment().format('YYYY-MM-DD');
  next({ name: 'timeline', query: queryParams });
}

export default Vue.component('timeline', {
  created() {
    this.$store.dispatch('timeline/getEntries', { date: this.$route.query.date });
  },
  watch: {
    '$route.query': function() {
      this.$store.dispatch('timeline/getEntries', { date: this.$route.query.date, forceRefresh: true, });
    },
  },
  beforeRouteEnter: makeRouteValid,
  beforeRouteUpdate: makeRouteValid,
  computed: {
    timelineDate(){
      return moment(this.$route.query.date, 'YYYY-MM-DD', true);
    },
    relativeTimelineDate() {
      const duration = this.timelineDate.diff(moment().startOf('day'));
      return duration !== 0 ? moment.duration(duration).humanize(true) : 'today';
    },
    entries() {
      return this.$store.state.timeline.entries;
    },
    finances() {
      return this.$store.state.timeline.finances;
    },
    transactions() {
      return this.entries.filter(e => e.entry_type === 'transaction');
    },
    isLoading() {
      return this.$store.state.timeline.entriesRequestStatus === RequestStatus.PENDING;
    },
  },
  methods: {
    componentType(entryType) {
      const componentName = {
        diary: 'html-entry',
      }[entryType] || entryType + '-entry';

      if(componentName in Vue.options.components){
        return componentName;
      }
    },
  },
  mounted(){
    this.$store.dispatch('timeline/getFinances', true);
  },
  template: `
    <main id="layout">
      <header>
        <timeline-nav id="timeline-nav"></timeline-nav>
        <h1 class="current-date">
          <time>{{ timelineDate.format('LL') }}</time>
          <small>{{ timelineDate.format('dddd') }}, {{ relativeTimelineDate }}</small>
        </h1>
      </header>
      <spinner v-if="isLoading"></spinner>
      <entry-map :entries="entries"></entry-map>
      <transactions :entries="transactions" :finances="finances" :current-date="timelineDate"></transactions>
      <component
        :entry="entry"
        :is="componentType(entry.entry_type)"
        v-for="entry in entries"
        v-if="componentType(entry.entry_type)"></component>
    </main>
  `
});