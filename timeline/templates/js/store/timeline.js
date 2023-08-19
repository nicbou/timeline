import { RequestStatus } from './../models/requests.js';
import config from './../config.js';

export default {
  namespaced: true,
  state: {
    entries: [],
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
  },
  getters: {
    filteredEntries: state => {
      return state.entries;
    }
  },
  actions: {
    async getEntries(context, forceRefresh=false) {
      if (context.state.entriesRequestStatus === RequestStatus.NONE || forceRefresh) {
        context.commit('ENTRIES_REQUEST_PENDING');
        const entriesRequestPromise = fetch(`${config.domain}/entries/${this.state.route.query.date}.json`)
          .then(response => response.ok ? response.json() : Promise.reject(response))
          .then(json => {
            context.commit('SET_ENTRIES', json.entries);
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
  }
};