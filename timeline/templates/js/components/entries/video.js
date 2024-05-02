import config from './../../config.js';

export default Vue.component('video-entry', {
  props: ['entry'],
  computed: {
    videoSrc() {
      const pathParts = this.entry.file_path.split('.');
      const extension = pathParts[pathParts.length - 1];
      return `${config.siteUrl}/metadata/${this.entry.checksum}/thumbnail.webm`;
    },
    caption() {
      if(this.entry.data.location && this.entry.data.location.city){
        return [this.entry.data.location.city, this.entry.data.location.country].join(', ');
      }
    },
    time() {
      return moment(this.entry.date_start).format('H:mm');
    },
  },
  methods: {
    videoHoverStart: function() {
      this.$refs.videoElement.play()
    },
    videoHoverEnd: function() {
      this.$refs.videoElement.pause()
      this.$refs.videoElement.currentTime = 0;
    },
  },
  template: `
    <article class="entry video" @mouseover="videoHoverStart" @mouseleave="videoHoverEnd">
      <figure>
        <video :src="videoSrc"
          loop
          ref="videoElement"/>
        <figcaption v-if="caption">{{ caption }}</figcaption>
      </figure>
      <time v-if="time !== '0:00'">{{ time }}</time>
    </article>
  `
});
