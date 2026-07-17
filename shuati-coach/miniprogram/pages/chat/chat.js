// pages/chat/chat.js · 问教练（转发到后端 /api/chat → Hermes Agent）
const app = getApp();

Page({
  data: {
    messages: [],   // { role: 'user' | 'assistant', content: string }
    input: '',
    loading: false
  },

  onInput(e) {
    this.setData({ input: e.detail.value });
  },

  async send() {
    const text = (this.data.input || '').trim();
    if (!text || this.data.loading) return;

    const history = this.data.messages.concat([{ role: 'user', content: text }]);
    this.setData({ messages: history, input: '', loading: true });

    try {
      const res = await app.request('/api/chat', 'POST', {
        system: '你是「专属刷题教练」里的智能答疑助手，用通俗中文回答用户关于题目、知识点、复习方法与备考规划的问题，必要时给出具体例子。',
        messages: history.map(m => ({ role: m.role, content: m.content }))
      });
      const reply = (res && res.reply) ? res.reply : '（暂无回复）';
      this.setData({
        messages: this.data.messages.concat([{ role: 'assistant', content: reply }]),
        loading: false
      });
    } catch (e) {
      this.setData({
        messages: this.data.messages.concat([{ role: 'assistant', content: '网络开小差了，稍后再试～' }]),
        loading: false
      });
      wx.showToast({ title: '请求失败', icon: 'none' });
    }
  }
});
