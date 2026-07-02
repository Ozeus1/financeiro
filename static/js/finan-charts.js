/* ════════════════════════════════════════════════════════════════
   FiNan Charts — defaults globais do Chart.js + helpers.
   Carregado no base.html logo após o chart.umd.min.js.
   ════════════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    window.FinanUI = {
        // Paleta padrão para gráficos de categorias
        palette: ['#4361ee', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899',
                  '#14b8a6', '#f97316', '#6366f1', '#84cc16', '#06b6d4', '#e11d48'],

        // "R$ 1.234,56"
        brl: function (v) {
            return 'R$ ' + Number(v || 0).toLocaleString('pt-BR', {
                minimumFractionDigits: 2, maximumFractionDigits: 2
            });
        },

        // "R$ 12,3k" — para eixos
        brlCompact: function (v) {
            var n = Number(v || 0), a = Math.abs(n), s = n < 0 ? '-' : '';
            if (a >= 1000000) return s + 'R$ ' + (a / 1000000).toLocaleString('pt-BR', { maximumFractionDigits: 1 }) + 'M';
            if (a >= 1000)    return s + 'R$ ' + (a / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 }) + 'k';
            return s + 'R$ ' + a.toLocaleString('pt-BR', { maximumFractionDigits: 0 });
        },

        // Callback de tooltip padrão (label + valor em BRL)
        tooltipLabel: function (ctx) {
            var v = ctx.parsed.y !== undefined && ctx.parsed.y !== null ? ctx.parsed.y : ctx.parsed;
            return ' ' + ctx.dataset.label + ': ' + window.FinanUI.brl(Math.abs(v));
        }
    };

    if (typeof Chart === 'undefined') return;

    Chart.defaults.font.family = "'Inter','Segoe UI',system-ui,-apple-system,sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.color = '#64748b';

    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15,23,42,.92)';
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 10;
    Chart.defaults.plugins.tooltip.boxPadding = 4;
    Chart.defaults.plugins.tooltip.titleFont = { weight: '700' };

    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.pointStyle = 'rectRounded';
    Chart.defaults.plugins.legend.labels.boxWidth = 10;
    Chart.defaults.plugins.legend.labels.boxHeight = 10;

    Chart.defaults.elements.bar.borderRadius = 6;
    Chart.defaults.elements.line.tension = 0.35;
    Chart.defaults.elements.point.radius = 3;
    Chart.defaults.elements.point.hoverRadius = 5;
})();
