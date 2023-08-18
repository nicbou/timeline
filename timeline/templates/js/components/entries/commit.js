import TimelineEntryIcon from './entry-icon.js';

export default Vue.component('commit-entry', {
  props: ['entry'],
  computed: {
    filesChangedString: function() {
      if(this.entry.data.changes.files === 1) {
        return `${this.entry.data.changes.files} file changed`;
      }
      return `${this.entry.data.changes.files} files changed`;
    }
  },
  template: `
    <div class="commit">
      <entry-icon icon-class="fab fa-git-square" :entry="entry"></entry-icon>
      <div class="meta">
        <a target="_blank" :href="entry.data.url || entry.data.repo.url">Commit</a> to <a target="_blank" :href="entry.data.repo.url">{{ entry.data.repo.name }}</a>
      </div>
      <div class="content">
        {{ entry.title }}
        <small>
          {{ filesChangedString }}
          (+{{ entry.data.changes.insertions }}, -{{ entry.data.changes.deletions }})
        </small>
      </div>
    </div>
  `
});