import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement,
  Filler, Tooltip, Legend,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Filler, Tooltip, Legend)
ChartJS.defaults.color = '#94a0bd'
ChartJS.defaults.font.family = 'Inter, system-ui, sans-serif'
ChartJS.defaults.borderColor = 'rgba(148,163,214,0.08)'

export const baseOptions = (extra = {}) => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { labels: { boxWidth: 10, boxHeight: 10, usePointStyle: true, font: { size: 11 } } },
    tooltip: { backgroundColor: '#172036', borderColor: 'rgba(148,163,214,.2)', borderWidth: 1, padding: 10 },
  },
  scales: {
    x: { grid: { display: false }, ticks: { font: { size: 10 }, maxRotation: 0 } },
    y: { ticks: { font: { size: 10 } } },
  },
  ...extra,
})

/** Gradient fill for line datasets */
export const fill = (hex) => (ctx) => {
  const { chart } = ctx
  const { ctx: c, chartArea } = chart
  if (!chartArea) return `${hex}22`
  const g = c.createLinearGradient(0, chartArea.top, 0, chartArea.bottom)
  g.addColorStop(0, `${hex}55`)
  g.addColorStop(1, `${hex}00`)
  return g
}

/** Horizontal threshold line dataset */
export const threshold = (label, value, n, color) => ({
  label, data: Array(n).fill(value), borderColor: color, borderDash: [5, 5],
  borderWidth: 1.2, pointRadius: 0, fill: false,
})
