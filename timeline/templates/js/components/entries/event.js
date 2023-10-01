import config from './../../config.js';

export default Vue.component('event-entry', {
  props: ['entry'],
  data() {
    return {
      expanded: false,
    }
  },
  computed: {
    currentDate() {
      return moment(this.$route.query.date, 'YYYY-MM-DD', true);
    },
    isAllDay() {
      return (
        this.dateStart <= this.currentDate.startOf('day')
        && this.dateEnd
        && this.dateEnd >= this.currentDate.endOf('day').milliseconds(0)
      );
    },
    startsEarlier() {
      return this.dateStart < this.currentDate.startOf('day');
    },
    endsLater() {
      return this.dateEnd && this.dateEnd > this.currentDate.endOf('day').milliseconds(0);
    },
    dateStart() {
      return moment(this.entry.date_start);
    },
    dateEnd() {
      return this.entry.date_end ? moment(this.entry.date_end) : null;
    },
    dateEndPrint() {
      // Adds the missing second to the end date
      return moment(this.dateEnd).add(1, 'seconds');
    },
    description() {
      return (this.entry.data.description || '').trim().replaceAll('<br><br>', '<br>').replaceAll('\n', '<br>');
    }
  },
  template: `
    <article class="entry event" @click="expanded = !expanded" :class="{'expanded': expanded, 'starts-earlier': startsEarlier, 'ends-later': endsLater}">
      <i class="fa-regular fa-calendar"></i>
      <time v-if="!isAllDay && !startsEarlier">{{ dateStart.format('H:mm') }}</time>
      <time v-if="!isAllDay && startsEarlier">&hellip;{{ dateEndPrint.format('H:mm') }}</time>
      <time class="all-day" v-if="isAllDay">All day</time>
      <div class="summary">{{ entry.data.summary.replaceAll('\\n', ', ') }}</div>
      <div class="description" v-if="description" v-html="description"></div>
    </article>
  `
});