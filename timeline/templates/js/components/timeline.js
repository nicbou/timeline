import SpinnerComponent from './spinner.js';
import TimelineMap from './entry-map.js';
import TransactionsList from './transactions.js';
import TimelineNav from './timeline-nav.js';
import TimelineDiaryEntry from './entries/diary.js';
import TimelineEventEntry from './entries/event.js';
import TimelineImageEntry from './entries/image.js';
import TimelinePdfEntry from './entries/pdf.js';
import TimelineTextEntry from './entries/text.js';
import TimelineVideoEntry from './entries/video.js';
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
      const componentName = entryType + '-entry';
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
      <timeline-nav id="timeline-nav"></timeline-nav>
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