import router from './routes.js';
import store from './store/store.js';

export const app = new Vue({
  el: '#page',
  router,
  store,
});