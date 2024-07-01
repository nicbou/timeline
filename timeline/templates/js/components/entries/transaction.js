import config from './../../config.js';
import {formattedAmount} from './../../libs/currency.js';

export default Vue.component('transaction-entry', {
  props: ['entry'],
  computed: {
    entryIcon() {
      return `${config.siteUrl}/images/${this.entry.data.account.toLowerCase()}.png`;
    },
    amount() {
      return formattedAmount(this.entry.data.amount)
    },
  },
  template: `
    <article class="entry transaction">
      <img :src="entryIcon">
      <div class="description">
        <div class="summary">{{ entry.data.otherParty }}</div>
        <div class="description" v-if="entry.data.description">{{ entry.data.description }}</div>
      </div>
      <div class="amount">{{ amount }}</div>
    </article>
  `
});