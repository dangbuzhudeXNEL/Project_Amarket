/* shared.js — POC 通用工具函数，所有页面引入 */

(function (global) {
  'use strict';

  /**
   * fetch JSON 数据，统一错误处理。
   * 返回 Promise<data> 或 throw Error。
   *
   * M3b 接 API 时，调用方把 url 从 '/assets/data/X.json' 换成 '/api/X' 即可。
   */
  async function fetchJSON(url) {
    const res = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText} loading ${url}`);
    return res.json();
  }

  /** 格式化数字：1234.5 → '1,234.50' */
  function formatNumber(n, digits = 2) {
    if (n == null || isNaN(n)) return '-';
    return Number(n).toLocaleString('zh-CN', {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }

  /** 格式化涨跌幅：3.2 → '+3.20%'（带正负号 + 颜色 class） */
  function formatChangePct(pct) {
    if (pct == null || isNaN(pct)) return { text: '-', cls: 'num-neutral' };
    const sign = pct >= 0 ? '+' : '';
    return {
      text: `${sign}${pct.toFixed(2)}%`,
      cls: pct > 0 ? 'num-up' : pct < 0 ? 'num-down' : 'num-neutral',
    };
  }

  /** ISO 时间 → '2026-06-24 13:42:15' */
  function formatDateTime(iso) {
    if (!iso) return '-';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return iso;
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
           `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }

  /** ISO 时间 → '13:42' */
  function formatTime(iso) {
    if (!iso) return '-';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return '-';
    const pad = (n) => String(n).padStart(2, '0');
    return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  /** ISO 时间 → '14分钟前' / '2小时前' / '昨天 13:42' */
  function timeAgo(iso) {
    if (!iso) return '-';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return '-';
    const seconds = Math.floor((Date.now() - d.getTime()) / 1000);
    if (seconds < 60) return `${seconds}秒前`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}分钟前`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}小时前`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}天前`;
    return formatDateTime(iso);
  }

  /** 重要性分数 → ★ 字符串 */
  function stars(score) {
    if (!score) return '';
    const n = Math.max(0, Math.min(5, Math.round(score)));
    return '★'.repeat(n) + '☆'.repeat(5 - n);
  }

  /** 情绪 → CSS class */
  function sentimentClass(sentiment) {
    const map = {
      '强利多': 'sent-strong-bull',
      '利多': 'sent-bull',
      '中性': 'sent-neutral',
      '利空': 'sent-bear',
      '强利空': 'sent-strong-bear',
    };
    return map[sentiment] || 'sent-neutral';
  }

  /** alert level → tag class */
  function alertTagClass(level) {
    return level ? `tag tag-${level.toLowerCase()}` : 'tag';
  }

  /** 显示页面顶部错误 banner */
  function showBanner(msg, type = 'error') {
    let el = document.getElementById('global-banner');
    if (!el) {
      el = document.createElement('div');
      el.id = 'global-banner';
      el.className = `banner banner-${type}`;
      const main = document.querySelector('.page-shell') || document.body;
      main.insertBefore(el, main.firstChild);
    } else {
      el.className = `banner banner-${type}`;
    }
    el.textContent = msg;
  }

  /** URL ?id=X 取 query 参数 */
  function getQueryParam(name) {
    return new URLSearchParams(location.search).get(name);
  }

  /** 时钟（每秒 tick），返回停止函数 */
  function startClock(targetEl) {
    function update() {
      if (!targetEl) return;
      const d = new Date();
      const pad = (n) => String(n).padStart(2, '0');
      targetEl.textContent = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
    }
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }

  /** 桌面宽度检测，<1280 显示警告 banner（不强制阻止） */
  function checkViewport() {
    if (window.innerWidth < 1280) {
      showBanner('POC 为桌面优先版，建议宽度 ≥ 1280px', 'warn');
    }
  }

  /**
   * 自动刷新工具（M3b polling）。
   * @param {number} intervalMs - 间隔毫秒
   * @param {Function} fn - 每 tick 调用（应为 async；忽略返回值；异常会被吞掉但 console.warn）
   * @returns {{stop: () => void}} 控制句柄
   */
  function startAutoRefresh(intervalMs, fn) {
    let stopped = false;
    let timer = null;
    async function tick() {
      if (stopped) return;
      try { await fn(); } catch (e) { console.warn('[autorefresh]', e); }
      if (!stopped) timer = setTimeout(tick, intervalMs);
    }
    timer = setTimeout(tick, intervalMs);
    return { stop() { stopped = true; if (timer) clearTimeout(timer); } };
  }

  const POLLING_LS_KEY = 'amarket.polling.enabled';

  /** 读 polling 开关（持久到 localStorage，默认 false）。 */
  function isPollingEnabled() {
    try { return localStorage.getItem(POLLING_LS_KEY) === '1'; }
    catch { return false; }
  }

  /** 写 polling 开关；返回新值。 */
  function setPollingEnabled(enabled) {
    try {
      localStorage.setItem(POLLING_LS_KEY, enabled ? '1' : '0');
    } catch { /* ignore */ }
    return enabled;
  }

  global.Amarket = {
    fetchJSON, formatNumber, formatChangePct, formatDateTime, formatTime,
    timeAgo, stars, sentimentClass, alertTagClass, showBanner,
    getQueryParam, startClock, checkViewport,
    startAutoRefresh, isPollingEnabled, setPollingEnabled,
  };
})(window);
