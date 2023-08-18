export default Vue.component('video-preview', {
  props: ['entry'],
  template: `
    <video autoplay controls
      :alt="entry.title"
      :src="entry.data.previews.preview"/>
  `
});