import config from './../../config.js';

export default Vue.component('image-entry', {
  props: ['entry'],
  computed: {
    imgSrc() {
      const pathParts = this.entry.file_path.split('.');
      const extension = pathParts[pathParts.length - 1];
      return `${config.siteUrl}/metadata/${this.entry.checksum}/thumbnail.webp`;
    },
    caption() {
      if(this.entry.data.location && this.entry.data.location.city){
        return [this.entry.data.location.city, this.entry.data.location.country].join(', ');
      }
    },
    time() {
      return moment(this.entry.date_start).format('H:mm');
    },
    cssBackground() {
      return `url("${this.imgSrc}")`;
    },
  },
  template: `
    <article class="entry image" :style="{backgroundImage: cssBackground}">
      <figure>
        <img :src="imgSrc">
        <figcaption v-if="caption">{{ caption }}</figcaption>
      </figure>
      <time v-if="time !== '0:00'">{{ time }}</time>
    </article>
  `
});