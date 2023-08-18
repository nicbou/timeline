export default Vue.component('entry-icon', {
  props: ['entry', 'iconClass'],
  template: `
    <router-link
      :to="{ path: $route.fullPath, query: { source: entry.source }}" :title="'Show only ' + entry.source + ' entries'"
      class="icon" :class="iconClass">
    </router-link>
  `
});