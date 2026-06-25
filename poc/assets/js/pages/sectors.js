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
        const [sectorsResp, newsResp] = await Promise.all([
          A.fetchJSON(`/api/dashboard/sectors?window=${this.window}`),
          A.fetchJSON('/api/news?limit=200'),
        ]);
        sectorsData = sectorsResp;
        allNews = newsResp.items || [];
        this.sectorsList = sectorsData.sectors;
        this.$nextTick(() => this.renderChart());
        this.$watch('dimension', () => this.renderChart());
        // M3b — window 切换重新拉
        this.$watch('window', async () => {
          try {
            sectorsData = await A.fetchJSON(`/api/dashboard/sectors?window=${this.window}`);
            this.sectorsList = sectorsData.sectors;
            this.renderChart();
          } catch (e) { A.showBanner(`刷新失败：${e.message}`); }
        });
        // polling
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
    renderChart() {
      const el = document.getElementById('big-heatmap');
      if (!el) return;
      if (!chart) chart = echarts.init(el, null, { renderer: 'canvas' });

      const items = this.sectorsList.map((s) => {
        // M3b post-merge polish：change_pct 可能为 null（Phase 1 数据空时）→ 用中性灰 + "—"
        const cp = s.change_pct;
        const cpKnown = (cp !== null && cp !== undefined && !isNaN(cp));
        let value, color, opacity;
        if (this.dimension === 'change') {
          value = cpKnown ? Math.max(0.3, Math.abs(cp)) : 0.5;
          color = !cpKnown ? '#4a4d55' : (cp >= 0 ? '#00d97e' : '#ff4d5e');
          opacity = cpKnown ? Math.min(1, 0.4 + Math.abs(cp) / 4) : 0.55;
        } else if (this.dimension === 'news') {
          value = Math.max(1, s.news_count_24h);
          color = s.news_count_24h > 0 ? '#00c2ff' : '#4a4d55';
          opacity = Math.min(1, 0.35 + s.news_count_24h / 30);
        } else {
          const w = s.market_cap_weight || 0;
          value = w * 100 || 1;
          color = w > 0 ? '#b026ff' : '#4a4d55';
          opacity = 0.4 + w * 3;
        }
        const labelText = this.dimension === 'change'
          ? `${s.name}\n${cpKnown ? (cp >= 0 ? '+' : '') + cp + '%' : '—'}`
          : this.dimension === 'news'
          ? `${s.name}\n${s.news_count_24h} 条`
          : `${s.name}\n${((s.market_cap_weight || 0) * 100).toFixed(1)}%`;
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
            const cp = sec.change_pct;
            const cpKnown = (cp !== null && cp !== undefined && !isNaN(cp));
            const cpHtml = cpKnown
              ? `<span style="color:${cp >= 0 ? '#00d97e' : '#ff4d5e'};font-weight:600">${cp >= 0 ? '+' : ''}${cp}%</span>`
              : `<span style="color:#7a7d85;font-weight:600">— (M4 接调度后填充)</span>`;
            const mcw = sec.market_cap_weight;
            const mcwHtml = (mcw !== null && mcw !== undefined)
              ? `<span style="color:#fff;font-weight:600">${(mcw * 100).toFixed(1)}%</span>`
              : `<span style="color:#7a7d85">—</span>`;
            return `
              <div style="font-family:Inter,sans-serif;padding:4px">
                <div style="font-weight:600;font-size:14px;margin-bottom:6px">${sec.name}</div>
                <div style="font-size:12px;color:#9da0a8">涨跌 ${cpHtml}</div>
                <div style="font-size:12px;color:#9da0a8">新闻 <span style="color:#fff;font-weight:600">${sec.news_count_24h} 条</span></div>
                <div style="font-size:12px;color:#9da0a8">市值权重 ${mcwHtml}</div>
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
