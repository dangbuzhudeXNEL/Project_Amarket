/* params.js — 赛博朋克参数控制台 */

function paramsPage() {
  const A = window.Amarket;
  return {
    params: [],
    groups: [],
    async init() {
      // 时钟
      const clockEl = document.getElementById('clock');
      if (clockEl) A.startClock(clockEl);
      // UID 模拟（hex random）
      const uidEl = document.getElementById('uid');
      if (uidEl) {
        const uid = Array.from({ length: 8 }, () => Math.floor(Math.random() * 16).toString(16).toUpperCase()).join('');
        uidEl.textContent = uid;
      }
      try {
        this.params = await A.fetchJSON('assets/data/params.json');
        this.groups = this.groupParams(this.params);
      } catch (e) {
        document.querySelector('.cyber-shell').innerHTML = `
          <div style="padding:40px;color:var(--neon-magenta);text-align:center">
            <h2>SYS.ERROR // DATA.LOAD_FAILED</h2>
            <p>${e.message}</p>
            <p style="font-size:12px;opacity:0.6">run: <code>uv run python scripts/dump_poc_fixtures.py</code></p>
          </div>
        `;
      }
    },
    groupParams(params) {
      const groupMap = {
        sources: { name: 'DATA_SOURCES', note: 'news source toggles + poll rates', items: [] },
        news: { name: 'NEWS_COLLECTOR', note: 'fetch + batch behavior', items: [] },
        keywords: { name: 'KEYWORDS', note: 'scoring weights', items: [] },
        ai: { name: 'AI_ENGINE', note: 'provider + timeouts', items: [] },
        alerts: { name: 'ALERTS', note: 'P0-P3 thresholds + cooldown', items: [] },
        scheduler: { name: 'SCHEDULER', note: 'cron + intervals', items: [] },
      };
      for (const p of params) {
        const prefix = p.key.split('.')[0];
        if (groupMap[prefix]) {
          groupMap[prefix].items.push(p);
        } else {
          if (!groupMap.misc) groupMap.misc = { name: 'MISC', note: '未分类', items: [] };
          groupMap.misc.items.push(p);
        }
      }
      return Object.values(groupMap).filter((g) => g.items.length > 0);
    },
    formatValue(v) {
      if (typeof v === 'boolean') return v ? 'TRUE' : 'FALSE';
      if (v === null) return 'NULL';
      if (typeof v === 'string') return `"${v}"`;
      return String(v);
    },
    formatValueClass(v) {
      if (v === true) return 'bool-true';
      if (v === false) return 'bool-false';
      return '';
    },
    showToast(msg) {
      const el = document.getElementById('cyber-toast');
      if (!el) return;
      el.textContent = msg;
      el.classList.add('show');
      clearTimeout(el._timeout);
      el._timeout = setTimeout(() => el.classList.remove('show'), 2200);
    },
  };
}
