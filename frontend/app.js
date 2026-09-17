/**
 * Samsung Stock AI Analyst - Vanilla JavaScript Application
 * Handles Chat, CRUD, Chart.js Visualization, Conversation History & Themes
 */

(function () {
  'use strict';

  // State Management
  const state = {
    currentConvId: null,
    conversations: [],
    dataPage: 0,
    dataLimit: 15,
    dataTotal: 0,
    sortOrder: 'desc',
    summary: null,
    stockChart: null,
    isGenerating: false,
    allChartData: []
  };

  // Utility: HTML Sanitizer for XSS prevention
  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Toast Notification System
  function showToast(message, type = 'info', duration = 3500) {
    const container = elements.toastContainer || document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    else if (type === 'error') icon = '⚠️';
    else if (type === 'warning') icon = '⚡';

    toast.innerHTML = `
      <span class="toast-icon">${icon}</span>
      <span class="toast-msg" style="flex:1;">${escapeHtml(message)}</span>
      <button class="toast-close" aria-label="닫기">&times;</button>
    `;

    const closeBtn = toast.querySelector('.toast-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => toast.remove());
    }

    container.appendChild(toast);

    setTimeout(() => {
      if (toast.parentElement) {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
      }
    }, duration);
  }

  const API = {
    async request(url, options = {}) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout
        options.signal = controller.signal;

        const res = await fetch(url, options);
        clearTimeout(timeoutId);

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: res.statusText }));
          const errorMsg = err.detail || `서버 에러 (${res.status})`;
          throw new Error(errorMsg);
        }
        return res.json();
      } catch (err) {
        if (!navigator.onLine) {
          showToast('오프라인 상태입니다. 네트워크 연결을 확인해주세요.', 'error');
          throw new Error('인터넷 연결이 오프라인 상태입니다.');
        }
        if (err.name === 'AbortError') {
          showToast('서버 응답 시간이 초과되었습니다. Render 기동(콜드스타트) 중일 수 있습니다.', 'warning');
          throw new Error('요청 시간 초과 (15초)');
        }
        const msg = err.message || '네트워크 연결에 실패했습니다.';
        if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
          showToast('백엔드 API 서버 연결 실패: Render 콜드스타트 또는 서버 주소를 확인해주세요.', 'error');
        }
        throw err;
      }
    },

    async get(endpoint) {
      return this.request(`${CONFIG.API_BASE_URL}${endpoint}`);
    },

    async post(endpoint, data) {
      return this.request(`${CONFIG.API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    },

    async put(endpoint, data) {
      return this.request(`${CONFIG.API_BASE_URL}${endpoint}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    },

    async delete(endpoint) {
      return this.request(`${CONFIG.API_BASE_URL}${endpoint}`, {
        method: 'DELETE'
      });
    }
  };

  // DOM Elements
  const elements = {
    // Theme
    themeToggleBtn: document.getElementById('themeToggleBtn'),
    
    // Tabs & Views
    navTabs: document.querySelectorAll('.nav-tab'),
    viewPanels: document.querySelectorAll('.view-panel'),
    
    // Cold start banner
    coldStartBanner: document.getElementById('coldStartBanner'),
    dismissBannerBtn: document.getElementById('dismissBannerBtn'),
    
    // Status
    apiStatusBadge: document.getElementById('apiStatusBadge'),
    apiStatusText: document.getElementById('apiStatusText'),
    swaggerDocsLink: document.getElementById('swaggerDocsLink'),
    storageModeLabel: document.getElementById('storageModeLabel'),
    
    // KPI summary
    kpiPeriod: document.getElementById('kpiPeriod'),
    kpiCount: document.getElementById('kpiCount'),
    kpiLatest: document.getElementById('kpiLatest'),
    kpiAvg: document.getElementById('kpiAvg'),
    kpiRange: document.getElementById('kpiRange'),
    kpiMin: document.getElementById('kpiMin'),
    kpiTrendBadge: document.getElementById('kpiTrendBadge'),
    
    // Chat
    chatMessages: document.getElementById('chatMessages'),
    welcomeBox: document.getElementById('welcomeBox'),
    chatForm: document.getElementById('chatForm'),
    chatInput: document.getElementById('chatInput'),
    sendBtn: document.getElementById('sendBtn'),
    newChatBtn: document.getElementById('newChatBtn'),
    conversationList: document.getElementById('conversationList'),
    promptChips: document.querySelectorAll('.chip-btn'),
    
    // Data CRUD
    dataTableBody: document.getElementById('dataTableBody'),
    openAddModalBtn: document.getElementById('openAddModalBtn'),
    refreshDataBtn: document.getElementById('refreshDataBtn'),
    sortOrderSelect: document.getElementById('sortOrderSelect'),
    prevPageBtn: document.getElementById('prevPageBtn'),
    nextPageBtn: document.getElementById('nextPageBtn'),
    pageInfo: document.getElementById('pageInfo'),
    
    // Modal
    dataModal: document.getElementById('dataModal'),
    modalTitle: document.getElementById('modalTitle'),
    dataForm: document.getElementById('dataForm'),
    editDataId: document.getElementById('editDataId'),
    inputDate: document.getElementById('inputDate'),
    inputValue: document.getElementById('inputValue'),
    inputMemo: document.getElementById('inputMemo'),
    closeModalBtn: document.getElementById('closeModalBtn'),
    cancelModalBtn: document.getElementById('cancelModalBtn'),
    
    // Export
    exportCsvBtn: document.getElementById('exportCsvBtn'),
    exportJsonBtn: document.getElementById('exportJsonBtn'),
    
    // Chart
    stockChartCanvas: document.getElementById('stockChart'),
    
    // Toast
    toastContainer: document.getElementById('toastContainer'),

    // Server Settings Modal
    serverSettingsModal: document.getElementById('serverSettingsModal'),
    serverSettingsForm: document.getElementById('serverSettingsForm'),
    inputApiBaseUrl: document.getElementById('inputApiBaseUrl'),
    closeSettingsModalBtn: document.getElementById('closeSettingsModalBtn'),
    resetLocalUrlBtn: document.getElementById('resetLocalUrlBtn'),
    bannerConfigBtn: document.getElementById('bannerConfigBtn')
  };

  // =========================================================
  // Helper & UI Utilities
  // =========================================================
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'error' ? '⚠️' : (type === 'success' ? '✅' : 'ℹ️');
    toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
    elements.toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function escapeHtml(text) {
    if (!text) return '';
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function formatPrice(num) {
    if (num === null || num === undefined || isNaN(num)) return '-';
    return Number(num).toLocaleString('ko-KR') + '원';
  }

  function formatMarkdown(text) {
    if (!text) return '';
    let html = escapeHtml(text);
    // Bold: **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Bullet points: * or -
    html = html.replace(/^\s*[\*\-]\s+(.*)$/gm, '• $1');
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    return html;
  }

  // =========================================================
  // Theme Management
  // =========================================================
  function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    elements.themeToggleBtn.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
  }

  elements.themeToggleBtn.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    elements.themeToggleBtn.textContent = next === 'dark' ? '☀️' : '🌙';
    if (state.stockChart) {
      renderChart(state.allChartData);
    }
  });

  // =========================================================
  // Navigation Tabs
  // =========================================================
  elements.navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.getAttribute('data-target');
      elements.navTabs.forEach(t => {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
      });
      tab.classList.add('active');
      tab.setAttribute('aria-selected', 'true');

      elements.viewPanels.forEach(panel => {
        panel.classList.toggle('active', panel.id === target);
      });

      if (target === 'viewChart' && (!state.stockChart || state.allChartData.length === 0)) {
        loadChartData();
      } else if (target === 'viewData') {
        loadDataItems();
      }
    });
  });

  // =========================================================
  // KPI Summary
  // =========================================================
  async function loadSummary() {
    try {
      const summary = await API.get('/api/data/summary');
      state.summary = summary;
      
      elements.kpiPeriod.textContent = summary.period;
      elements.kpiCount.textContent = `총 ${summary.count.toLocaleString()}개 거래일`;

      const m = summary.metrics;
      elements.kpiLatest.textContent = formatPrice(m.latest);
      elements.kpiAvg.textContent = formatPrice(m.average);
      elements.kpiRange.textContent = `${formatPrice(m.max)}`;
      elements.kpiMin.textContent = `최저: ${formatPrice(m.min)}`;

      // Trend Badge
      elements.kpiTrendBadge.textContent = summary.trend;
      elements.kpiTrendBadge.className = 'trend-badge';
      if (summary.trend.includes('상승')) {
        elements.kpiTrendBadge.classList.add('trend-up');
      } else if (summary.trend.includes('하락')) {
        elements.kpiTrendBadge.classList.add('trend-down');
      } else {
        elements.kpiTrendBadge.classList.add('trend-flat');
      }

      // Chart View: Dynamic Insight Cards below time-series chart
      const insightFactWhy = document.getElementById('insightFactWhy');
      const insightAction = document.getElementById('insightAction');
      if (insightFactWhy && summary.insights) {
        insightFactWhy.innerHTML = `<strong>[실시간 분석]</strong> ${escapeHtml(summary.insights)}<br><span style="color:var(--text-muted);font-size:0.8rem;margin-top:6px;display:inline-block;">* 분석 기간: ${escapeHtml(summary.period)} (총 ${summary.count.toLocaleString()}개 거래일 기준)</span>`;
      }
      if (insightAction && summary.trend) {
        insightAction.innerHTML = `<strong>[전략 제언]</strong> 현재 삼성전자는 <strong>${escapeHtml(summary.trend)}</strong> 상태입니다. 최근 20일 이동평균선(SMA 20)을 1차 지지선으로 설정하고, 단기 이격도가 ±5% 이상 벌어질 경우 분할 대응 전략을 권장합니다.`;
      }
    } catch (err) {
      console.error('Failed to load summary:', err);
    }
  }

  // =========================================================
  // AI Chat & Conversations
  // =========================================================
  async function loadConversations() {
    try {
      const list = await API.get('/api/conversations');
      state.conversations = list;
      renderConversationList();
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  }

  function renderConversationList() {
    elements.conversationList.innerHTML = '';
    if (state.conversations.length === 0) {
      elements.conversationList.innerHTML = '<li style="padding: 12px; font-size: 0.8rem; color: var(--text-muted); text-align: center;">이전 대화가 없습니다.</li>';
      return;
    }

    state.conversations.forEach(conv => {
      const li = document.createElement('li');
      li.className = `conversation-item ${conv.id === state.currentConvId ? 'active' : ''}`;
      li.innerHTML = `
        <div class="conv-title-wrap" title="${escapeHtml(conv.title)}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <span>${escapeHtml(conv.title)}</span>
        </div>
        <button class="conv-del-btn" data-id="${conv.id}" title="대화 삭제" aria-label="대화 삭제">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
        </button>
      `;

      li.querySelector('.conv-title-wrap').addEventListener('click', () => {
        loadSpecificConversation(conv.id);
      });

      li.querySelector('.conv-del-btn').addEventListener('click', async (e) => {
        e.stopPropagation();
        if (confirm('이 대화 기록을 삭제하시겠습니까?')) {
          await deleteConversation(conv.id);
        }
      });

      elements.conversationList.appendChild(li);
    });
  }

  async function loadSpecificConversation(convId) {
    try {
      const conv = await API.get(`/api/conversations/${convId}`);
      state.currentConvId = conv.id;
      renderConversationList();

      elements.chatMessages.innerHTML = '';
      if (elements.welcomeBox) {
        elements.welcomeBox.style.display = 'none';
      }

      conv.messages.forEach(msg => {
        appendChatMessage(msg.role, msg.content, false);
      });

      scrollChatToBottom();
      showToast('대화 기록을 성공적으로 불러왔습니다.', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  async function deleteConversation(convId) {
    try {
      await API.delete(`/api/conversations/${convId}`);
      showToast('대화가 삭제되었습니다.', 'info');
      if (state.currentConvId === convId) {
        resetChatToNew();
      }
      loadConversations();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  function resetChatToNew() {
    state.currentConvId = null;
    elements.chatMessages.innerHTML = '';
    elements.chatMessages.appendChild(elements.welcomeBox);
    elements.welcomeBox.style.display = 'block';
    renderConversationList();
  }

  elements.newChatBtn.addEventListener('click', () => {
    resetChatToNew();
  });

  function appendChatMessage(role, content, animate = true) {
    if (elements.welcomeBox && elements.welcomeBox.style.display !== 'none') {
      elements.welcomeBox.style.display = 'none';
    }

    const row = document.createElement('div');
    row.className = `message-row ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? 'ME' : 'AI';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = formatMarkdown(content);

    row.appendChild(avatar);
    row.appendChild(bubble);

    elements.chatMessages.appendChild(row);
    scrollChatToBottom();
    return row;
  }

  function showTypingIndicator() {
    const row = document.createElement('div');
    row.className = 'message-row assistant typing-row';
    row.id = 'typingIndicator';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = 'AI';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble typing-indicator';
    bubble.innerHTML = `
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    `;

    row.appendChild(avatar);
    row.appendChild(bubble);
    elements.chatMessages.appendChild(row);
    scrollChatToBottom();
  }

  function removeTypingIndicator() {
    const el = document.getElementById('typingIndicator');
    if (el) el.remove();
  }

  function scrollChatToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  }

  async function handleSendMessage(text) {
    const message = text.trim();
    if (!message || state.isGenerating) return;

    appendChatMessage('user', message);
    elements.chatInput.value = '';
    elements.chatInput.style.height = 'auto';

    state.isGenerating = true;
    elements.sendBtn.disabled = true;
    showTypingIndicator();

    try {
      const sendToDiscord = document.getElementById('discordBroadcastCheckbox')?.checked ?? false;
      const endpoint = sendToDiscord ? '/api/discord/chat' : '/api/chat';
      const response = await API.post(endpoint, {
        message: message,
        conversation_id: state.currentConvId
      });

      removeTypingIndicator();
      state.currentConvId = response.conversation_id;
      appendChatMessage('assistant', response.reply);
      
      if (response.sent_to_discord) {
        showToast('Discord 채널로 질문/답변이 실시간 브로드캐스트되었습니다! 📢', 'info');
      }

      // Refresh list to update title & timestamp
      loadConversations();
      loadSummary();
    } catch (err) {
      removeTypingIndicator();
      appendChatMessage('assistant', `⚠️ 오류가 발생했습니다: ${err.message}`);
      showToast(err.message, 'error');
    } finally {
      state.isGenerating = false;
      elements.sendBtn.disabled = false;
    }
  }

  // Discord Briefing Button Event
  const discordBriefingBtn = document.getElementById('discordBriefingBtn');
  if (discordBriefingBtn) {
    discordBriefingBtn.addEventListener('click', async () => {
      try {
        discordBriefingBtn.disabled = true;
        const originalText = discordBriefingBtn.textContent;
        discordBriefingBtn.textContent = '📢 전송 중...';
        await API.post('/api/discord/briefing', {});
        showToast('Discord 채널로 삼성전자 최신 분석 브리핑이 전송되었습니다! 🚀', 'success');
      } catch (err) {
        showToast(`Discord 브리핑 전송 실패: ${err.message}`, 'error');
      } finally {
        discordBriefingBtn.disabled = false;
        discordBriefingBtn.textContent = '📢 Discord 브리핑';
      }
    });
  }

  elements.chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    handleSendMessage(elements.chatInput.value);
  });

  elements.chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(elements.chatInput.value);
    }
  });

  elements.promptChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const query = chip.getAttribute('data-query');
      if (query) {
        handleSendMessage(query);
      }
    });
  });

  // Auto-resize chat textarea
  elements.chatInput.addEventListener('input', () => {
    elements.chatInput.style.height = 'auto';
    elements.chatInput.style.height = Math.min(elements.chatInput.scrollHeight, 120) + 'px';
  });

  // =========================================================
  // Chart.js Visualization (3-1 Time Series Data) & Signals
  // =========================================================
  async function loadChartData() {
    try {
      // Fetch recent trading days for smooth line chart & deep stats for signals
      const [chartRes, statsRes] = await Promise.all([
        API.get('/api/data?limit=150&sort_by=date&sort_order=asc'),
        API.get('/api/data/statistics').catch(() => null)
      ]);
      state.allChartData = chartRes.items;
      renderChart(state.allChartData);
      if (statsRes) {
        renderTechnicalSignals(statsRes);
      }
    } catch (err) {
      console.error('Failed to load chart data:', err);
    }
  }

  function renderTechnicalSignals(stats) {
    const badge = document.getElementById('signalBadge');
    const rsiEl = document.getElementById('rsiIndicator');
    const summaryText = document.getElementById('signalSummaryText');
    const warningBox = document.getElementById('signalWarningBox');
    if (!badge || !rsiEl || !summaryText || !warningBox) return;

    const rsi = stats.rsi_14;
    rsiEl.textContent = `RSI 14: ${rsi.toFixed(1)}`;

    let badgeClass = 'signal-hold';
    let badgeText = '중립 / 관망';
    let summaryMsg = '';
    let warningMsg = '';

    if (rsi >= 70) {
      badgeClass = 'signal-sell';
      badgeText = '🔴 과열 / 분할 매도 고려';
      summaryMsg = `14일 상대강도지수(RSI)가 ${rsi.toFixed(1)}로 단기 과열 임계치(70)를 초과했습니다. 단기 차익실현 매물 출회 가능성이 높습니다.`;
      warningMsg = `⚠️ <strong>[단기 과매수 경고]</strong> 추격 매수를 자제하고 20일 이동평균선(SMA 20: ${formatPrice(stats.sma_20)}) 이탈 여부를 주시하며 분할 차익실현을 권장합니다.`;
    } else if (rsi <= 30) {
      badgeClass = 'signal-buy';
      badgeText = '🟢 과매도 / 분할 매수 기회';
      summaryMsg = `14일 상대강도지수(RSI)가 ${rsi.toFixed(1)}로 기술적 과매도 구간(30 이하)에 도달했습니다. 낙폭 과대에 따른 반등 압력이 형성 중입니다.`;
      warningMsg = `💡 <strong>[기술적 반등 신호]</strong> 과거 최저 지지선(${formatPrice(stats.min_price)}) 방어 여부를 확인하며 분할 매수 관점 진입이 유효합니다.`;
    } else {
      const trend = (state.summary && state.summary.trend) ? state.summary.trend : '';
      if (trend.includes('상승')) {
        badgeClass = 'signal-buy';
        badgeText = '🟢 추세 상승 / 보유 및 추종';
        summaryMsg = `RSI 지수(${rsi.toFixed(1)})가 안정적이며 20일 이동평균선(${formatPrice(stats.sma_20)}) 대비 견조한 우상향 추세를 유지하고 있습니다.`;
        warningMsg = `ℹ️ <strong>[안정 성장 구간]</strong> 20일 역사적 변동성(±${formatPrice(stats.volatility)})을 감안하여 트레일링 스탑을 설정하세요.`;
      } else if (trend.includes('하락')) {
        badgeClass = 'signal-sell';
        badgeText = '🔴 단기 조정 / 비중 축소';
        summaryMsg = `20일 이동평균선(${formatPrice(stats.sma_20)})을 하회하는 약세 흐름입니다. 60일 이동평균선(${formatPrice(stats.sma_60)}) 지지 확인이 선행되어야 합니다.`;
        warningMsg = `⚠️ <strong>[추세 하락 주의]</strong> 섣부른 물타기를 지양하고 하락 브레이크가 걸릴 때까지 현금 비중 확대를 권장합니다.`;
      } else {
        badgeClass = 'signal-hold';
        badgeText = '🟡 박스권 / 관망 및 탐색';
        summaryMsg = `20일 및 60일 이동평균선 부근에서 횡보 중입니다. 명확한 거래량 수반 돌파가 나타날 때까지 관망을 권장합니다.`;
        warningMsg = '';
      }
    }

    badge.className = `signal-badge ${badgeClass}`;
    badge.textContent = badgeText;
    summaryText.textContent = summaryMsg;

    if (warningMsg) {
      warningBox.style.display = 'block';
      warningBox.innerHTML = warningMsg;
    } else {
      warningBox.style.display = 'none';
    }
  }

  function calculateSMA(data, period = 20) {
    const sma = [];
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        sma.push(null);
      } else {
        const slice = data.slice(i - period + 1, i + 1);
        const sum = slice.reduce((acc, curr) => acc + curr.value, 0);
        sma.push(Math.round(sum / period));
      }
    }
    return sma;
  }

  function renderChart(items) {
    if (!items || items.length === 0) return;

    const labels = items.map(item => item.date);
    const closePrices = items.map(item => item.value);
    const sma20 = calculateSMA(items, 20);

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#9ca3af' : '#475569';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';

    if (state.stockChart) {
      state.stockChart.destroy();
    }

    const ctx = elements.stockChartCanvas.getContext('2d');
    
    // Gradient for close price line
    const gradient = ctx.createLinearGradient(0, 0, 0, 350);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.4)');
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

    state.stockChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: '삼성전자 종가 (원)',
            data: closePrices,
            borderColor: '#3b82f6',
            backgroundColor: gradient,
            borderWidth: 2,
            fill: true,
            tension: 0.1,
            pointRadius: 0,
            pointHoverRadius: 5
          },
          {
            label: '20일 이동평균선 (SMA 20)',
            data: sma20,
            borderColor: '#f59e0b',
            borderWidth: 1.8,
            borderDash: [5, 4],
            fill: false,
            tension: 0.1,
            pointRadius: 0,
            pointHoverRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false
        },
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: textColor,
              font: { family: 'Outfit', size: 12 }
            }
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                let label = context.dataset.label || '';
                if (label) label += ': ';
                if (context.parsed.y !== null) {
                  label += Number(context.parsed.y).toLocaleString() + '원';
                }
                return label;
              }
            }
          }
        },
        scales: {
          x: {
            grid: { color: gridColor },
            ticks: {
              color: textColor,
              maxTicksLimit: 12,
              font: { family: 'Outfit', size: 11 }
            }
          },
          y: {
            grid: { color: gridColor },
            ticks: {
              color: textColor,
              callback: function (val) {
                return (val / 10000) + '만원';
              },
              font: { family: 'Outfit', size: 11 }
            }
          }
        }
      }
    });
  }

  // =========================================================
  // Data Management CRUD
  // =========================================================
  async function loadDataItems() {
    try {
      const offset = state.dataPage * state.dataLimit;
      const res = await API.get(`/api/data?limit=${state.dataLimit}&offset=${offset}&sort_order=${state.sortOrder}`);
      state.dataTotal = res.total;
      renderDataTable(res.items);
      updatePaginationControls();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  function renderDataTable(items) {
    elements.dataTableBody.innerHTML = '';
    if (!items || items.length === 0) {
      elements.dataTableBody.innerHTML = `
        <tr><td colspan="4" style="text-align: center; padding: 24px; color: var(--text-muted);">
          등록된 데이터가 없습니다.
        </td></tr>
      `;
      return;
    }

    items.forEach(item => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${escapeHtml(item.date)}</strong></td>
        <td class="price-cell">${formatPrice(item.value)}</td>
        <td class="memo-cell" title="${escapeHtml(item.memo)}">${escapeHtml(item.memo || '-')}</td>
        <td style="text-align: center;">
          <div class="action-btns" style="justify-content: center;">
            <button class="icon-action-btn edit-btn" data-id="${item.id}" title="수정" aria-label="수정">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            </button>
            <button class="icon-action-btn del delete-btn" data-id="${item.id}" title="삭제" aria-label="삭제">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
        </td>
      `;

      tr.querySelector('.edit-btn').addEventListener('click', () => openEditModal(item));
      tr.querySelector('.delete-btn').addEventListener('click', () => handleDeleteItem(item.id, item.date));

      elements.dataTableBody.appendChild(tr);
    });
  }

  function updatePaginationControls() {
    const totalPages = Math.ceil(state.dataTotal / state.dataLimit) || 1;
    const currentPage = state.dataPage + 1;
    elements.pageInfo.textContent = `총 ${state.dataTotal.toLocaleString()}개 항목 중 (${currentPage} / ${totalPages} 페이지)`;
    elements.prevPageBtn.disabled = state.dataPage <= 0;
    elements.nextPageBtn.disabled = currentPage >= totalPages;
  }

  elements.prevPageBtn.addEventListener('click', () => {
    if (state.dataPage > 0) {
      state.dataPage--;
      loadDataItems();
    }
  });

  elements.nextPageBtn.addEventListener('click', () => {
    const totalPages = Math.ceil(state.dataTotal / state.dataLimit) || 1;
    if (state.dataPage + 1 < totalPages) {
      state.dataPage++;
      loadDataItems();
    }
  });

  elements.sortOrderSelect.addEventListener('change', (e) => {
    state.sortOrder = e.target.value;
    state.dataPage = 0;
    loadDataItems();
  });

  elements.refreshDataBtn.addEventListener('click', async () => {
    try {
      elements.refreshDataBtn.disabled = true;
      elements.refreshDataBtn.textContent = '🔄 최신 동기화 중...';

      // 1. Trigger backend sync up to today (Yahoo Finance / latest records)
      const syncRes = await API.post('/api/data/sync', {});

      // 2. Reload data items, summary bar, and chart
      await Promise.all([
        loadDataItems(),
        loadSummary(),
        loadChartData()
      ]);

      if (syncRes && syncRes.updated_count > 0) {
        showToast(`오늘까지의 최신 데이터 ${syncRes.updated_count}건이 성공적으로 동기화되었습니다! (최신일: ${syncRes.latest_date})`, 'success');
      } else {
        showToast('이미 오늘까지의 데이터가 최신 상태입니다. 목록을 새로고침했습니다.', 'info');
      }
    } catch (err) {
      await loadDataItems();
      showToast(`최신 데이터 동기화 알림: ${err.message}`, 'warning');
    } finally {
      elements.refreshDataBtn.disabled = false;
      elements.refreshDataBtn.textContent = '🔄 새로고침';
    }
  });

  // Modal Handlers
  function openAddModal() {
    elements.modalTitle.textContent = '새 시계열 데이터 추가';
    elements.editDataId.value = '';
    elements.dataForm.reset();
    
    // Set default date to today
    elements.inputDate.value = new Date().toISOString().split('T')[0];
    elements.dataModal.classList.add('active');
  }

  function openEditModal(item) {
    elements.modalTitle.textContent = '시계열 데이터 수정';
    elements.editDataId.value = item.id;
    elements.inputDate.value = item.date;
    elements.inputValue.value = item.value;
    elements.inputMemo.value = item.memo || '';
    elements.dataModal.classList.add('active');
  }

  function closeModal() {
    elements.dataModal.classList.remove('active');
  }

  elements.openAddModalBtn.addEventListener('click', openAddModal);
  elements.closeModalBtn.addEventListener('click', closeModal);
  elements.cancelModalBtn.addEventListener('click', closeModal);
  elements.dataModal.addEventListener('click', (e) => {
    if (e.target === elements.dataModal) closeModal();
  });

  elements.dataForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = elements.editDataId.value;
    const payload = {
      date: elements.inputDate.value,
      value: parseFloat(elements.inputValue.value),
      memo: elements.inputMemo.value.trim()
    };

    try {
      if (id) {
        // Edit
        await API.put(`/api/data/${id}`, payload);
        showToast('데이터가 성공적으로 수정되었습니다.', 'success');
      } else {
        // Add
        await API.post('/api/data', payload);
        showToast('새 데이터가 성공적으로 등록되었습니다.', 'success');
      }

      closeModal();
      loadDataItems();
      loadSummary();
      loadChartData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  async function handleDeleteItem(id, dateStr) {
    if (!confirm(`[${dateStr}] 일자 데이터를 정말 삭제하시겠습니까?`)) return;

    try {
      await API.delete(`/api/data/${id}`);
      showToast('데이터가 삭제되었습니다.', 'info');
      loadDataItems();
      loadSummary();
      loadChartData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  // =========================================================
  // Export CSV / JSON
  // =========================================================
  elements.exportCsvBtn.addEventListener('click', () => {
    window.open(`${CONFIG.API_BASE_URL}/api/data/export?format=csv`, '_blank');
  });

  elements.exportJsonBtn.addEventListener('click', () => {
    window.open(`${CONFIG.API_BASE_URL}/api/data/export?format=json`, '_blank');
  });

  // =========================================================
  // Initial Healthcheck & Bootstrap
  // =========================================================
  async function initApp() {
    initTheme();

    // Check health
    if (elements.swaggerDocsLink) {
      elements.swaggerDocsLink.href = `${CONFIG.API_BASE_URL}/docs`;
    }
    try {
      const health = await API.get('/health');
      elements.apiStatusBadge.style.display = 'flex';
      elements.apiStatusText.textContent = `API 정상 (데이터 ${health.data_count.toLocaleString()}건)`;
    } catch (err) {
      elements.apiStatusBadge.style.backgroundColor = 'rgba(244, 63, 94, 0.15)';
      elements.apiStatusBadge.style.color = 'var(--accent-rose)';
      elements.apiStatusText.textContent = 'API 연결 대기 중...';
      elements.coldStartBanner.classList.remove('hidden');
    }

    // Load initial views
    await Promise.all([
      loadSummary(),
      loadConversations(),
      loadDataItems(),
      loadChartData()
    ]);
  }

  elements.dismissBannerBtn.addEventListener('click', () => {
    elements.coldStartBanner.classList.add('hidden');
  });

  // Server Settings Modal Trigger & Form
  function openServerSettings() {
    if (elements.serverSettingsModal) {
      elements.inputApiBaseUrl.value = localStorage.getItem('API_BASE_URL') || CONFIG.API_BASE_URL || '';
      elements.serverSettingsModal.classList.add('active');
    }
  }

  function closeServerSettings() {
    if (elements.serverSettingsModal) {
      elements.serverSettingsModal.classList.remove('active');
    }
  }

  if (elements.bannerConfigBtn) {
    elements.bannerConfigBtn.addEventListener('click', (e) => {
      e.preventDefault();
      openServerSettings();
    });
  }

  if (elements.apiStatusBadge) {
    elements.apiStatusBadge.style.cursor = 'pointer';
    elements.apiStatusBadge.title = '클릭하여 백엔드 API 서버 주소 변경';
    elements.apiStatusBadge.addEventListener('click', openServerSettings);
  }

  if (elements.closeSettingsModalBtn) {
    elements.closeSettingsModalBtn.addEventListener('click', closeServerSettings);
  }

  if (elements.resetLocalUrlBtn) {
    elements.resetLocalUrlBtn.addEventListener('click', () => {
      localStorage.removeItem('API_BASE_URL');
      showToast('로컬 개발 주소(http://localhost:8000)로 초기화되었습니다. 새로고침합니다.', 'info');
      setTimeout(() => location.reload(), 800);
    });
  }

  if (elements.serverSettingsForm) {
    elements.serverSettingsForm.addEventListener('submit', (e) => {
      e.preventDefault();
      let url = elements.inputApiBaseUrl.value.trim();
      if (url.endsWith('/')) url = url.slice(0, -1);
      localStorage.setItem('API_BASE_URL', url);
      showToast('백엔드 API 주소가 저장되었습니다. 연결을 시도합니다...', 'success');
      setTimeout(() => location.reload(), 600);
    });
  }

  // Mobile Sidebar Toggle
  const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
  const appSidebar = document.getElementById('appSidebar');
  if (mobileSidebarToggle && appSidebar) {
    mobileSidebarToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      appSidebar.classList.toggle('open');
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
      if (window.innerWidth <= 900 && appSidebar.classList.contains('open')) {
        if (!appSidebar.contains(e.target) && !mobileSidebarToggle.contains(e.target)) {
          appSidebar.classList.remove('open');
        }
      }
    });
  }

  // Network Online / Offline Detection
  window.addEventListener('online', () => {
    showToast('네트워크 연결이 복구되었습니다. 최신 데이터를 동기화합니다.', 'success');
    loadSummary();
    loadDataItems();
    loadConversations();
  });

  window.addEventListener('offline', () => {
    showToast('네트워크 연결이 끊겼습니다. 현재 오프라인 모드입니다.', 'warning');
  });

  // Start app on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
  } else {
    initApp();
  }

})();
