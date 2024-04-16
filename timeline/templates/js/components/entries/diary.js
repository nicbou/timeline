import config from './../../config.js';

export default Vue.component('diary-entry', {
  props: ['entry'],
  data() {
    return {
      expanded: false,
      html: null,
    }
  },
  async mounted(){
    const req = await fetch(`${config.domain}/metadata/${this.entry.checksum}/content.html`);
    this.html = await req.text();
  },
  template: `
    <article v-if="html" class="entry diary" @click="expanded = !expanded" :class="{'expanded': expanded}">
      <main v-html="html"></main>
    </article>
  `
});