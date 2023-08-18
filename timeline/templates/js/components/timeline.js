import SpinnerComponent from './spinner.js';
import TimelineHtmlEntry from './entries/html.js';
import TimelineNav from './timeline-nav.js';
import TimelineTextEntry from './entries/text.js';
import { filters } from './../models/filters.js';
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
      filters,
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
    isLoading: function() {
      return this.$store.state.timeline.entriesRequestStatus === RequestStatus.PENDING;
    },
    transactionsEntries: function() {
      return this.entries.filter(this.filters.transaction.filterFunction);
    },
  },
  methods: {
  },
  template: `
    <div id="timeline">
      <header>
        <timeline-nav id="timeline-nav"></timeline-nav>
      </header>
      <main class="content-with-sidebar">
        <div class="sidebar">
          <h1 class="current-date">{{ timelineDate.format('LL') }}</h1>
          <span class="subtitle">{{ timelineDate.format('dddd') }}, {{ relativeTimelineDate }}</span>
        </div>
        <div class="content entries">
          <spinner v-if="isLoading"></spinner>
          <component
            :entry="entry"
            :is="entry.entry_type + '-entry'"
            :key="entry.id"
            class="entry"
            v-for="entry in entries"
            v-if="!isLoading"></component>
        </div>
      </main>
    </div>
  `
});