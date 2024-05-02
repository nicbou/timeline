import config from './../../config.js';

export default Vue.component('text-entry', {
  props: ['entry'],
  data() {
    return {
      text: '',
    };
  },
  computed: {
    fileName: function() {
      const pathParts = this.entry.file_path.split('/');
      return pathParts[pathParts.length - 1];
    },
  },
  async mounted(){
    const req = await fetch(`${config.siteUrl}/metadata/${this.entry.checksum}/content.txt`);
    this.text = await req.text();
  },
  template: `
    <article class="entry text">
      <main>
        <pre>{{ text }}</pre>
      </main>
    </article>
  `
});