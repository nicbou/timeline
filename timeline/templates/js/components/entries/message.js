import TimelineEntryIcon from './entry-icon.js';

export default Vue.component('message-entry', {
  props: ['entry'],
  computed: {
    iconClass: function() {
      if (this.entry.entry_type === 'message.text.sms') {
        return 'fas fa-sms';
      }
      else if (this.entry.entry_type === 'message.telegram'){
        return 'fab fa-telegram-plane';
      }
      else if (this.entry.entry_type === 'message.facebook'){
        return 'fab fa-facebook-messenger';
      }
      else if (this.entry.entry_type === 'message.reddit'){
        return 'fab fa-reddit';
      }
    },
    entryClass: function() {
      if (this.entry.entry_type === 'message.text.sms') {
        return 'sms';
      }
      else if (this.entry.entry_type === 'message.telegram'){
        return 'telegram';
      }
      else if (this.entry.entry_type === 'message.facebook'){
        return 'facebook-messenger';
      }
      else if (this.entry.entry_type === 'message.reddit'){
        return 'reddit';
      }
    },
    senderName: function() {
      return this.entry.data.sender_name || this.entry.data.sender_id;
    },
    recipientName: function() {
      return this.entry.data.recipient_name || this.entry.data.recipient_id;
    },
  },
  template: `
    <div :class="entryClass">
      <entry-icon :icon-class="iconClass" :entry="entry"></entry-icon>
      <div class="meta">
        <span :title="senderName" class="sender">{{ senderName }}</span>
         ▸ 
        <span :title="recipientName" class="recipient">{{ recipientName }}</span>
      </div>
      <div class="content">
        <image-thumbnail
          v-if="entry.data.file && entry.data.file.mimetype.startsWith('image/') && entry.data.previews"
          @select="$emit('select', entry)"
          :entry="entry"></image-thumbnail>
        <video-thumbnail
          v-if="entry.data.file && entry.data.file.mimetype.startsWith('video/') && entry.data.previews"
          @select="$emit('select', entry)"
          :entry="entry"></video-thumbnail>
        <audio controls
          v-if="entry.data.file && entry.data.file.mimetype.startsWith('audio/')" :src="entry.data.file.path"></audio>
        {{ entry.description }}
      </div>
    </div>
  `
});