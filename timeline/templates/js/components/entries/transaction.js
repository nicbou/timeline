import TimelineEntryIcon from './entry-icon.js';

export default Vue.component('transaction-entry', {
  props: ['entry'],
  computed: {
    isExpense: function(){
      return this.entry.entry_type === 'finance.expense';
    },
    transactionType: function(){
      return this.isExpense ? 'expense' : 'income';
    },
    amount: function(){
      let amount = this.entry.data.recipient.amount;
      if(this.isExpense) {
        amount = this.entry.data.sender.amount;
      }
      return Number(amount).toFixed(2);
    },
    otherCurrencyAmount: function(){
      let amount = this.entry.data.sender.amount;
      if(this.isExpense) {
        amount = this.entry.data.recipient.amount;
      }
      return Number(amount).toFixed(2);
    },
    currency: function(){
      let currency = this.entry.data.recipient.currency;
      if(this.isExpense) {
        currency = this.entry.data.sender.currency;
      }
      return currency === 'EUR' ? '€' : currency;
    },
    otherCurrency: function(){
      let currency = this.entry.data.sender.currency;
      if(this.isExpense) {
        currency = this.entry.data.recipient.currency;
      }
      return currency === 'EUR' ? '€' : currency;
    },
    otherPartyName: function(){
      if(this.isExpense) {
        return this.entry.data.recipient.name;
      }
      return this.entry.data.sender.name;
    },
  },
  template: `
    <div class="transaction">
      <entry-icon icon-class="fas fa-piggy-bank" :entry="entry"></entry-icon>
      <div class="meta">{{ otherPartyName }}</div>
      <div class="content">
        <strong>{{ amount }}{{ currency }}</strong> {{ transactionType }}
        <span v-if="otherCurrency !== currency">({{ otherCurrencyAmount }}{{ otherCurrency }})</span>
        <small v-if="entry.description">{{ entry.description }}</small>
      </div>
    </div>
  `
});