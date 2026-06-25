/* news.js — 新闻流页 */

function newsPage() {
  const A = window.Amarket;
  return {
    news: [],
    sourceOptions: [],
    categoryOptions: [],
    filter: {
      sources: [], categories: [], sentiments: [],
      minImportance: 0, search: '', sortBy: 'time',
    },
    fmt: {
      dateTime: A.formatDateTime,
      stars: A.stars,
      sentClass: A.sentimentClass,
      alertClass: A.alertTagClass,
    },
    async init() {
      A.checkViewport();
      try {
        const resp = await A.fetchJSON('/api/news?limit=200');
        this.news = resp.items || [];
        this.sourceOptions = Array.from(new Set(this.news.map((n) => n.source).filter(Boolean))).sort();
        this.categoryOptions = Array.from(new Set(this.news.map((n) => n.primary_category).filter(Boolean))).sort();
        if (A.isPollingEnabled()) this._startPolling();
        document.addEventListener('amarket:polling-changed', (e) => {
          if (e.detail.enabled) this._startPolling();
          else this._stopPolling();
        });
      } catch (e) {
        A.showBanner(`数据加载失败：${e.message}`);
      }
    },
    _polling: null,
    _startPolling() {
      if (this._polling) return;
      this._polling = A.startAutoRefresh(30000, () => this.init());
    },
    _stopPolling() {
      if (this._polling) { this._polling.stop(); this._polling = null; }
    },
    get hasActiveFilters() {
      return this.filter.sources.length || this.filter.categories.length ||
             this.filter.sentiments.length || this.filter.minImportance ||
             this.filter.search;
    },
    get filteredNews() {
      return this.news.filter((n) => {
        if (this.filter.sources.length && !this.filter.sources.includes(n.source)) return false;
        if (this.filter.categories.length && !this.filter.categories.includes(n.primary_category)) return false;
        if (this.filter.sentiments.length && !this.filter.sentiments.includes(n.sentiment)) return false;
        if (this.filter.minImportance && (n.importance || 0) < this.filter.minImportance) return false;
        if (this.filter.search) {
          const q = this.filter.search.toLowerCase();
          if (!(n.title || '').toLowerCase().includes(q) &&
              !(n.summary || '').toLowerCase().includes(q)) return false;
        }
        return true;
      });
    },
    get sortedNews() {
      const arr = this.filteredNews.slice();
      if (this.filter.sortBy === 'importance') {
        arr.sort((a, b) => (b.importance || 0) - (a.importance || 0));
      } else if (this.filter.sortBy === 'sentiment') {
        const order = { '强利空': -2, '利空': -1, '中性': 0, '利多': 1, '强利多': 2 };
        arr.sort((a, b) => (order[b.sentiment] ?? 0) - (order[a.sentiment] ?? 0));
      } else {
        arr.sort((a, b) => new Date(b.published_at) - new Date(a.published_at));
      }
      return arr;
    },
    resetFilter() {
      this.filter = {
        sources: [], categories: [], sentiments: [],
        minImportance: 0, search: '', sortBy: 'time',
      };
    },
  };
}
