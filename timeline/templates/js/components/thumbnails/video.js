export default Vue.component('video-thumbnail', {
  props: ['entry', 'height'],
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
    <video
      :alt="entry.title"
      :height="height"
      :src="entry.data.previews.thumbnail"
      @click="$emit('select', entry)"
      @mouseleave="videoHoverEnd"
      @mouseover="videoHoverStart"
      loop
      ref="videoElement"/>
  `
});