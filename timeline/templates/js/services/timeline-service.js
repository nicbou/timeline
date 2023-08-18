import config from './../config.js';

export default class {
  static getEntries(date) {
    return fetch(`${config.domain}/entries/${date.toISOString().split('T')[0]}.json`)
      .then(response => response.ok ? response.json() : Promise.reject(response))
      .then(json => json.entries);
  }
}