// ==========================================
// GLOBALS, STATE, & CONSTANTS
// ==========================================
let budgetData = null;
let activeCharts = {};
let tableData = [];
let tableSort = { key: 'year', asc: false };

// Theme Colors for Chart.js
const CHART_COLORS = [
  '#8f7efc', // Purple
  '#00a8ff', // Blue
  '#00d2d3', // Green
  '#ff9f43', // Yellow
  '#ff7675', // Red
  '#fd79a8', // Pink
  '#fdcb6e', // Peach
  '#00cec9', // Teal
  '#a55eea', // Violet
  '#26de81'  // Mint
];

// Helper to get translucent versions of chart colors
const hexToRgba = (hex, opacity) => {
  const c = hex.replace('#', '');
  const r = parseInt(c.substring(0, 2), 16);
  const g = parseInt(c.substring(2, 4), 16);
  const b = parseInt(c.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
};

// Global Chart Options
Chart.defaults.color = '#958eb6';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 11;

// ==========================================
// INITIALIZATION & EVENT LISTENERS
// ==========================================
document.addEventListener('DOMContentLoaded', async () => {
  await fetchBudgetData();
  initializeNavbar();
  populateDropdowns();
  setupEventListeners();
  
  // Render default view (Overview Tab)
  renderOverviewTab();
});

// Fetch compiled data
async function fetchBudgetData() {
  try {
    const response = await fetch('budget_data.json');
    budgetData = await response.json();
    
    // Prepare table flattened dataset
    tableData = [];
    budgetData.years.forEach(year => {
      const yearTotal = getYearTotalOutlay(year);
      budgetData.ministries.forEach(m => {
        const outlay = m.history[year] || 0;
        const share = yearTotal > 0 ? (outlay / yearTotal) * 100 : 0;
        tableData.push({
          ministry: m.name,
          key: m.key,
          year: year,
          outlay: outlay,
          share: share
        });
      });
    });
  } catch (error) {
    console.error("Error fetching budget_data.json:", error);
  }
}

// Navigation Tabs
function initializeNavbar() {
  const navItems = document.querySelectorAll('.nav-item');
  const tabPanes = document.querySelectorAll('.tab-pane');
  const tabTitle = document.getElementById('tab-title');
  const tabSubtitle = document.getElementById('tab-subtitle');

  const tabMeta = {
    overview: {
      title: "Overview Dashboard",
      subtitle: "Key fiscal statistics and trends of the last decade"
    },
    analyzer: {
      title: "Ministry Outlay Analyzer",
      subtitle: "Inspect historical spending and budget share for specific ministries"
    },
    yearly: {
      title: "Yearly Breakdown",
      subtitle: "Detailed spending distribution for any selected fiscal year"
    },
    compare: {
      title: "Year-on-Year Share Comparison",
      subtitle: "Compare budget allocation pie charts side-by-side"
    },
    'table-view': {
      title: "Detailed Budget Ledger",
      subtitle: "Search, sort, and export the entire budget historical table"
    }
  };

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const targetTab = item.getAttribute('data-tab');
      
      // Update Navbar State
      navItems.forEach(btn => btn.classList.remove('active'));
      item.classList.add('active');

      // Update Panel Visibility
      tabPanes.forEach(pane => pane.classList.remove('active'));
      const activePane = document.getElementById(targetTab);
      if (activePane) activePane.classList.add('active');

      // Update Titles
      if (tabMeta[targetTab]) {
        tabTitle.textContent = tabMeta[targetTab].title;
        tabSubtitle.textContent = tabMeta[targetTab].subtitle;
      }

      // Trigger respective tab renders
      destroyCharts();
      if (targetTab === 'overview') renderOverviewTab();
      else if (targetTab === 'analyzer') renderAnalyzerTab();
      else if (targetTab === 'yearly') renderYearlyTab();
      else if (targetTab === 'compare') renderCompareTab();
      else if (targetTab === 'table-view') renderTableTab();
    });
  });
  
  // Initialize Lucide Icons
  lucide.createIcons();
}

// Dropdowns Setup
function populateDropdowns() {
  const minSelect = document.getElementById('ministry-select');
  const yearSelect = document.getElementById('year-select');
  const compYearA = document.getElementById('compare-year-a');
  const compYearB = document.getElementById('compare-year-b');

  // Fill Ministries
  minSelect.innerHTML = '';
  budgetData.ministries.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m.key;
    opt.textContent = m.name;
    minSelect.appendChild(opt);
  });

  // Fill Years
  const createYearOptions = (selectEl, defaultVal) => {
    selectEl.innerHTML = '';
    budgetData.years.forEach(year => {
      const opt = document.createElement('option');
      opt.value = year;
      opt.textContent = year;
      if (year === defaultVal) opt.selected = true;
      selectEl.appendChild(opt);
    });
  };

  createYearOptions(yearSelect, "2025-26");
  createYearOptions(compYearA, "2013-14");
  createYearOptions(compYearB, "2025-26");
}

function setupEventListeners() {
  // Ministry select dropdown listener
  document.getElementById('ministry-select').addEventListener('change', () => {
    renderAnalyzerTab();
  });

  // Year select dropdown listener
  document.getElementById('year-select').addEventListener('change', () => {
    renderYearlyTab();
  });

  // Comparison select dropdown listeners
  document.getElementById('compare-year-a').addEventListener('change', () => {
    renderCompareTab();
  });
  document.getElementById('compare-year-b').addEventListener('change', () => {
    renderCompareTab();
  });

  // Table search text listener
  document.getElementById('table-search').addEventListener('input', () => {
    renderTableRows();
  });

  // Table export CSV listener
  document.getElementById('btn-export-csv').addEventListener('click', () => {
    exportCSV();
  });

  // Table header sorting listeners
  const sortableHeaders = document.querySelectorAll('.data-table th.sortable');
  sortableHeaders.forEach(th => {
    th.addEventListener('click', () => {
      const sortKey = th.getAttribute('data-sort');
      if (tableSort.key === sortKey) {
        tableSort.asc = !tableSort.asc;
      } else {
        tableSort.key = sortKey;
        tableSort.asc = true;
      }
      
      // Update indicator arrows
      sortableHeaders.forEach(el => {
        const icon = el.querySelector('i');
        icon.setAttribute('data-lucide', 'chevrons-up-down');
      });
      const currentIcon = th.querySelector('i');
      currentIcon.setAttribute('data-lucide', tableSort.asc ? 'chevron-up' : 'chevron-down');
      lucide.createIcons();

      // Sort and render
      renderTableRows();
    });
  });
}

// Chart Destroyer Helper
function destroyCharts() {
  Object.keys(activeCharts).forEach(chartKey => {
    if (activeCharts[chartKey]) {
      activeCharts[chartKey].destroy();
      activeCharts[chartKey] = null;
    }
  });
}

// ==========================================
// DATA COMPUTATION UTILITIES
// ==========================================
function getYearTotalOutlay(year) {
  let total = 0;
  budgetData.ministries.forEach(m => {
    total += m.history[year] || 0;
  });
  return total;
}

function getMinistryOutlay(mKey, year) {
  const m = budgetData.ministries.find(item => item.key === mKey);
  return m ? (m.history[year] || 0) : 0;
}

function getMinistryAvgOutlay(mKey) {
  const m = budgetData.ministries.find(item => item.key === mKey);
  if (!m) return 0;
  let sum = 0;
  budgetData.years.forEach(y => {
    sum += m.history[y] || 0;
  });
  return sum / budgetData.years.length;
}

// ==========================================
// RENDER MODULES
// ==========================================

/* ------------------------------------------
   1. OVERVIEW TAB
------------------------------------------ */
function renderOverviewTab() {
  const latestYear = budgetData.years[budgetData.years.length - 1]; // "2025-26"
  const prevYear = budgetData.years[budgetData.years.length - 2];  // "2024-25"

  // Consolidated Year Budgets
  const latestTotal = getYearTotalOutlay(latestYear);
  const prevTotal = getYearTotalOutlay(prevYear);

  // Stats Card 1: Latest Outlay & YoY
  const outlayDiff = latestTotal - prevTotal;
  const outlayGrowthPercent = prevTotal > 0 ? (outlayDiff / prevTotal) * 100 : 0;
  
  document.getElementById('outlay-val').textContent = `₹${latestTotal.toLocaleString('en-IN', {maximumFractionDigits:2})} Cr`;
  const trendEl = document.getElementById('outlay-trend');
  if (outlayGrowthPercent >= 0) {
    trendEl.className = "trend positive";
    trendEl.innerHTML = `<i data-lucide="arrow-up-right"></i> +${outlayGrowthPercent.toFixed(2)}% (YoY)`;
  } else {
    trendEl.className = "trend negative";
    trendEl.innerHTML = `<i data-lucide="arrow-down-right"></i> ${outlayGrowthPercent.toFixed(2)}% (YoY)`;
  }

  // Stats Card 2: 13-Year Avg
  let sumOutlays = 0;
  budgetData.years.forEach(y => {
    sumOutlays += getYearTotalOutlay(y);
  });
  const avgOutlay = sumOutlays / budgetData.years.length;
  document.getElementById('avg-outlay-val').textContent = `₹${avgOutlay.toLocaleString('en-IN', {maximumFractionDigits:2})} Cr`;

  // Stats Card 3: Top Sector (2025-26)
  let topMinistry = "";
  let maxVal = -1;
  budgetData.ministries.forEach(m => {
    const val = m.history[latestYear] || 0;
    if (val > maxVal) {
      maxVal = val;
      topMinistry = m.name;
    }
  });
  const topPct = latestTotal > 0 ? (maxVal / latestTotal) * 100 : 0;
  
  document.getElementById('top-ministry-val').textContent = topMinistry.split(' & ')[0].split(' / ')[0];
  document.getElementById('top-ministry-percent').textContent = `${topPct.toFixed(1)}% of total outlay (₹${maxVal.toLocaleString('en-IN')} Cr)`;

  // Update Icons in cards
  lucide.createIcons();

  // Draw Line trend chart
  const trendCtx = document.getElementById('overviewTrendChart').getContext('2d');
  const lineLabels = budgetData.years;
  const lineData = budgetData.years.map(y => getYearTotalOutlay(y));

  const gradient = trendCtx.createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, hexToRgba(CHART_COLORS[0], 0.4));
  gradient.addColorStop(1, hexToRgba(CHART_COLORS[0], 0.0));

  activeCharts.overviewTrend = new Chart(trendCtx, {
    type: 'line',
    data: {
      labels: lineLabels,
      datasets: [{
        label: 'Consolidated Outlay',
        data: lineData,
        borderColor: CHART_COLORS[0],
        borderWidth: 3,
        backgroundColor: gradient,
        fill: true,
        tension: 0.35,
        pointBackgroundColor: CHART_COLORS[0],
        pointHoverRadius: 6,
        pointHoverBackgroundColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#110e25',
          titleColor: '#fff',
          bodyColor: '#a55eea',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: (ctx) => ` Outlay: ₹${ctx.parsed.y.toLocaleString('en-IN')} Cr`
          }
        }
      },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.03)' }, ticks: { color: '#958eb6' } },
        y: { 
          grid: { color: 'rgba(255,255,255,0.03)' }, 
          ticks: { 
            color: '#958eb6',
            callback: (val) => `₹${(val / 100000).toFixed(1)}L Cr` // Format in Lakh Crores
          } 
        }
      }
    }
  });

  // Draw Share Donut Chart (2025-26)
  const shareCtx = document.getElementById('overviewShareChart').getContext('2d');
  const donutLabels = budgetData.ministries.map(m => m.name.split(' & ')[0].split(' / ')[0]);
  const donutData = budgetData.ministries.map(m => m.history[latestYear] || 0);

  activeCharts.overviewShare = new Chart(shareCtx, {
    type: 'doughnut',
    data: {
      labels: donutLabels,
      datasets: [{
        data: donutData,
        backgroundColor: CHART_COLORS,
        borderColor: 'rgba(8, 6, 17, 0.8)',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#110e25',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: (ctx) => {
              const val = ctx.parsed;
              const pct = (val / latestTotal) * 100;
              return ` Outlay: ₹${val.toLocaleString('en-IN')} Cr (${pct.toFixed(1)}%)`;
            }
          }
        }
      },
      cutout: '65%'
    }
  });
}

/* ------------------------------------------
   2. MINISTRY ANALYZER TAB
------------------------------------------ */
function renderAnalyzerTab() {
  const mKey = document.getElementById('ministry-select').value;
  const m = budgetData.ministries.find(item => item.key === mKey);
  if (!m) return;

  // Title update
  document.getElementById('analyzer-chart-title').textContent = `${m.name} Outlay Progression`;

  // Calculated Stats
  // 1. Avg Outlay
  const avg = getMinistryAvgOutlay(mKey);
  document.getElementById('m-avg-val').textContent = `₹${avg.toLocaleString('en-IN', {maximumFractionDigits:2})} Cr`;

  // 2. Peak Year
  let peakYear = "";
  let peakVal = -1;
  budgetData.years.forEach(y => {
    const val = m.history[y] || 0;
    if (val > peakVal) {
      peakVal = val;
      peakYear = y;
    }
  });
  document.getElementById('m-peak-val').textContent = `₹${peakVal.toLocaleString('en-IN')} Cr`;
  document.getElementById('m-peak-year').textContent = `Achieved in ${peakYear}`;

  // 3. Growth rate since 2013-14
  const val2013 = m.history['2013-14'] || 0;
  const val2025 = m.history['2025-26'] || 0;
  const diff = val2025 - val2013;
  const growthPercent = val2013 > 0 ? (diff / val2013) * 100 : 0;
  document.getElementById('m-growth-val').textContent = `${growthPercent >= 0 ? '+' : ''}${growthPercent.toFixed(1)}%`;

  // 4. Avg Share of budget
  let totalShareSum = 0;
  budgetData.years.forEach(y => {
    const totalOutlay = getYearTotalOutlay(y);
    const mVal = m.history[y] || 0;
    if (totalOutlay > 0) {
      totalShareSum += (mVal / totalOutlay) * 100;
    }
  });
  const avgShare = totalShareSum / budgetData.years.length;
  document.getElementById('m-share-val').textContent = `${avgShare.toFixed(2)}%`;

  // Charts data
  const lineLabels = budgetData.years;
  const lineData = budgetData.years.map(y => m.history[y] || 0);
  
  // Calculate YoY growth rate list
  const yoyGrowthData = budgetData.years.map((y, idx) => {
    if (idx === 0) return 0;
    const prevVal = m.history[budgetData.years[idx - 1]] || 0;
    const curVal = m.history[y] || 0;
    if (prevVal === 0) return 0;
    return ((curVal - prevVal) / prevVal) * 100;
  });

  const trendCtx = document.getElementById('ministryTrendChart').getContext('2d');
  
  activeCharts.ministryTrend = new Chart(trendCtx, {
    type: 'bar',
    data: {
      labels: lineLabels,
      datasets: [
        {
          type: 'bar',
          label: 'Outlay (₹ Cr)',
          data: lineData,
          backgroundColor: hexToRgba(CHART_COLORS[2], 0.6),
          borderColor: CHART_COLORS[2],
          borderWidth: 1.5,
          yAxisID: 'y'
        },
        {
          type: 'line',
          label: 'YoY Growth (%)',
          data: yoyGrowthData,
          borderColor: CHART_COLORS[4],
          borderWidth: 2.5,
          tension: 0.3,
          fill: false,
          pointBackgroundColor: CHART_COLORS[4],
          pointRadius: 4,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { boxWidth: 12 } },
        tooltip: {
          backgroundColor: '#110e25',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: (ctx) => {
              if (ctx.datasetIndex === 0) {
                return ` Outlay: ₹${ctx.parsed.y.toLocaleString('en-IN')} Cr`;
              } else {
                return ` YoY Growth: ${ctx.parsed.y.toFixed(2)}%`;
              }
            }
          }
        }
      },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.03)' } },
        y: {
          type: 'linear',
          position: 'left',
          grid: { color: 'rgba(255,255,255,0.03)' },
          title: { display: true, text: 'Outlay (₹ Crores)', color: '#958eb6' }
        },
        y1: {
          type: 'linear',
          position: 'right',
          grid: { drawOnChartArea: false }, // Only show grid of left axis
          title: { display: true, text: 'Growth (%)', color: '#958eb6' },
          ticks: {
            callback: (val) => `${val}%`
          }
        }
      }
    }
  });

  // Draw average share comparison pie chart
  // This pie chart compares the selected ministry's average outlay vs all other ministries combined average outlay
  const shareCtx = document.getElementById('ministryShareChart').getContext('2d');
  
  let allOthersAvg = 0;
  budgetData.ministries.forEach(item => {
    if (item.key !== mKey) {
      allOthersAvg += getMinistryAvgOutlay(item.key);
    }
  });

  activeCharts.ministryShare = new Chart(shareCtx, {
    type: 'pie',
    data: {
      labels: [m.name.split(' & ')[0].split(' / ')[0], 'All Other Sectors'],
      datasets: [{
        data: [avg, allOthersAvg],
        backgroundColor: [CHART_COLORS[1], 'rgba(255, 255, 255, 0.05)'],
        borderColor: ['#fff', varColorBorder()],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { boxWidth: 12 } },
        tooltip: {
          backgroundColor: '#110e25',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: (ctx) => {
              const val = ctx.parsed;
              const pct = (val / (avg + allOthersAvg)) * 100;
              return ` Avg Outlay: ₹${val.toLocaleString('en-IN', {maximumFractionDigits:0})} Cr (${pct.toFixed(2)}%)`;
            }
          }
        }
      }
    }
  });
}

function varColorBorder() {
  return 'rgba(255, 255, 255, 0.06)';
}

/* ------------------------------------------
   3. YEARLY BREAKDOWN TAB
------------------------------------------ */
function renderYearlyTab() {
  const selectedYear = document.getElementById('year-select').value;
  
  // Title update
  document.getElementById('yearly-chart-title').textContent = `${selectedYear} Outlay Distribution`;
  document.getElementById('yearly-insights-sub').textContent = `Specific insight stats for ${selectedYear}`;

  const yearTotal = getYearTotalOutlay(selectedYear);
  document.getElementById('year-total-outlay').textContent = `₹${yearTotal.toLocaleString('en-IN', {maximumFractionDigits:2})} Cr`;

  // Calculate YoY budget expansion
  const yearIdx = budgetData.years.indexOf(selectedYear);
  const growthRateEl = document.getElementById('year-growth-rate');
  if (yearIdx === 0) {
    growthRateEl.textContent = 'N/A';
  } else {
    const prevYear = budgetData.years[yearIdx - 1];
    const prevTotal = getYearTotalOutlay(prevYear);
    const growth = ((yearTotal - prevTotal) / prevTotal) * 100;
    growthRateEl.textContent = `${growth >= 0 ? '+' : ''}${growth.toFixed(2)}% (YoY)`;
    growthRateEl.className = growth >= 0 ? 'accent-text' : 'shift-down';
  }

  // Draw Pie chart
  const pieCtx = document.getElementById('yearlyPieChart').getContext('2d');
  const pieLabels = budgetData.ministries.map(m => m.name.split(' & ')[0].split(' / ')[0]);
  const pieData = budgetData.ministries.map(m => m.history[selectedYear] || 0);

  activeCharts.yearlyPie = new Chart(pieCtx, {
    type: 'doughnut',
    data: {
      labels: pieLabels,
      datasets: [{
        data: pieData,
        backgroundColor: CHART_COLORS,
        borderColor: 'rgba(8, 6, 17, 0.8)',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#110e25',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: (ctx) => {
              const val = ctx.parsed;
              const pct = (val / yearTotal) * 100;
              return ` Outlay: ₹${val.toLocaleString('en-IN')} Cr (${pct.toFixed(2)}%)`;
            }
          }
        }
      },
      cutout: '55%'
    }
  });

  // Render Top 3 list items
  const sortedMinistries = budgetData.ministries.map(m => {
    return { name: m.name, value: m.history[selectedYear] || 0 };
  }).sort((a, b) => b.value - a.value);

  const topListEl = document.getElementById('yearly-top-list');
  topListEl.innerHTML = '';
  
  for (let i = 0; i < 3; i++) {
    const m = sortedMinistries[i];
    const pct = yearTotal > 0 ? (m.value / yearTotal) * 100 : 0;
    
    const li = document.createElement('li');
    li.innerHTML = `
      <span class="rank">#${i+1}</span>
      <span class="name">${m.name.split(' & ')[0].split(' / ')[0]}</span>
      <span class="val">₹${m.value.toLocaleString('en-IN')} Cr</span>
      <span class="pct">${pct.toFixed(1)}%</span>
    `;
    topListEl.appendChild(li);
  }
}

/* ------------------------------------------
   4. BUDGET SHARE COMPARISON TAB
------------------------------------------ */
function renderCompareTab() {
  const yearA = document.getElementById('compare-year-a').value;
  const yearB = document.getElementById('compare-year-b').value;

  // Update chart header titles
  document.getElementById('compare-title-a').textContent = `Outlay Distribution: ${yearA}`;
  document.getElementById('compare-title-b').textContent = `Outlay Distribution: ${yearB}`;

  const totalA = getYearTotalOutlay(yearA);
  const totalB = getYearTotalOutlay(yearB);

  // Draw Pie chart A
  const drawPieCompare = (canvasId, year, total, chartKey) => {
    const ctx = document.getElementById(canvasId).getContext('2d');
    const labels = budgetData.ministries.map(m => m.name.split(' & ')[0].split(' / ')[0]);
    const data = budgetData.ministries.map(m => m.history[year] || 0);

    activeCharts[chartKey] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: CHART_COLORS,
          borderColor: 'rgba(8, 6, 17, 0.8)',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#110e25',
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
            padding: 12,
            callbacks: {
              label: (ctx) => {
                const val = ctx.parsed;
                const pct = (val / total) * 100;
                return ` Outlay: ₹${val.toLocaleString('en-IN')} Cr (${pct.toFixed(2)}%)`;
              }
            }
          }
        },
        cutout: '60%'
      }
    });
  };

  drawPieCompare('comparePieChartA', yearA, totalA, 'comparePieA');
  drawPieCompare('comparePieChartB', yearB, totalB, 'comparePieB');

  // Render Table Comparison rows
  const tbody = document.getElementById('compare-table-body');
  tbody.innerHTML = '';

  budgetData.ministries.forEach(m => {
    const valA = m.history[yearA] || 0;
    const valB = m.history[yearB] || 0;
    const shareA = totalA > 0 ? (valA / totalA) * 100 : 0;
    const shareB = totalB > 0 ? (valB / totalB) * 100 : 0;

    const absDiff = valB - valA;
    const pctDiff = valA > 0 ? (absDiff / valA) * 100 : 0;
    const shareShift = shareB - shareA;

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="bold-value">${m.name}</td>
      <td class="text-right">₹${valA.toLocaleString('en-IN', {maximumFractionDigits:2})} Cr</td>
      <td class="text-right">₹${valB.toLocaleString('en-IN', {maximumFractionDigits:2})} Cr</td>
      <td class="text-right ${absDiff >= 0 ? 'shift-up' : 'shift-down'}">${absDiff >= 0 ? '+' : ''}₹${absDiff.toLocaleString('en-IN', {maximumFractionDigits:2})} Cr</td>
      <td class="text-right">${valA > 0 ? `${pctDiff >= 0 ? '+' : ''}${pctDiff.toFixed(2)}%` : 'N/A'}</td>
      <td class="text-right ${shareShift >= 0 ? 'shift-up' : 'shift-down'}">${shareShift >= 0 ? '+' : ''}${shareShift.toFixed(2)}%</td>
    `;
    tbody.appendChild(tr);
  });
}

/* ------------------------------------------
   5. DATA TABLE TAB
------------------------------------------ */
function renderTableTab() {
  renderTableRows();
}

function renderTableRows() {
  const tbody = document.getElementById('table-body');
  tbody.innerHTML = '';

  // Get search criteria
  const query = document.getElementById('table-search').value.toLowerCase().trim();

  // Filter
  let filtered = tableData.filter(row => {
    return row.ministry.toLowerCase().includes(query) || row.year.toLowerCase().includes(query);
  });

  // Sort
  filtered.sort((a, b) => {
    let compA = a[tableSort.key];
    let compB = b[tableSort.key];

    if (typeof compA === 'string') {
      return tableSort.asc ? compA.localeCompare(compB) : compB.localeCompare(compA);
    } else {
      return tableSort.asc ? compA - compB : compB - compA;
    }
  });

  // Render rows
  filtered.forEach(row => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="bold-value">${row.ministry}</td>
      <td>${row.year}</td>
      <td class="text-right">₹${row.outlay.toLocaleString('en-IN', {maximumFractionDigits:2})} Cr</td>
      <td class="text-right">${row.share.toFixed(2)}%</td>
    `;
    tbody.appendChild(tr);
  });
}

// CSV Exporter
function exportCSV() {
  let csvContent = "data:text/csv;charset=utf-8,";
  csvContent += "Ministry,Year,Outlay (in Crores),Share of Year Budget (%)\n";

  tableData.forEach(row => {
    // Escape commas in names
    const mName = `"${row.ministry.replace(/"/g, '""')}"`;
    csvContent += `${mName},${row.year},${row.outlay.toFixed(2)},${row.share.toFixed(2)}\n`;
  });

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", "union_budget_india_2013_2026.csv");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
