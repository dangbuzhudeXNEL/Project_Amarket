/* news-detail.js — 单条新闻详情 */

function newsDetailPage() {
  const A = window.Amarket;
  return {
    news: null,
    error: '',
    fmt: {
      dateTime: A.formatDateTime,
      stars: A.stars,
      sentClass: A.sentimentClass,
      alertClass: A.alertTagClass,
    },
    async init() {
      A.checkViewport();
      const id = A.getQueryParam('id');
      if (!id) {
        this.error = '请从新闻流页面进入（缺少 id 参数）';
        return;
      }
      try {
        this.news = await A.fetchJSON(`assets/data/news-detail-${id}.json`);
        document.title = `Amarket — ${this.news.title}`;
      } catch (e) {
        if (e.message.includes('404')) {
          this.error = `新闻 #${id} 不存在（M3a 只 dump 了 5 条详情样本，完整 130 条 M3b 接 API 后可看）`;
        } else {
          this.error = `加载失败：${e.message}`;
        }
      }
    },
  };
}
