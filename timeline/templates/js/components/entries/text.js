import config from './../../config.js';

export default Vue.component('text-entry', {
  props: ['entry'],
  data() {
    return {
      text: '',
    };
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