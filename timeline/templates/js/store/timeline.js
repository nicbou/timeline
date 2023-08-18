import { RequestStatus } from './../models/requests.js';
import { filters } from './../models/filters.js';
import TimelineService from './../services/timeline-service.js';

export default {
  namespaced: true,
  state: {
    entries: [],
    enabledFilters: [],
    entriesRequestStatus: RequestStatus.NONE,
    entriesRequestPromise: null,
  },
  mutations: {
    SET_ENTRIES(state, entries) {
      state.entries = entries;
    },
    SET_ENTRIES_REQUEST_PROMISE(state, promise) {
      state.entriesRequestPromise = promise;
    },
    ENTRIES_REQUEST_SUCCESS(state) {
      state.entriesRequestStatus = RequestStatus.SUCCESS;
    },
    ENTRIES_REQUEST_PENDING(state) {
      state.entriesRequestStatus = RequestStatus.PENDING;
    },
    ENTRIES_REQUEST_FAILURE(state) {
      state.entriesRequestStatus = RequestStatus.FAILURE;
    },
    TOGGLE_FILTER(state, filterName) {
      const indexOf = state.enabledFilters.indexOf(filterName);
      if(indexOf >= 0) {
        state.enabledFilters.splice(indexOf, 1);
      }
      else {
        state.enabledFilters.push(filterName);
        state.enabledFilters.sort();
      }
    },
  },
  getters: {
    filteredEntries: state => {
      if(state.enabledFilters.length === 0) {
        return state.entries;
      }
      return state.entries.filter(
        entry => state.enabledFilters.some(filterName => filters[filterName].filterFunction(entry))
      );
    }
  },
  actions: {
    async getEntries(context, forceRefresh=false) {
      const timelineDate = moment(this.state.route.query.date, 'YYYY-MM-DD');
      if (context.state.entriesRequestStatus === RequestStatus.NONE || forceRefresh) {
        context.commit('ENTRIES_REQUEST_PENDING');
        const filters = {...this.state.route.query};
        delete filters['date'];
        const entriesRequestPromise = TimelineService.getEntries(timelineDate)
          .then(entries => {
            context.commit('SET_ENTRIES', entries);
            context.commit('ENTRIES_REQUEST_SUCCESS');
            return context.state.entries;
          })
          .catch(async response => {
            context.commit('SET_ENTRIES', []);
            context.commit('ENTRIES_REQUEST_FAILURE');
            return Promise.reject(response);
          });
        context.commit('SET_ENTRIES_REQUEST_PROMISE', entriesRequestPromise);
        return entriesRequestPromise;
      }
      return context.state.entriesRequestPromise;
    },
    toggleFilter(context, filterName) {
      if(!(filterName in filters)){
        throw new Error(`Filter "${filterName}" does not exist.`);
      }
      context.commit('TOGGLE_FILTER', filterName);
    },
  }
};