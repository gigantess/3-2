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

  const API = {
    async get(endpoint) {
      const res = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || '요청 처리에 실패했습니다.');
      }
      return res.json();
    },

    async post(endpoint, data) {
      const res = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || '요청 처리에 실패했습니다.');
      }
      return res.json();
    },

    async put(endpoint, data) {
      const res = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || '요청 처리에 실패했습니다.');
      }
      return res.json();
    },

    async delete(endpoint) {
      const res = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`, {
        method: 'DELETE'
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || '요청 처리에 실패했습니다.');
      }
      return res.json();
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
    toastContainer: document.getElementById('toastContainer')
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
      const response = await API.post('/api/chat', {
        message: message,
        conversation_id: state.currentConvId
      });

      removeTypingIndicator();
      state.currentConvId = response.conversation_id;
      appendChatMessage('assistant', response.reply);
      
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
  // Chart.js Visualization (3-1 Time Series Data)
  // =========================================================
  async function loadChartData() {
    try {
      // Fetch up to 150 recent trading days for smooth line chart
      const res = await API.get('/api/data?limit=150&sort_by=date&sort_order=asc');
      state.allChartData = res.items;
      renderChart(state.allChartData);
    } catch (err) {
      console.error('Failed to load chart data:', err);
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

  elements.refreshDataBtn.addEventListener('click', () => {
    loadDataItems();
    loadSummary();
    showToast('데이터 목록을 새로고침했습니다.', 'info');
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
      loadDataItems()
    ]);
  }

  elements.dismissBannerBtn.addEventListener('click', () => {
    elements.coldStartBanner.classList.add('hidden');
  });

  // Start app on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
  } else {
    initApp();
  }

})();
