import { hasGeolocation } from './../utils/entries.js';

export const filters = {
  blog: {
    displayName: 'blog post',
    displayNamePlural: 'blog posts',
    iconClass: 'fas fa-rss',
    filterFunction: (entry) => entry.entry_type === 'social.blog',
  },
  browse: {
    displayName: 'page view',
    displayNamePlural: 'page views',
    iconClass: 'fas fa-globe-americas',
    filterFunction: (entry) => entry.entry_type === 'browse',
  },
  commit: {
    displayName: 'commit',
    displayNamePlural: 'commits',
    iconClass: 'fab fa-git-square',
    filterFunction: (entry) => entry.entry_type === 'commit',
  },
  file: {
    displayName: 'file',
    displayNamePlural: 'files',
    iconClass: 'fas fa-file',
    filterFunction: (entry) => entry.entry_type === 'file',
  },
  image: {
    displayName: 'image',
    displayNamePlural: 'images',
    iconClass: 'fas fa-image',
    filterFunction: (entry) => entry.entry_type === 'image',
  },
  hackerNews: {
    displayName: 'Hacker News entry',
    displayNamePlural: 'Hacker News entries',
    iconClass: 'fab fa-y-combinator',
    filterFunction: (entry) => entry.entry_type === 'social.hackernews',
  },
  journal: {
    displayName: 'journal entry',
    displayNamePlural: 'journal entries',
    iconClass: 'fas fa-pen-square',
    filterFunction: (entry) => entry.entry_type === 'journal',
  },
  location: {
    displayName: 'location ping',
    displayNamePlural: 'location pings',
    iconClass: 'fas fa-map-marker-alt',
    filterFunction: hasGeolocation,
  },
  message: {
    displayName: 'message',
    displayNamePlural: 'messages',
    iconClass: 'fas fa-comments',
    filterFunction: (entry) => entry.entry_type === 'message',
  },
  reddit: {
    displayName: 'reddit entry',
    displayNamePlural: 'reddit entries',
    iconClass: 'fab fa-reddit',
    filterFunction: (entry) => entry.entry_type === 'social.reddit.',
  },
  search: {
    displayName: 'search',
    displayNamePlural: 'searches',
    iconClass: 'fas fa-search',
    filterFunction: (entry) => entry.entry_type === 'search',
  },
  transaction: {
    displayName: 'transaction',
    displayNamePlural: 'transactions',
    iconClass: 'fas fa-piggy-bank',
    filterFunction: (entry) => entry.entry_type === 'transaction',
  },
  twitter: {
    displayName: 'tweet',
    displayNamePlural: 'tweets',
    iconClass: 'fab fa-twitter',
    filterFunction: (entry) => entry.entry_type === 'social.twitter.',
  },
  video: {
    displayName: 'video',
    displayNamePlural: 'videos',
    iconClass: 'fas fa-video',
    filterFunction: (entry) => entry.entry_type === 'video',
  },
}