export default Vue.component('transactions', {
  props: ['entries'],
  computed: {
    totals() {
      const amounts = this.entries.map(e => Number(e.data.amount));
      const incomes = amounts.filter(a => a >= 0);
      const expenses = amounts.filter(a => a < 0);
      return {
        income: incomes.reduce((a, b) => a + b, 0),
        incomeCount: incomes.length,
        expenses: expenses.reduce((a, b) => a + b, 0),
        expenseCount: expenses.length,
      }
    },
  },
  methods: {
    roundCurrency(num, roundDown=false) {
      if(roundDown) {
        return Math.floor(num * 100) / 100;
      }
      return Math.round(num * 100) / 100;
    },
    formatCurrency(num, currency='€') {
      const amount = Number(num);
      const decimalsToShow = (Math.abs(amount) < 20 && amount !== 0) ? 2 : 0;
      let formattedAmount = this.roundCurrency(amount)
        .toLocaleString('en-GB', {
          minimumFractionDigits: decimalsToShow,
          maximumFractionDigits: decimalsToShow,
        });

      if(formattedAmount === '-0.00'){
        formattedAmount = '0.00';
      }
      else if(formattedAmount === '-0'){
        formattedAmount = '0';
      }
      return (currency ? `${formattedAmount} ${currency}` : formattedAmount).replace('-', '−');
    }
  },
  template: `
    <details class="transactions">
      <summary>
        <div class="total-income">
          <strong class="amount">+{{ formatCurrency(totals.income) }}</strong>
          <small class="transaction-count">{{ totals.incomeCount || 'No' }} transactions</small>
        </div>
        <div class="total-expenses">
          <strong class="amount">{{ formatCurrency(totals.expenses) }}</strong>
          <small class="transaction-count">{{ totals.expenseCount || 'No' }} transactions</small>
        </div>
      </summary>
      <div class="transaction" v-for="entry in entries">
        <img src="/images/n26.png">
        <div class="details">
          <span class="other-party">{{ entry.data.otherParty }}</span>
          <small v-if="entry.data.description" class="description">{{ entry.data.description }}</small>
        </div>
        <span class="amount">{{ formatCurrency(entry.data.amount) }}</span>
      </div>
    </details>
  `
});
