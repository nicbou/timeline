import TimelineEntryIcon from './entry-icon.js';

export default Vue.component('activity-entry', {
  props: ['entry'],
  computed: {
    metaText: function() {
      if(this.entry.entry_type === 'search') {
        if(this.url.startsWith('https://maps.google.com')) {
          return 'Google Maps search';
        }
        else if(this.url.startsWith('https://www.google.com/search?tbm=isch&q=')) {
          return 'Google Images search';
        }
        else if(this.url.startsWith('https://translate.google.com/')) {
          return 'Google Translate';
        }
        else if(this.url.startsWith('https://www.google.com')) {
          return 'Google search';
        }
        else if(this.url.startsWith('https://youtube.com')) {
          return 'YouTube search';
        }
        else if(this.url.startsWith('https://twitter.com')) {
          return 'Twitter search';
        }
        else if(this.url.startsWith('https://www.urbandictionary.com/')) {
          return 'Urban Dictionary search';
        }
        else if(this.url.startsWith('https://www.wikipedia.org/')) {
          return 'Wikipedia search';
        }
        else if(this.url.startsWith('https://www.dict.cc')) {
          return 'dict.cc search';
        }
        return 'Other search';
      }
      else if(this.entry.entry_type === 'watch') {
        return 'YouTube video';
      }
      return 'Page view';
    },
    icon: function() {
      return this.entry.entry_type === 'search' ? `"${this.entry.title}"` : this.entry.title;
    },
    url: function() {
      return this.entry.data.url;
    },
    hostname: function() {
      let hostname = null;
      try {
        hostname = (new URL(this.url)).hostname.replace(/^(www\.)/,"");
      }
      catch {}
      return hostname;
    },
    entryClass: function() {
      if (this.hostname && this.hostname.startsWith('youtube.')) {
        return 'watch youtube';
      }
      else if(this.entry.entry_type === 'search') {
        return 'search';
      }
      return 'browse';
    },
    iconClass: function() {
      if (this.hostname && this.hostname.startsWith('youtube.')) {
        return 'fab fa-youtube';
      }
      else if(this.entry.entry_type === 'search') {
        return 'fas fa-search';
      }
      return 'fas fa-globe-americas';
    },
  },
  template: `
    <div :class="entryClass">
      <entry-icon :icon-class="iconClass" :entry="entry"></entry-icon>
      <div class="meta">{{ metaText }}</div>
      <div class="content">
        <a :href="url">"{{ entry.title }}"</a>
        <small v-if="entry.description">{{ entry.description }}</small>
      </div>
    </div>
  `
});