import sync from './libs/vuex-router-sync.js';
import router from './routes.js';
import store from './store/store.js';

sync(store, router, { moduleName: 'route' } );

export const app = new Vue({
  el: '#page',
  router,
  store,
});