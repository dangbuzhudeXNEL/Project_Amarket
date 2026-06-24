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
          <span class="live-indicator">
            <span class="live-dot"></span>
            LIVE
          </span>
          <span id="topbar-clock">--:--:--</span>
        </div>
      </div>
    `;
    const clockEl = document.getElementById('topbar-clock');
    if (clockEl && window.Amarket) window.Amarket.startClock(clockEl);
  }

  document.addEventListener('DOMContentLoaded', render);
})();
