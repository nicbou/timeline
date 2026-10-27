export default Vue.component('comment-entry', {
  props: ['entry'],
  data() {
    return { expanded: false };
  },
  computed: {
    time() {
      return moment(this.entry.start).format('H:mm');
    }
  },
  template: `
    <article class="entry comment" @click="expanded = !expanded" :class="{'expanded': expanded}">
      <i class="fa-brands fa-reddit"></i>
      <div class="meta">
        <a class="post-title" :href="entry.data.post_url" target="_blank" @click.stop>{{ entry.data.post_title }}</a>
        <span class="subreddit">r/{{ entry.data.subreddit }}</span>
      </div>
      <time>{{ time }}</time>
      <div class="body" v-if="expanded" v-html="entry.data.body" @click.stop></div>
    </article>
  `
});
