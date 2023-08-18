import EntryFilter from './filter.js'
import EntryMap from './previews/geolocation.js'
import JournalEntry from './entries/journal.js'
import Preview from './preview.js';
import SpinnerComponent from './spinner.js';
import TimelineActivityEntry from './entries/activity.js';
import TimelineCommitEntry from './entries/commit.js';
import TimelineGalleryEntry from './entries/gallery.js';
import TimelineHtmlEntry from './entries/html.js';
import TimelineJournalEntry from './entries/journal.js'
import TimelineMessageEntry from './entries/message.js';
import TimelineNav from './timeline-nav.js';
import TimelinePostEntry from './entries/post.js'
import TimelineTextEntry from './entries/text.js';
import TransactionEntry from './entries/transaction.js';
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
      isJournalModalOpen: false,
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
    groupedEntries: function() {
      // Group entries by time, in roughly 1 hour groups
      let lastGroupDate = null;
      let lastGroupName = null;
      const timeGroups = this.entries.reduce((groups, entry) => {
        const timeDiff = lastGroupDate ? (new Date(entry.date_on_timeline) - lastGroupDate)/1000 : 0;
        if(!lastGroupDate || timeDiff > 3600) {
          lastGroupDate = new Date(entry.date_on_timeline);
          lastGroupName = entry.date_on_timeline;
          groups[lastGroupName] = [];
        }

        groups[lastGroupName].push(entry);
        return groups;
      }, []);
      const sortedTimeGroups = Object.keys(timeGroups).sort().map(key => timeGroups[key]);

      // Combine media entries within a time group into a single gallery
      return sortedTimeGroups.map(timeGroup => {
        const isMediaEntry = entry => {
          return ['image', 'pdf', 'video'].includes(entry.entry_type);
        };

        let galleryIndex = null;
        return timeGroup.reduce((entries, entry, index) => {
          const isGalleryEntry = ['image', 'pdf', 'video'].includes(entry.entry_type);

          // The first media in the group becomes a gallery. The other ones get deleted.
          if(isGalleryEntry) {
            if(galleryIndex === null){
              galleryIndex = index;
              entries.push([]); // Create a gallery - a subgroup of entries
            }
            entries[galleryIndex].push(entry);
          }
          else {
            entries.push(entry);
          }
          return entries;
        }, []);
      });
    },
    isLoading: function() {
      return this.$store.state.timeline.entriesRequestStatus === RequestStatus.PENDING;
    },
    transactionsEntries: function() {
      return this.entries.filter(this.filters.transaction.filterFunction);
    },
  },
  methods: {
    clearSource: function() {
      const queryParams = { ...this.$store.state.route.query };
      delete queryParams.source;
      this.$router.push({ name: 'timeline', query: queryParams });
    },
    openPreview: function(entry) {
      this.selectedEntry = entry;
    },
    closePreview: function() {
      this.selectedEntry = null;
    },
    entryGroupTitle: function(group) {
      const firstEntry = Array.isArray(group[0]) ? group[0][0] : group[0];
      return this.formattedTime(firstEntry.date_on_timeline);
    },
    entryType: function(entry) {
      if(Array.isArray(entry)) {
        return 'gallery';
      }

      const t = entry.entry_type;
      if(t === 'browse') {
        return 'activity-entry';
      }
      else if(t === 'commit') {
        return 'commit-entry';
      }
      else if(t === 'html') {
        return 'html-entry';
      }
      else if(t === 'journal') {
        return 'journal-entry';
      }
      else if(t === 'message') {
        return 'message-entry';
      }
      else if(t === 'post' || t === 'comment') {
        return 'post-entry';
      }
      else if(t === 'text') {
        return 'text-entry';
      }
      else if(t === 'watch') {
        return 'watch-entry';
      }
    },
    formattedTime: function(dateString) {
      const date = new Date(dateString);
      return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
    }
  },
  template: `
    <div id="timeline" :class="{'modal-open': !!selectedEntry || isJournalModalOpen}">
      <header>
        <timeline-nav id="timeline-nav"></timeline-nav>
      </header>
      <main class="content-with-sidebar">
        <div class="sidebar">
          <h1 class="current-date">{{ timelineDate.format('LL') }}</h1>
          <span class="subtitle">{{ timelineDate.format('dddd') }}, {{ relativeTimelineDate }}</span>
          <entry-map class="map" v-show="!isLoading" :entries="entries"></entry-map>
          <ul class="recap" v-if="!isLoading">
            <li v-if="$route.query.source" @click="clearSource">
              <div class="filter source">
                <i class="icon fas fa-sign-in-alt"></i>
                <span class="filter-name">{{ $route.query.source }}</span>
              </div>
            </li>
            <li v-for="(filter, filterName) in filters" :key="filterName"><entry-filter :name="filterName"></entry-filter></li>
          </ul>
        </div>
        <div class="content entries">
          <spinner v-if="isLoading"></spinner>
          <button class="button" @click="isJournalModalOpen=true" v-show="!isLoading"><i class="fas fa-pen"></i> Write something</button>
          <div class="entry-group" v-for="group in groupedEntries" :data-group-title="entryGroupTitle(group)">
            <component
              :entry="entry"
              :is="entryType(entry)"
              :key="entry.id"
              @select="openPreview"
              class="entry"
              v-for="entry in group"
              v-if="entryType(entry) && !isLoading"></component>
          </div>
          <div class="separator" v-if="transactionsEntries.length">Unknown time</div>
          <transaction-entry
            :entry="entry"
            :key="entry.id"
            class="entry"
            v-for="entry in transactionsEntries"></transaction-entry>
        </div>
      </main>
      <preview :entry="selectedEntry" v-if="selectedEntry" @close="closePreview"></preview>
    </div>
  `
});