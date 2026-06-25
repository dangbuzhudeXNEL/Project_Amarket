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
        this.news = await A.fetchJSON(`/api/news/${id}`);
        document.title = `Amarket — ${this.news.title}`;
      } catch (e) {
        if (e.message.includes('404')) {
          this.error = `新闻 #${id} 不存在或已被删除`;
        } else {
          this.error = `加载失败：${e.message}`;
        }
      }
    },
  };
}
