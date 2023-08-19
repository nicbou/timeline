import config from './../../config.js';

export default Vue.component('html-entry', {
  props: ['entry'],
  data() {
    return {
      html: null
    };
  },
  computed: {
    fileName: function() {
      const pathParts = this.entry.file_path.split('/');
      return pathParts[pathParts.length - 1];
    },
  },
  async mounted(){
    const req = await fetch(`${config.domain}/metadata/${this.entry.checksum}/content.html`);
    this.html = await req.text();
  },
  template: `
    <div class="entry html">
      <i class="icon fas fa-file-alt" :entry="entry"></i>
      <div class="meta">{{ fileName }}</div>
      <div class="content" v-html="html"></div>
    </div>
  `
});