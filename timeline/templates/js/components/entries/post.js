import TimelineEntryIcon from './entry-icon.js';

const postTypes = {
  twitter: {
    getIconClass: entry => 'fab fa-twitter',
    getUser: entry => `@${entry.data.post_user}`,
    getUserUrl: entry => `https://twitter.com/${entry.data.post_user}`,
    getPostUrl: entry => `https://twitter.com/${entry.data.post_user}/status/${entry.data.post_id}`,
    getPostWebsite: entry => 'Twitter',
    getPostCommunity: entry => null,
    getPostCommunityUrl: entry => null,
    getPostType: entry => 'Tweet',
    getRichDescription: entry => `<p>${entry.description}</p>`.replace(/@([\w]{1,50})/ig, '<a target="_blank" href="https://twitter.com/$1">@$1</a>'),
  },
  reddit: {
    getIconClass: entry => 'fab fa-reddit',
    getUser: entry => entry.data.post_user,
    getUserUrl: entry => `https://reddit.com/user/${entry.data.post_user}`,
    getPostUrl: entry => `https://reddit.com/comments/${entry.data.post_thread_id}/_/${entry.data.post_id}`,
    getPostWebsite: entry => 'Reddit',
    getPostCommunity: entry => `/r/${entry.data.post_community}`,
    getPostCommunityUrl: entry => `https://www.reddit.com/r/${entry.data.post_community}`,
    getPostType: entry => entry.entry_type === 'social.reddit.comment' ? 'Comment' : 'Post',
    getRichDescription: entry => {
      if(entry.entry_type === 'social.reddit.post') {
        return `<h3><a href="${entry.data.post_url}">${entry.title}</a></h3>`;
      }
      return entry.data.post_body_html;
    },
  },
  hackernews: {
    getIconClass: entry => 'fab fa-y-combinator',
    getUser: entry => entry.data.post_user,
    getUserUrl: entry => `https://news.ycombinator.com/submitted?id=${entry.data.post_user}`,
    getPostUrl: entry => `https://news.ycombinator.com/item?id=${entry.data.post_id}`,
    getPostWebsite: entry => 'Hacker News',
    getPostCommunity: entry => null,
    getPostCommunityUrl: entry => null,
    getPostType: entry => entry.entry_type === 'social.hackernews.comment' ? 'Comment' : 'Submission',
    getRichDescription: entry => {
      if(entry.entry_type === 'social.hackernews.story'){
        return `<h3><a href="https://news.ycombinator.com/item?id=${entry.data.post_id}">${entry.title}</a></h3>`
      }
      else {
        // The first paragraph isn't wrapped in a <p> tag
        return '<p>' + entry.data.post_body_html.replace('<p>', '</p><p>');
      }
    },
  },
  blog: {
    getIconClass: entry => 'fas fa-rss',
    getUser: entry => entry.data.post_user,
    getUserUrl: entry => null,
    getPostUrl: entry => entry.data.post_url,
    getPostWebsite: entry => 'Website',
    getPostCommunity: entry => new URL(entry.data.post_url).hostname,
    getPostCommunityUrl: entry => new URL(entry.data.post_url).hostname,
    getPostType: entry => 'Post',
    getRichDescription: entry => entry.data.post_body_html,
  },
}

export default Vue.component('post-entry', {
  props: ['entry'],
  computed: {
    postClass: function() {
      return this.entry.entry_type.split('.')[1];
    },
    postType: function() {
      return postTypes[this.postClass];
    },
  },
  template: `
    <div :class="postClass">
      <entry-icon :icon-class="postType.getIconClass(entry)" :entry="entry"></entry-icon>
      <div class="meta">
        <a :href="postType.getPostUrl(entry)" class="user" target="_blank">{{ postType.getPostType(entry) }}</a>
        <span v-if="postType.getPostCommunity(entry)">
          on <a :href="postType.getPostCommunityUrl(entry)" class="community" target="_blank">{{ postType.getPostCommunity(entry) }}</a>
        </span>
        <span v-if="!postType.getPostCommunity(entry)">
          on <a :href="postType.getPostUrl(entry)" class="community" target="_blank">{{ postType.getPostWebsite(entry) }}</a>
        </span>
        <span v-if="entry.data.post_score !== undefined && entry.data.post_score !== null" class="score" :class="{positive: entry.data.post_score >= 1, negative: entry.data.post_score < 1}">{{ entry.data.post_score }}</span>
      </div>
      <div class="content" v-html="postType.getRichDescription(entry)"></div>
    </div>
  `
});