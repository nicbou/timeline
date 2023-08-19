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
    dateStart: function() {
      return new Date(this.entry.date_start);
    }
  },
  async mounted(){
    const req = await fetch(`${config.domain}/metadata/${this.entry.checksum}/content.html`);
    this.html = await req.text();
  },
  template: `
    <article class="entry html">
      <details>
        <summary>
          <datetime>{{ dateStart.toLocaleTimeString('en-GB', {hour: 'numeric', minute:'2-digit'}) }}</datetime>
          <h2>{{ fileName }}</h2>
        </summary>
        <div class="content" v-html="html"></div>
      <details>
    </article>
  `
});