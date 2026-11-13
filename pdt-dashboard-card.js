
/* Portfolio Dividend Tracker dashboard card - v0.3.3 */
(() => {
  const DOMAIN = 'portfolio_dividend_tracker';
  const METRICS = {
    currentWorth: ['Portefeuillewaarde', '€'],
    totalGains: ['Totaal resultaat', '€'],
    unrealisedGains: ['Ongerealiseerd resultaat', '€'],
    realisedGains: ['Gerealiseerd resultaat', '€'],
    dividendsReceived: ['Ontvangen dividend', '€'],
    transactionsCosts: ['Transactiekosten', '€']
  };
  const PERIODS = [
    ['1m', '1M'], ['3m', '3M'], ['ytd', 'YTD'],
    ['1y', '1J'], ['max', 'MAX']
  ];

  const num = v => Number(v && typeof v === 'object' ? v.value : v);
  const fmt = v => Number.isFinite(num(v))
    ? new Intl.NumberFormat('nl-NL', {
        style: 'currency',
        currency: 'EUR',
        maximumFractionDigits: 2
      }).format(num(v))
    : '—';
  const esc = s => String(s ?? '').replace(
    /[&<>"']/g,
    c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;',
      '"': '&quot;', "'": '&#39;'
    }[c])
  );

  class PDTDashboardCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.period = 'ytd';
      this.metric = 'currentWorth';
      this.points = [];
      this.loading = false;
      this.error = '';
      this.lastKey = '';
      this._hass = null;
    }

    setConfig(config) {
      this.config = {
        title: 'Portfolio Dividend Tracker',
        grid_columns: 12,
        chart_height: 400,
        ...config
      };
      if (config.grid_columns == null && config.card_width != null) {
        this.config.grid_columns = Math.max(1, Math.min(12, Math.round(Number(config.card_width) * 12 / 100) || 12));
      }
      this.render();
    }

    set hass(hass) {
      this._hass = hass;
      this.render();
      if (!this.lastKey && !this.loading) this.load();
    }

    static getConfigElement() {
      return document.createElement('pdt-dashboard-card-editor');
    }

    static getStubConfig() {
      return {
        title: 'Portfolio Dividend Tracker',
        grid_columns: 12,
        chart_height: 400
      };
    }

    getCardSize() {
      return Math.max(
        4,
        Math.ceil((Number(this.config?.chart_height) || 400) / 50) + 4
      );
    }

    getGridOptions() {
      return {
        columns: Math.max(1, Math.min(12, Number(this.config?.grid_columns) || 12)),
        min_columns: 1,
        rows: Math.max(
          4,
          Math.ceil((Number(this.config?.chart_height) || 400) / 50) + 4
        )
      };
    }

    findValue(label) {
      const explicit = this.config?.entities?.[label];
      if (explicit) return this._hass?.states?.[explicit]?.state;

      const found = Object.values(this._hass?.states || {}).find(
        x => x.entity_id.startsWith('sensor.') &&
          (x.attributes.friendly_name || '')
            .toLowerCase()
            .includes(METRICS[label][0].toLowerCase())
      );
      return found?.state;
    }

    async load() {
      if (!this._hass || this.loading) return;

      this.loading = true;
      this.error = '';
      this.render();

      try {
        const msg = {
          type: 'call_service',
          domain: DOMAIN,
          service: 'get_history',
          service_data: {
            period: this.period,
            group_by: this.period === '1m' || this.period === '3m'
              ? 'day'
              : 'week'
          },
          return_response: true
        };

        if (this.config.entry_id) {
          msg.service_data.entry_id = this.config.entry_id;
        }

        const result = await this._hass.connection.sendMessagePromise(msg);
        const payload = result?.response ?? result;
        const data = payload?.data ?? payload;

        if (!Array.isArray(data?.ticks)) {
          throw new Error('Geen ticks-array in API-response');
        }

        this.points = data.ticks
          .filter(t => t && t.values && t.date)
          .sort((a, b) => String(a.date).localeCompare(String(b.date)));

        this.lastKey = this.period;
        this.lastUpdate = Date.now();
      } catch (e) {
        this.error = e?.message || String(e);
        this.points = [];
      } finally {
        this.loading = false;
        this.render();
      }
    }

    render() {
      if (!this.shadowRoot || !this.config) return;

      const data = this.points.map(p => ({
        date: p.date,
        label: p.label || p.date,
        v: num(p.values[this.metric])
      })).filter(p => Number.isFinite(p.v));

      let chart = '<div class="empty">' +
        (this.loading
          ? 'Historische gegevens ophalen…'
          : this.error
            ? 'API-fout: ' + esc(this.error)
            : 'Geen historische gegevens beschikbaar') +
        '</div>';

      const chartHeight = Math.max(
        200,
        Math.min(800, Number(this.config.chart_height) || 400)
      );

      if (data.length) {
        const w = 960;
        const h = chartHeight;
        const pad = 38;

        let min = Math.min(...data.map(p => p.v));
        let max = Math.max(...data.map(p => p.v));

        if (min === max) {
          min -= 1;
          max += 1;
        }

        const spread = max - min;
        min -= spread * 0.08;
        max += spread * 0.08;

        const x = i => pad + i * (w - pad * 2) /
          Math.max(1, data.length - 1);
        const y = v => h - pad -
          (v - min) / (max - min) * (h - pad * 2);

        const d = data.map(
          (p, i) => (i ? 'L' : 'M') +
            x(i).toFixed(1) + ' ' + y(p.v).toFixed(1)
        ).join(' ');

        const ticks = [0, .25, .5, .75, 1].map(t => {
          const yy = pad + t * (h - 2 * pad);
          return `<line x1="${pad}" x2="${w-pad}" y1="${yy}" y2="${yy}"
            stroke="currentColor" opacity=".12"
            stroke-dasharray="4 5"/>
            <text x="${pad-6}" y="${yy+4}" text-anchor="end"
            fill="currentColor" opacity=".65" font-size="11">
            ${esc(new Intl.NumberFormat('nl-NL', {
              maximumFractionDigits: 0
            }).format(max - t * (max - min)))}</text>`;
        }).join('');

        const markers = data.map(
          (p, i) => `<circle cx="${x(i)}" cy="${y(p.v)}"
            r="9" fill="transparent">
            <title>${esc(p.label)}: ${esc(fmt(p.v))}</title>
            </circle>`
        ).join('');

        chart = `<svg viewBox="0 0 ${w} ${h}" role="img"
          aria-label="Historische ${esc(METRICS[this.metric][0])}">
          ${ticks}
          <path d="${d}" fill="none" stroke="#17b989"
          stroke-width="3" stroke-linejoin="round"
          stroke-linecap="round"/>
          ${markers}
          <text x="${pad}" y="${h-8}" fill="currentColor"
          opacity=".65" font-size="12">${esc(data[0].label)}</text>
          <text x="${w-pad}" y="${h-8}" text-anchor="end"
          fill="currentColor" opacity=".65" font-size="12">
          ${esc(data[data.length-1].label)}</text>
          </svg>`;
      }

      const keys = ['currentWorth', 'totalGains', 'dividendsReceived'];
      const tiles = keys.map(k => {
        const last = this.points.at(-1)?.values?.[k];
        const val = this.findValue(k) ?? last;
        return `<div class="tile">
          <div class="muted">${esc(METRICS[k][0])}</div>
          <div class="value">${fmt(val)}</div>
          </div>`;
      }).join('');

      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
            color: var(--primary-text-color, #222);
            font-family: var(--paper-font-body1_-_font-family, Arial, sans-serif);
          }
          ha-card {
            background: var(--ha-card-background, var(--card-background-color, #fff));
            border-radius: var(--ha-card-border-radius, 16px);
            padding: 22px;
            overflow: hidden;
          }
          .top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
          }
          .heading { font-size: 24px; font-weight: 700; }
          .muted, .foot {
            color: var(--secondary-text-color, #777);
            font-size: 13px;
          }
          .tiles {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin: 20px 0;
          }
          .tile {
            border: 1px solid var(--divider-color, #ddd);
            border-radius: 12px;
            padding: 16px;
            min-width: 0;
          }
          .value {
            font-size: 23px;
            font-weight: 650;
            margin-top: 8px;
            overflow-wrap: anywhere;
          }
          .controls {
            display: flex;
            gap: 8px;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            margin: 18px 0;
          }
          .buttons { display: flex; flex-wrap: wrap; gap: 5px; }
          button {
            border: 1px solid var(--divider-color, #ddd);
            background: transparent;
            color: inherit;
            border-radius: 8px;
            padding: 9px 12px;
            cursor: pointer;
            font: inherit;
          }
          button.active {
            background: var(--primary-color, #178a71);
            color: #fff;
            border-color: transparent;
          }
          button:disabled { opacity: .5; cursor: wait; }
          .chart svg {
            width: 100%;
            height: ${chartHeight}px;
            display: block;
          }
          .empty {
            min-height: 220px;
            display: grid;
            place-items: center;
            text-align: center;
            color: var(--secondary-text-color, #777);
          }
          .foot {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            margin-top: 10px;
            flex-wrap: wrap;
          }
          @media(max-width:650px) {
            ha-card { padding: 14px; }
            .tiles { grid-template-columns: 1fr; }
            .heading { font-size: 20px; }
            .value { font-size: 20px; }
          }
        </style>
        <ha-card>
          <div class="top">
            <div>
              <div class="heading">${esc(this.config.title)}</div>
              <div class="muted">Historische portefeuilleprestaties</div>
            </div>
            <button id="refresh" ${this.loading ? 'disabled' : ''}>
              ↻ Vernieuwen
            </button>
          </div>
          <div class="tiles">${tiles}</div>
          <div class="controls">
            <div class="buttons">
              ${PERIODS.map(([id, label]) =>
                `<button data-period="${id}"
                class="${this.period === id ? 'active' : ''}"
                ${this.loading ? 'disabled' : ''}>${label}</button>`
              ).join('')}
            </div>
            <div class="buttons">
              ${Object.entries(METRICS).map(([id, [label]]) =>
                `<button data-metric="${id}"
                class="${this.metric === id ? 'active' : ''}">
                ${esc(label)}</button>`
              ).join('')}
            </div>
          </div>
          <div class="chart">${chart}</div>
          <div class="foot">
            <span>${data.length} meetpunten · ${esc(this.period.toUpperCase())}</span>
            <span>${this.lastUpdate
              ? 'Bijgewerkt ' + new Date(this.lastUpdate).toLocaleTimeString('nl-NL')
              : ''}</span>
          </div>
        </ha-card>`;

      this.shadowRoot.querySelector('#refresh').onclick = () => this.load();
      this.shadowRoot.querySelectorAll('[data-period]').forEach(b => {
        b.onclick = () => {
          this.period = b.dataset.period;
          this.load();
        };
      });
      this.shadowRoot.querySelectorAll('[data-metric]').forEach(b => {
        b.onclick = () => {
          this.metric = b.dataset.metric;
          this.render();
        };
      });
    }
  }

  class PDTDashboardCardEditor extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.config = {
        title: 'Portfolio Dividend Tracker',
        grid_columns: 12,
        chart_height: 400
      };
    }

    setConfig(config) {
      this.config = {
        title: 'Portfolio Dividend Tracker',
        grid_columns: 12,
        chart_height: 400,
        ...config
      };
      if (config.grid_columns == null && config.card_width != null) {
        this.config.grid_columns = Math.max(1, Math.min(12, Math.round(Number(config.card_width) * 12 / 100) || 12));
      }
      this.render();
    }

    set hass(hass) {
      this._hass = hass;
    }

    render() {
      const width = Math.max(
        1,
        Math.min(12, Number(this.config.grid_columns) || 12)
      );
      const height = Math.max(
        200,
        Math.min(800, Number(this.config.chart_height) || 400)
      );

      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
            color: var(--primary-text-color);
            font-family: var(--paper-font-body1_-_font-family, Arial, sans-serif);
          }
          .field { margin: 16px 0 22px; }
          label {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 10px;
            font-weight: 500;
          }
          input[type=range] {
            width: 100%;
            accent-color: var(--primary-color, #03a9f4);
            cursor: pointer;
          }
          input[type=text] {
            width: 100%;
            box-sizing: border-box;
            padding: 12px;
            border: 1px solid var(--divider-color, #777);
            border-radius: 8px;
            background: var(--card-background-color);
            color: inherit;
            font: inherit;
          }
          .hint {
            font-size: 12px;
            color: var(--secondary-text-color);
            margin-top: 7px;
          }
        </style>
        <div class="field">
          <label for="title">Titel</label>
          <input id="title" type="text" value="${esc(this.config.title)}">
        </div>
        <div class="field">
          <label for="width">
            Kolombreedte <output id="width-value">${width} / 12</output>
          </label>
          <input id="width" type="range"
            min="1" max="12" step="1" value="${width}">
          <div class="hint">
            Aantal gridkolommen dat de kaart inneemt in een Secties-dashboard.
            De beschikbare ruimte is afhankelijk van de sectie-indeling.
          </div>
        </div>
        <div class="field">
          <label for="height">
            Grafiekhoogte <output id="height-value">${height} px</output>
          </label>
          <input id="height" type="range"
            min="200" max="800" step="25" value="${height}">
        </div>`;

      const update = (key, value) => {
        this.config = { ...this.config, [key]: value };
        this.dispatchEvent(new CustomEvent('config-changed', {
          detail: { config: { ...this.config } },
          bubbles: true,
          composed: true
        }));
      };

      const title = this.shadowRoot.getElementById('title');
      title.addEventListener('change', () => update('title', title.value));

      for (const [id, key, suffix] of [
        ['width', 'grid_columns', ' / 12'],
        ['height', 'chart_height', ' px']
      ]) {
        const input = this.shadowRoot.getElementById(id);
        const output = this.shadowRoot.getElementById(id + '-value');
        input.addEventListener('input', () => {
          output.textContent = input.value + suffix;
          update(key, Number(input.value));
        });
      }
    }
  }

  if (!customElements.get('pdt-dashboard-card-editor')) {
    customElements.define('pdt-dashboard-card-editor', PDTDashboardCardEditor);
  }

  if (!customElements.get('pdt-dashboard-card')) {
    customElements.define('pdt-dashboard-card', PDTDashboardCard);
  }

  window.customCards = window.customCards || [];
  window.customCards.push({
    type: 'pdt-dashboard-card',
    name: 'PDT Dashboard Card',
    description: 'Historische portefeuilleprestaties met instelbare gridkolommen en grafiekhoogte'
  });
})();
