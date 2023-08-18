import TimelineEntryIcon from './entry-icon.js';

export default Vue.component('journal-entry', {
  props: ['entry'],
  data: function() {
    return {
      unsavedDescription: null,
      isEditing: false,
      isSaving: false,
    };
  },
  computed: {
    markdownDescription: function() {
      return this.entry.description ? marked(this.entry.description) : '<p class="placeholder">No text here</p>';
    },
  },
  methods: {
    edit: function() {
      this.unsavedDescription = this.entry.description;
      this.isEditing = true;
      this.$nextTick(() => {
        this.$refs.editor.focus();
      });
    },
    saveChanges: function(){
      this.isSaving = true;
      if(this.unsavedDescription.length) {
        this.entry.description = this.unsavedDescription;
        this.$store.dispatch('timeline/updateEntry', this.entry).then(e => {
          this.unsavedDescription = null;
          this.isEditing = false;
          this.isSaving = false;
        });
      }
      else {
        this.deleteEntry();
      }
    },
    deleteEntry: function() {
      this.$store.dispatch('timeline/deleteEntry', this.entry);
    },
    cancelChanges: function() {
      this.isEditing = false;
      this.unsavedDescription = null;
    },
  },
  template: `
    <div class="journal">
      <entry-icon icon-class="fas fa-pen-square" :entry="entry"></entry-icon>
      <div class="meta">Journal entry</div>
      <div class="content" :class="{editing: isEditing}">
        <textarea ref="editor" class="journal-content" v-if="isEditing" v-model="unsavedDescription"></textarea>
        <div class="input-group" v-if="isEditing">
          <button class="button" @click.stop.prevent="saveChanges" :disabled="isSaving">Save changes</button>
          <button class="button" @click.stop.prevent="deleteEntry" :disabled="isSaving">Delete entry</button>
          <button class="button" @click.stop.prevent="cancelChanges" :disabled="isSaving">Cancel</button>
        </div>
        <div v-html="markdownDescription" v-if="!isEditing" @click="edit"></div>
      </div>
    </div>
  `
});