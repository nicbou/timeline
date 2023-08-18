export default Vue.component('image-preview', {
  props: ['entry'],
  computed: {
    imageSrcSet: function() {
        return `${this.entry.data.previews.preview} 1x, ${this.entry.data.previews.preview2x} 2x`;
    },
  },
  template: `
    <img
      :alt="entry.title"
      :src="entry.data.previews.preview"
      :srcset="imageSrcSet"
      />
  `
});