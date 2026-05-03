import config from './../../config.js';

export default Vue.component('pdf-entry', {
  props: ['entry'],
  computed: {
    imgSrc() {
      return `${config.siteUrl}/metadata/${this.entry.checksum}/thumbnail.webp`;
    },
  },
  methods: {
    onMouseMove(event){
      const targetRect = event.currentTarget.getBoundingClientRect();
      var y = event.clientY - targetRect.top;  //y position within the element.

      const relativePosition = (y / this.$refs.figure.offsetHeight);
      const imageHeight = this.$refs.image.naturalHeight / this.$refs.image.naturalWidth * this.$refs.figure.offsetWidth;
      const distanceToScroll = (imageHeight - this.$refs.figure.offsetHeight);
      this.$refs.image.style.objectPosition = `center ${relativePosition * -distanceToScroll}px`;
    }
  },
  template: `
    <article class="entry image pdf">
      <figure ref="figure" @mousemove.capture="onMouseMove">
        <img ref="image" :src="imgSrc">
        <figcaption>{{ entry.file_name }}</figcaption>
      </figure>
    </article>
  `
});