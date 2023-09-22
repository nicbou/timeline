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
  data: function() {
    return {
      selectedEntry: null,
    }
  },
  created: function() {
    this.$store.dispatch('timeline/getEntries').catch(response => {
      if([401, 403].includes(response.status)) {
        this.$router.push({name: 'login'});
      }
    });
  },
  watch: {
    '$route.query': function() {
      this.selectedEntry = null;
      this.$store.dispatch('timeline/getEntries', true).catch(response => {
        if([401, 403].includes(response.status)) {
          this.$router.push({name: 'login'});
        }
      });
    }
  },
  beforeRouteEnter: makeRouteValid,
  beforeRouteUpdate: makeRouteValid,
  computed: {
    timelineDate: function(){
      return moment(this.$store.state.route.query.date, 'YYYY-MM-DD', true);
    },
    relativeTimelineDate: function() {
      const duration = this.timelineDate.diff(moment().startOf('day'));
      return duration !== 0 ? moment.duration(duration).humanize(true) : 'today';
    },
    entries: function() {
      return this.$store.getters['timeline/filteredEntries'];
    },
    transactions: function() {
      return this.entries.filter(e => e.entry_type === 'transaction');
    },
    isLoading: function() {
      return this.$store.state.timeline.entriesRequestStatus === RequestStatus.PENDING;
    },
  },
  methods: {
    componentType(entryType) {
      return {
        diary: 'html-entry',
      }[entryType] || entryType + '-entry';
    }
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
      <transactions :entries="transactions" v-if="transactions.length"></transactions>
      <component
        :entry="entry"
        :is="componentType(entry.entry_type)"
        v-for="entry in entries"
        v-if="componentType(entry.entry_type) && !isLoading"></component>
    </main>
  `
});