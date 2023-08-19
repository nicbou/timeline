import config from './../../config.js';

export default Vue.component('text-entry', {
  props: ['entry'],
  data() {
    return {
      text: null
    };
  },
  computed: {
    fileName: function() {
      const pathParts = this.entry.file_path.split('/');
      return pathParts[pathParts.length - 1];
    },
    paragraphs: function() {
      return this.text.split('\n\n');
    },
  },
  async mounted(){
    const req = await fetch(`${config.domain}/metadata/${this.entry.checksum}/content.txt`);
    this.text = await req.text();
  },
  template: `
    <article class="entry text">
      <i class="icon fas fa-file-alt" :entry="entry"></i>
      <div class="meta">{{ fileName }}</div>
      <div class="content">
        <p v-for="paragraph in paragraphs">{{ paragraph }}</p>
      </div>
    </article>
  `
});