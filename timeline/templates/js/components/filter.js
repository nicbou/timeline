import { filters } from './../models/filters.js';

export default Vue.component('entry-filter', {
  props: ['name'],
  computed: {
    filter: function() {
      return filters[this.name];
    },
    entries: function() {
      return this.$store.state.timeline.entries.filter(this.filter.filterFunction);
    },
    filterName: function() {
      if(this.entries.length === 1) {
        return `1 ${this.filter.displayName}`;
      }
      return `${this.entries.length} ${this.filter.displayNamePlural}`;
    },
    isEnabled: function() {
      return this.$store.state.timeline.enabledFilters.includes(this.name);
    },
    isDisabled: function() {
      return (
        this.$store.state.timeline.enabledFilters.length > 0
        && !this.$store.state.timeline.enabledFilters.includes(this.name)
      );
    }
  },
  methods: {
    toggleFilter: function() {
      this.$store.dispatch('timeline/toggleFilter', this.name);
    },
  },
  template: `
    <div v-if="isEnabled || entries.length" class="filter" :class="{disabled: isDisabled}" @click="toggleFilter">
      <i class="icon" :class="filter.iconClass"></i>
      <span class="filter-name">{{ filterName }}</span>
    </div>
  `
});