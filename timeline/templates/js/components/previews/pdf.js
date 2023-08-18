import ImagePreview from './image.js';

export default Vue.component('pdf-preview', {
  props: ['entry'],
  computed: {
  },
  template: `
    <object :data="entry.data.file.path" type="application/pdf">
      <image-preview :entry="entry"></image-preview>
    </object>
  `
});
