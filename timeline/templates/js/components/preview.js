import ImagePreview from './previews/image.js';
import PdfPreview from './previews/pdf.js';
import VideoPreview from './previews/video.js';
import { hasGeolocation } from './../utils/entries.js';

export default Vue.component('preview', {
  props: ['entry'],
  computed: {
    mimetype: function(){
      if (this.entry.data && this.entry.data.file) {
        return this.entry.data.file.mimetype;
      }
      return undefined;
    },
    previewType: function() {
      if (this.mimetype.startsWith('image/')) {
        return 'image-preview';
      }
      else if(this.mimetype.startsWith('video/')) {
        return 'video-preview';
      }
      else if(this.mimetype === 'application/pdf') {
        return 'pdf-preview';
      }
    },
  },
  methods: {
    hasGeolocation,
    close: function(event) {
      this.$emit('close');
    }
  },
  template: `
    <div class="preview modal content-with-sidebar">
      <div class="content">
        <button class="button close" @click="close" title="Close"><i class="fas fa-times"></i></button>
        <component :is="previewType" :entry="entry"></component>
      </div>
      <div class="sidebar">
        <dl>
          <div class="attribute" v-show="entry.title">
            <dt>Title</dt>
            <dd>{{ entry.title }}</dd>
          </div>
          <div class="attribute" v-show="entry.description">
            <dt>Description</dt>
            <dd>{{ entry.description }}</dd>
          </div>
          <div class="attribute">
            <dt>Source</dt>
            <dd>
              <router-link :to="{ path: $route.fullPath, query: { source: entry.source }}">{{ entry.source }}</router-link>
            </dd>
          </div>
          <div class="attribute">
            <dt>Type</dt>
            <dd>{{ entry.data.file.mimetype }}</dd>
          </div>
          <div class="attribute">
            <dt>Path</dt>
            <dd>{{ entry.data.file.path }}</dd>
          </div>
          <div class="attribute" v-if="hasGeolocation(entry)">
            <dt>Location</dt>
            <dd>
              <entry-map class="map" :entries="[entry]"></entry-map>
              <small>
                <i class="fas fa-map-marker-alt"></i>
                {{ entry.data.location.latitude }}, {{ entry.data.location.longitude }}
              </small>
            </dd>
          </div>
          <div class="attribute">
            <dt>Actions</dt>
            <dl>
              <div class="input-group vertical">
                <a v-if="entry.data.file.path" class="button" title="Save this file to your device" :href="entry.data.file.path" target="_blank">
                  <i class="fas fa-search"></i>
                  Show original
                </a>
                <a v-if="entry.data.file.path" class="button" title="Save this file to your device" :href="entry.data.file.path" download>
                  <i class="fas fa-download"></i>
                  Download
                </a>
              </div>
            </dl>
          </div>
        </dl>
      </div>
    </div>
  `
});