export default Vue.component('transactions', {
  props: ['currentDate', 'entries', 'finances'],
  data() {
    return {
      showTransactions: false
    }
  },
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
    expenseEntries(){
      return this.entries.filter(e => Number(e.data.amount) < 0);
    },
    incomeEntries(){
      return this.entries.filter(e => Number(e.data.amount) >= 0);
    },
  },
  methods: {
    entryIcon(entry) {
      return `/images/${entry.data.account.toLowerCase()}.png`;
    },
    roundCurrency(num, roundDown=false) {
      if(roundDown) {
        return Math.floor(num * 100) / 100;
      }
      return Math.round(num * 100) / 100;
    },
    formatCurrency(num, currency='€') {
      const amount = Math.round(Number(num));
      let formattedAmount = this.roundCurrency(amount).toLocaleString('en-GB');

      if(formattedAmount === '-0.00'){
        formattedAmount = '0.00';
      }
      else if(formattedAmount === '-0'){
        formattedAmount = '0';
      }
      return (currency ? `${formattedAmount} ${currency}` : formattedAmount).replace('-', '−');
    },
    graphPathPoint(graphWidth, graphHeight) {
      const datesToShow = [];
      for(let i=-14; i<=14; i++){  // Show balance 5 days in each direction
        const dateToShow = new Date(this.currentDate);
        dateToShow.setDate(dateToShow.getDate() + i);
        datesToShow.push(dateToShow.toISOString().split('T')[0]);
      }

      let total = 0;
      const values = datesToShow.map(d => {
        total += Number(this.finances[d]) || 0;
        return total;
      });
      const minValue = Math.min(...values);
      const maxValue = Math.max(...values);

      return values.map((value, index) => {
        const x = index / datesToShow.length * graphWidth;
        const y = graphHeight - ((value - minValue) / (maxValue - minValue) * graphHeight);
        if(index === 0){
          return `M ${x} ${y}`;
        }
        return `L ${x} ${y}`;
      }).join(' ') // Turn balance into polyline point
    }
  },
  template: `
    <div class="transactions" @click="showTransactions = !showTransactions">
      <svg viewBox="0 -10 380 70" class="chart">
        <path
          fill="transparent"
          vector-effect="non-scaling-stroke"
          :d="graphPathPoint(380, 50)"/>
        <line
          stroke-width="1px"
          vector-effect="non-scaling-stroke"
          x1="190"
          x2="190"
          y1="0"
          y2="100"/>
      </svg>

      <div class="income">
        <h3>Income</h3>
        <strong class="total-amount">+{{ formatCurrency(totals.income) }}</strong>
        <ul v-if="entries.length && showTransactions" class="income">
          <li v-for="entry in incomeEntries">
            <img :src="entryIcon(entry)">
            <div class="details">
              <span class="other-party">{{ entry.data.otherParty }}</span>
              <small v-if="entry.data.description" class="description">{{ entry.data.description }}</small>
            </div>
            <span class="amount">{{ formatCurrency(entry.data.amount) }}</span>
          </li>
        </ul>
      </div>
      <div class="expenses">
        <h3>Expenses</h3>
        <strong class="total-amount">{{ formatCurrency(totals.expenses) }}</strong>
        <ul v-if="entries.length && showTransactions" class="expenses">
          <li v-for="entry in expenseEntries">
            <img :src="entryIcon(entry)">
            <div class="details">
              <span class="other-party">{{ entry.data.otherParty }}</span>
              <small v-if="entry.data.description" class="description">{{ entry.data.description }}</small>
            </div>
            <span class="amount">{{ formatCurrency(entry.data.amount) }}</span>
          </li>
        </ul>
      </div>
    </div>
  `
});
