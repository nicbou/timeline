import TimelineComponent from './components/timeline.js';
import store from './store/store.js';


const router = new VueRouter({
  mode: 'history',
  routes: [
    {
      path: '/timeline',
      name: 'timeline',
      component: TimelineComponent,
    },
    {
      path: '/',
      redirect: { name: 'timeline' }
    },
  ]
});

export default router;
