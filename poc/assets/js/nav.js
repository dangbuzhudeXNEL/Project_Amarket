/* nav.js — 顶部 nav 自动注入。OKX 5 页用，params.html 不引用此文件。 */

(function () {
  'use strict';

  const NAV_ITEMS = [
    { href: 'index.html', label: '首页', match: ['index.html', '/'] },
    { href: 'news.html', label: '新闻流', match: ['news.html', 'news-detail.html'] },
    { href: 'sectors.html', label: '板块', match: ['sectors.html'] },
    { href: 'reports.html', label: '日报', match: ['reports.html'] },
    { href: 'params.html', label: '参数', match: ['params.html'], cyber: true },
  ];

  function isActive(item) {
    const path = location.pathname.split('/').pop() || 'index.html';
    return item.match.some((m) => path === m || (m === '/' && path === ''));
  }

  function render() {
    const mount = document.getElementById('topbar-mount');
    if (!mount) return;
    const itemsHtml = NAV_ITEMS.map((item) => {
      const cls = ['nav-link'];
      if (isActive(item)) cls.push('active');
      if (item.cyber) cls.push('cyber');
      return `<a href="${item.href}" class="${cls.join(' ')}">${item.label}</a>`;
    }).join('');
    mount.innerHTML = `
      <div class="topbar">
        <div class="logo">Amarket</div>
        <div class="nav-items">${itemsHtml}</div>
        <div class="topbar-right">
          <button id="polling-toggle" class="live-indicator" type="button" aria-label="切换自动刷新">
            <span class="live-dot"></span>
            <span id="polling-label">LIVE</span>
          </button>
          <span id="topbar-clock">--:--:--</span>
        </div>
      </div>
    `;
    const clockEl = document.getElementById('topbar-clock');
    if (clockEl && window.Amarket) window.Amarket.startClock(clockEl);

    const toggleBtn = document.getElementById('polling-toggle');
    const labelEl = document.getElementById('polling-label');
    if (toggleBtn && window.Amarket) {
      const sync = () => {
        const on = window.Amarket.isPollingEnabled();
        toggleBtn.classList.toggle('on', on);
        toggleBtn.classList.toggle('off', !on);
        if (labelEl) labelEl.textContent = on ? 'LIVE' : 'PAUSED';
      };
      sync();
      toggleBtn.addEventListener('click', () => {
        const next = !window.Amarket.isPollingEnabled();
        window.Amarket.setPollingEnabled(next);
        sync();
        // 广播一次自定义事件，每页 init 里监听决定是否重启 polling
        document.dispatchEvent(new CustomEvent('amarket:polling-changed', { detail: { enabled: next } }));
      });
    }
  }

  document.addEventListener('DOMContentLoaded', render);
})();
