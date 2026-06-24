/* index.js — Dashboard 首页 Alpine x-data */

function indexPage() {
  const A = window.Amarket;
  return {
    data: {},
    marketStatus: { indexes: [] },
    news: [],
    allAlerts: [],
    importantAlerts: [],
    topSectors: [],
    sectorsUp: 0,
    reports: {},
    dataTime: '--:--',
    kindLabels: {
      premarket: '盘前', morning: '早盘', noon: '午间',
      afternoon: '尾盘', close: '收盘', evening: '晚间',
    },
    filter: { category: '', sentiment: '', minImportance: 0 },
    categories: [],
    fmt: {
      num: (n) => A.formatNumber(n),
      pctText: (p) => A.formatChangePct(p).text,
      pctClass: (p) => A.formatChangePct(p).cls,
      time: A.formatTime,
      timeAgo: A.timeAgo,
      stars: A.stars,
      sentClass: A.sentimentClass,
      alertClass: A.alertTagClass,
    },
    async init() {
      A.checkViewport();
      try {
        const [dashboard, news, alerts, sectors] = await Promise.all([
          A.fetchJSON('assets/data/dashboard.json'),
          A.fetchJSON('assets/data/news.json'),
          A.fetchJSON('assets/data/alerts.json'),
          A.fetchJSON('assets/data/sectors.json'),
        ]);
        this.data = dashboard;
        this.marketStatus = dashboard.market_status || { indexes: [] };
        this.reports = dashboard.today_reports || {};
        this.news = news;
        this.allAlerts = alerts;
        this.importantAlerts = alerts.filter((a) => a.level === 'P0' || a.level === 'P1');
        this.topSectors = sectors.sectors.slice().sort((a, b) => b.news_count_24h - a.news_count_24h);
        this.sectorsUp = sectors.sectors.filter((s) => (s.change_pct ?? 0) >= 0).length;
        this.dataTime = A.formatTime(dashboard.as_of) || '--:--';
        const catSet = new Set(news.map((n) => n.primary_category).filter(Boolean));
        this.categories = Array.from(catSet).sort();
        this.$nextTick(() => this.renderHeatmap(sectors));
      } catch (e) {
        A.showBanner(`数据加载失败：${e.message}。请跑 \`uv run python scripts/dump_poc_fixtures.py\``);
      }
    },
    get filteredNews() {
      return this.news.filter((n) => {
        if (this.filter.category && n.primary_category !== this.filter.category) return false;
        if (this.filter.sentiment && n.sentiment !== this.filter.sentiment) return false;
        if (this.filter.minImportance && (n.importance || 0) < this.filter.minImportance) return false;
        return true;
      });
    },
    resetFilter() {
      this.filter = { category: '', sentiment: '', minImportance: 0 };
    },
    renderHeatmap(sectorsData) {
      const el = document.getElementById('sector-heatmap');
      if (!el) return;
      const chart = echarts.init(el, null, { renderer: 'canvas' });
      const items = sectorsData.sectors.map((s) => ({
        name: `${s.name}\n${s.change_pct >= 0 ? '+' : ''}${s.change_pct}%`,
        value: Math.abs(s.change_pct) + 1,
        itemStyle: {
          color: s.change_pct >= 0 ? '#00d97e' : '#ff4d5e',
          opacity: Math.min(1, 0.45 + Math.abs(s.change_pct) / 4),
          borderRadius: 4,
        },
      }));
      chart.setOption({
        backgroundColor: 'transparent',
        series: [{
          type: 'treemap',
          data: items,
          roam: false,
          nodeClick: false,
          breadcrumb: { show: false },
          label: { show: true, color: '#fff', fontSize: 12, fontWeight: 600 },
          itemStyle: { borderColor: '#07080a', borderWidth: 3, gapWidth: 3 },
        }],
      });
      window.addEventListener('resize', () => chart.resize());
    },
  };
}
