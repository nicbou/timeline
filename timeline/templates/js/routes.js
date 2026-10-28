import TimelineComponent from './components/timeline.js';
import CountryMapComponent from './components/country-map.js';
import store from './store/store.js';


const router = new VueRouter({
  mode: 'hash',
  routes: [
    {
      path: '/timeline',
      name: 'timeline',
      component: TimelineComponent,
    },
    {
      path: '/map',
      name: 'map',
      component: CountryMapComponent,
    },
    {
      path: '/map/:countryCode',
      name: 'country',
      component: CountryMapComponent,
    },
    {
      path: '/',
      redirect: { name: 'timeline' }
    },
  ]
});

export default router;
