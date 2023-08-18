export default Vue.component('image-thumbnail', {
  props: ['entry', 'height'],
  computed: {
    src: function() {
      return this.entry.data.previews.thumbnail;
    },
    srcset: function() {
      return `${this.entry.data.previews.thumbnail} 1x, ${this.entry.data.previews.thumbnail2x} 2x`;
    },
    width: function() {
      // Some entries can have a preview but no width. For example, a PDF has no width.
      if(this.entry.data.media && this.entry.data.media.width && this.entry.data.height){
        return Math.floor(this.entry.data.media.width/entry.data.media.height * this.height)
      }
    }
  },
  template: `
    <img
      @click="$emit('select', entry)"
      :alt="entry.title"
      :height="height"
      :src="src"
      :srcset="srcset"
      :title="entry.title"
      :width="width"
      />
  `
});