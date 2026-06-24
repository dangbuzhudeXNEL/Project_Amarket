/* reports.js — 6 时段日报展示页 */

function reportsPage() {
  const A = window.Amarket;
  return {
    today: '',
    reportsByKind: {},
    current: '',
    kindOrder: ['premarket', 'morning', 'noon', 'afternoon', 'close', 'evening'],
    kindLabels: {
      premarket: '盘前', morning: '早盘', noon: '午间',
      afternoon: '尾盘', close: '收盘', evening: '晚间',
    },
    fmt: {
      dateTime: A.formatDateTime,
    },
    async init() {
      A.checkViewport();
      try {
        const data = await A.fetchJSON('assets/data/reports.json');
        this.today = data.today || '';
        this.reportsByKind = data.reports_by_kind || {};

        // URL ?kind=premarket 支持
        const urlKind = A.getQueryParam('kind');
        if (urlKind && this.reportsByKind[urlKind]) {
          this.current = urlKind;
        } else {
          // 默认选第一个有内容的
          this.current = this.kindOrder.find((k) => this.reportsByKind[k]) || '';
        }
      } catch (e) {
        A.showBanner(`数据加载失败：${e.message}`);
      }
    },
    get currentReport() {
      return this.current ? this.reportsByKind[this.current] : null;
    },
    get completedCount() {
      return Object.values(this.reportsByKind).filter(Boolean).length;
    },
    get renderedMarkdown() {
      if (!this.currentReport?.markdown) return '';
      try {
        return window.marked.parse(this.currentReport.markdown);
      } catch (e) {
        return `<pre>${this.currentReport.markdown}</pre>`;
      }
    },
  };
}
