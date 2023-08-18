import TimelineEntryIcon from './entry-icon.js';

export default Vue.component('text-entry', {
  props: ['entry'],
  computed: {
    fileName: function() {
      const pathParts = this.entry.data.file.path.split('/');
      return pathParts[pathParts.length - 1];
    },
    richDescription: function() {
      if (this.entry.data.file.mimetype === 'text/markdown'){
        return marked(this.entry.description);
      }
      return '<p>' + this.entry.description.replaceAll('\n', '</p><p>') + '</p>';
    },
  },
  template: `
    <div>
      <entry-icon icon-class="fas fa-file-alt" :entry="entry"></entry-icon>
      <div class="meta">{{ fileName }}</div>
      <div class="content" v-html="richDescription"></div>
    </div>
  `
});