import config from './../../config.js';

export default Vue.component('search-entry', {
  props: ['entry'],
  computed: {
    time() {
      return moment(this.entry.date_start).format('H:mm');
    }
  },
  template: `
    <a class="entry search" :href="entry.data.url" target="_blank">
      <i class="fa-solid fa-magnifying-glass"></i>
      <div class="query">
        {{ entry.data.query }}
      </div>
      <time>{{ time }}</time>
    </a>
  `
});