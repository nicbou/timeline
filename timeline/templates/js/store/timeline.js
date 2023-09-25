import { RequestStatus } from './../models/requests.js';
import config from './../config.js';

export default {
  namespaced: true,
  state: {
    entries: [],
    finances: {},
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

    SET_FINANCES(state, finances) {
      state.finances = finances;
    },
    SET_FINANCES_REQUEST_PROMISE(state, promise) {
      state.financesRequestPromise = promise;
    },
    FINANCES_REQUEST_SUCCESS(state) {
      state.financesRequestStatus = RequestStatus.SUCCESS;
    },
    FINANCES_REQUEST_PENDING(state) {
      state.financesRequestStatus = RequestStatus.PENDING;
    },
    FINANCES_REQUEST_FAILURE(state) {
      state.financesRequestStatus = RequestStatus.FAILURE;
    },
  },
  actions: {
    async getEntries(context, { date, forceRefresh }) {
      if (context.state.entriesRequestStatus === RequestStatus.NONE || forceRefresh) {
        context.commit('ENTRIES_REQUEST_PENDING');
        const entriesRequestPromise = fetch(`${config.domain}/entries/${date}.json`)
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
    async getFinances(context, forceRefresh=false) {
      if (context.state.financesRequestStatus === RequestStatus.NONE || forceRefresh) {
        context.commit('FINANCES_REQUEST_PENDING');
        const financesRequestPromise = fetch(`${config.domain}/entries/finances.json`)
          .then(response => response.ok ? response.json() : Promise.reject(response))
          .then(json => {
            context.commit('SET_FINANCES', json);
            context.commit('FINANCES_REQUEST_SUCCESS');
            return context.state.finances;
          })
          .catch(async response => {
            context.commit('SET_FINANCES', []);
            context.commit('FINANCES_REQUEST_FAILURE');
            return Promise.reject(response);
          });
        context.commit('SET_FINANCES_REQUEST_PROMISE', financesRequestPromise);
        return financesRequestPromise;
      }
      return context.state.financesRequestPromise;
    },
  }
};