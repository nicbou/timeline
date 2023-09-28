import config from './../../config.js';

export default Vue.component('event-entry', {
  props: ['entry'],
  data() {
    return {
      expanded: false,
    }
  },
  computed: {
    dateStart: function() {
      return new Date(this.entry.date_start);
    },
    dateEnd: function() {
      return this.entry.date_end ? new Date(this.entry.date_end) : null;
    },
    description: function() {
      return (this.entry.data.description || '').trim().replaceAll('<br><br>', '<br>').replaceAll('\n', '<br>');
    }
  },
  template: `
    <article class="entry event" @click="expanded = !expanded" :class="{'expanded': expanded}">
      <i class="fa-regular fa-calendar"></i>
      <time>{{ dateStart.toLocaleTimeString('en-GB', {hour: 'numeric', minute:'2-digit'}) }}</time>
      <div class="summary">{{ entry.data.summary.replaceAll('\\n', ', ') }}</div>
      <div class="description" v-if="description" v-html="description"></div>
    </article>
  `
});