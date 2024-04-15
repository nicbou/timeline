import config from './../../config.js';

export default Vue.component('transaction-entry', {
  props: ['entry'],
  computed: {
    entryIcon() {
      return `/images/${this.entry.data.account.toLowerCase()}.png`;
    },
    amount() {
      const amount = Math.round(Number(this.entry.data.amount));
      let formattedAmount = (Math.round(amount * 100) / 100).toLocaleString('en-GB');

      if(formattedAmount === '-0.00'){
        formattedAmount = '0.00';
      }
      else if(formattedAmount === '-0'){
        formattedAmount = '0';
      }
      return `${formattedAmount} €`.replace('-', '−');
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