/* sectors.js — 板块热力图全屏页 */

function sectorsPage() {
  const A = window.Amarket;
  let chart = null;
  let sectorsData = null;
  let allNews = [];

  return {
    sectorsList: [],
    selectedSector: null,
    relatedNews: [],
    window: '1d',
    dimension: 'change',
    windows: [
      { key: '1h', label: '1h' },
      { key: '4h', label: '4h' },
      { key: '1d', label: '1d' },
    ],
    get windowLabel() {
      return this.windows.find((w) => w.key === this.window)?.label || '1d';
    },
    get dimensionLabel() {
      return { change: '涨跌幅', news: '新闻热度', weight: '市值权重' }[this.dimension];
    },
    fmt: {
      pctText: (p) => A.formatChangePct(p).text,
      pctClass: (p) => A.formatChangePct(p).cls,
      timeAgo: A.timeAgo,
      stars: A.stars,
      sentClass: A.sentimentClass,
      alertClass: A.alertTagClass,
    },
    async init() {
      A.checkViewport();
      try {
        [sectorsData, allNews] = await Promise.all([
          A.fetchJSON('assets/data/sectors.json'),
          A.fetchJSON('assets/data/news.json'),
        ]);
        this.sectorsList = sectorsData.sectors;
        this.$nextTick(() => this.renderChart());
        this.$watch('dimension', () => this.renderChart());
      } catch (e) {
        A.showBanner(`数据加载失败：${e.message}`);
      }
    },
    renderChart() {
      const el = document.getElementById('big-heatmap');
      if (!el) return;
      if (!chart) chart = echarts.init(el, null, { renderer: 'canvas' });

      const items = this.sectorsList.map((s) => {
        let value, color, opacity;
        if (this.dimension === 'change') {
          value = Math.max(0.3, Math.abs(s.change_pct));
          color = s.change_pct >= 0 ? '#00d97e' : '#ff4d5e';
          opacity = Math.min(1, 0.4 + Math.abs(s.change_pct) / 4);
        } else if (this.dimension === 'news') {
          value = Math.max(1, s.news_count_24h);
          color = '#00c2ff';
          opacity = Math.min(1, 0.35 + s.news_count_24h / 30);
        } else {
          value = s.market_cap_weight * 100;
          color = '#b026ff';
          opacity = 0.4 + s.market_cap_weight * 3;
        }
        const labelText = this.dimension === 'change'
          ? `${s.name}\n${s.change_pct >= 0 ? '+' : ''}${s.change_pct}%`
          : this.dimension === 'news'
          ? `${s.name}\n${s.news_count_24h} 条`
          : `${s.name}\n${(s.market_cap_weight * 100).toFixed(1)}%`;
        return {
          name: labelText,
          value,
          sectorName: s.name,
          itemStyle: { color, opacity, borderRadius: 6 },
        };
      });

      chart.setOption({
        backgroundColor: 'transparent',
        tooltip: {
          formatter: (info) => {
            const sec = this.sectorsList.find((s) => s.name === info.data.sectorName);
            if (!sec) return '';
            return `
              <div style="font-family:Inter,sans-serif;padding:4px">
                <div style="font-weight:600;font-size:14px;margin-bottom:6px">${sec.name}</div>
                <div style="font-size:12px;color:#9da0a8">涨跌 <span style="color:${sec.change_pct>=0?'#00d97e':'#ff4d5e'};font-weight:600">${sec.change_pct>=0?'+':''}${sec.change_pct}%</span></div>
                <div style="font-size:12px;color:#9da0a8">新闻 <span style="color:#fff;font-weight:600">${sec.news_count_24h} 条</span></div>
                <div style="font-size:12px;color:#9da0a8">市值权重 <span style="color:#fff;font-weight:600">${(sec.market_cap_weight*100).toFixed(1)}%</span></div>
              </div>
            `;
          },
          backgroundColor: 'rgba(20,22,28,0.95)',
          borderColor: '#2a2d33',
          textStyle: { color: '#f0f1f3' },
        },
        series: [{
          type: 'treemap',
          data: items,
          roam: false,
          nodeClick: false,
          breadcrumb: { show: false },
          label: {
            show: true,
            color: '#fff',
            fontSize: 14,
            fontWeight: 600,
            textShadowColor: 'rgba(0,0,0,0.5)',
            textShadowBlur: 4,
          },
          itemStyle: { borderColor: '#07080a', borderWidth: 3, gapWidth: 3 },
        }],
      });

      chart.off('click');
      chart.on('click', (params) => {
        if (params.data?.sectorName) this.selectSector(params.data.sectorName);
      });
      window.addEventListener('resize', () => chart.resize());
    },
    selectSector(name) {
      this.selectedSector = this.sectorsList.find((s) => s.name === name);
      if (!this.selectedSector) {
        this.relatedNews = [];
        return;
      }
      // 过滤 news.json 中 related_sectors 包含该板块名的新闻
      this.relatedNews = allNews
        .filter((n) => (n.related_sectors || []).some((sec) => sec.name === name))
        .sort((a, b) => new Date(b.published_at) - new Date(a.published_at))
        .slice(0, 30);
    },
  };
}
