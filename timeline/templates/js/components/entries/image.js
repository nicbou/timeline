import config from './../../config.js';

export default Vue.component('image-entry', {
  props: ['entry'],
  computed: {
    imgSrc: function() {
      const pathParts = this.entry.file_path.split('.');
      const extension = pathParts[pathParts.length - 1];
      return `${config.domain}/metadata/${this.entry.checksum}/thumbnail.webp`;
    },
  },
  template: `
    <article class="entry image">
      <img :src="imgSrc">
    </article>
  `
});