import TimelineMap from './entry-map.js';
import TimelineNav from './timeline-nav.js';
import TimelineDiaryEntry from './entries/diary.js';
import TimelineEventEntry from './entries/event.js';
import TimelineImageEntry from './entries/image.js';
import TimelinePdfEntry from './entries/pdf.js';
import TimelineSearchEntry from './entries/search.js';
import TimelineTextEntry from './entries/text.js';
import TimelineTransactionEntry from './entries/transaction.js';
import TimelineVideoEntry from './entries/video.js';
import Weather from './weather.js';
import { formattedAmount } from './../libs/currency.js';
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
    lastLocation() {
      return this.entries
        .filter(e => e.data.location && e.data.location.latitude && e.data.location.longitude)
        .map(e => {
          return {
            lat: Number(e.data.location.latitude),
            lng: Number(e.data.location.longitude),
          };
        })
        .slice(-1)[0];

    },
    balances() {
      return this.$store.state.timeline.finances[this.$route.query.date];
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
    formattedAmount
  },
  mounted(){
    this.$store.dispatch('timeline/getFinances', true);
  },
  template: `
    <main id="layout">
      <timeline-nav id="timeline-nav"></timeline-nav>
      <div class="spinner" v-if="isLoading">Loading entries...</div>
      <div class="daily-summary" v-show="!isLoading">
        <div v-if="balances">
          <i class="fa-solid fa-piggy-bank"></i>
          {{ formattedAmount(balances.total.amount) }}
          <template v-if="balances.total.transactionAmount">
            ({{ formattedAmount(balances.total.transactionAmount) }})    
          </template>
        </div>
        <weather :date="timelineDate" :latitude="lastLocation?.lat" :longitude="lastLocation?.lng"></weather>
      </div>
      <entry-map v-show="!isLoading" :entries="entries"></entry-map>
      <component
        :entry="entry"
        :is="componentType(entry.entry_type)"
        :key="entry.key"
        v-for="entry in entries"
        v-if="!isLoading && componentType(entry.entry_type)"></component>
    </main>
  `
});