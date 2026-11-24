/**
 * Interactive Charts Module for Embodied Carbon Dashboard.
 * Integrates Chart.js with responsive sizing and engineering themes.
 */

class DashboardCharts {
  constructor() {
    this.chartInstances = {};
  }

  destroyChart(id) {
    if (this.chartInstances[id]) {
      this.chartInstances[id].destroy();
      delete this.chartInstances[id];
    }
  }

  // 1. Cumulative Carbon Trend (Planned S-Curve vs Actual Logged vs Projected)
  renderCumulativeTrend(canvasId, timelineData, carbonBudgetTonnes) {
    this.destroyChart(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const stages = timelineData.stages || [];
    const labels = stages.map(s => `${s.stage_name} (${s.date})`);
    const plannedData = stages.map(s => s.planned_cumulative_carbon_t);
    const actualData = stages.map(s => s.actual_cumulative_carbon_t);
    const projectedData = stages.map(s => s.projected_cumulative_carbon_t);

    this.chartInstances[canvasId] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Planned Budget S-Curve (tCO2e)',
            data: plannedData,
            borderColor: '#94a3b8',
            backgroundColor: 'rgba(148, 163, 184, 0.1)',
            borderDash: [5, 5],
            fill: false,
            tension: 0.3,
            pointRadius: 4
          },
          {
            label: 'Actual Cumulative Logged (tCO2e)',
            data: actualData,
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.15)',
            fill: true,
            tension: 0.2,
            pointRadius: 6,
            pointBackgroundColor: '#2563eb'
          },
          {
            label: 'Projected to Completion (tCO2e)',
            data: projectedData,
            borderColor: '#f59e0b',
            borderDash: [3, 3],
            fill: false,
            tension: 0.2,
            pointRadius: 5,
            pointBackgroundColor: '#f59e0b'
          }
        ]
      },
      options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
          tooltip: {
            callbacks: {
              label: (context) => {
                const val = (context.raw != null && !isNaN(context.raw)) ? Number(context.raw).toFixed(2) + ' tCO2e' : 'N/A';
                return `${context.dataset.label}: ${val}`;
              }
            }
          }
        },
        scales: {
          y: {
            title: { display: true, text: 'Cumulative Carbon (tCO2e)', font: { size: 11, weight: 'bold' } },
            grid: { color: '#f1f5f9' },
            beginAtZero: true
          },
          x: {
            grid: { display: false },
            ticks: { font: { size: 10 }, maxRotation: 25 }
          }
        }
      }
    });
  }

  // 2. EN 15978 Life Cycle Stage Breakdown (Donut Chart)
  renderStageBreakdown(canvasId, stageBreakdown) {
    this.destroyChart(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const labels = stageBreakdown.map(s => `${s.module}: ${s.label}`);
    const data = stageBreakdown.map(s => s.emissions_tonnes);
    const colors = stageBreakdown.map(s => s.color);

    this.chartInstances[canvasId] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } },
          tooltip: {
            callbacks: {
              label: (context) => {
                const total = context.dataset.data.reduce((a, b) => a + (Number(b) || 0), 0);
                const raw = Number(context.raw) || 0;
                const pct = total > 0 ? ((raw / total) * 100).toFixed(1) : '0.0';
                return ` ${context.label}: ${raw.toFixed(2)} tCO2e (${pct}%)`;
              }
            }
          }
        }
      }
    });
  }

  // 3. Material Carbon Hotspot Pareto (Bar Chart)
  renderMaterialHotspots(canvasId, materialsItems) {
    this.destroyChart(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const topItems = (materialsItems || []).slice(0, 6);
    const labels = topItems.map(m => m.material_name.length > 22 ? m.material_name.substring(0, 20) + '...' : m.material_name);
    const emissions = topItems.map(m => m.carbon_emission_tonnes);

    // Color gradient: cement & steel are distinct highlights
    const bgColors = topItems.map(m => {
      const cat = (m.category || '').toLowerCase();
      if (cat.includes('cement')) return '#ef4444'; // Red hotspot
      if (cat.includes('reinforce') || cat.includes('steel')) return '#f97316'; // Orange
      if (cat.includes('scm')) return '#10b981'; // Green SCM
      return '#3b82f6'; // Aggregates / general
    });

    this.chartInstances[canvasId] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Embodied Carbon (tCO2e)',
          data: emissions,
          backgroundColor: bgColors,
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => ` Carbon: ${(Number(ctx.raw) || 0).toFixed(3)} tCO2e`
            }
          }
        },
        scales: {
          y: {
            title: { display: true, text: 'Emissions (tCO2e)', font: { size: 11 } },
            beginAtZero: true,
            grid: { color: '#f1f5f9' }
          },
          x: {
            ticks: { font: { size: 10 }, maxRotation: 20 },
            grid: { display: false }
          }
        }
      }
    });
  }

  // 4. Planned vs Actual Material Consumption
  renderPlannedVsActual(canvasId, materialsItems) {
    this.destroyChart(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const topItems = (materialsItems || []).slice(0, 5);
    const labels = topItems.map(m => m.material_name.length > 18 ? m.material_name.substring(0, 16) + '..' : m.material_name);
    const plannedCarbon = topItems.map(m => m.planned_carbon_kg / 1000.0);
    const actualCarbon = topItems.map(m => m.carbon_emission_tonnes);

    this.chartInstances[canvasId] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Planned Design Carbon (tCO2e)',
            data: plannedCarbon,
            backgroundColor: '#94a3b8',
            borderRadius: 4
          },
          {
            label: 'Actual Consumed Carbon (tCO2e)',
            data: actualCarbon,
            backgroundColor: '#2563eb',
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } }
        },
        scales: {
          y: {
            title: { display: true, text: 'Carbon (tCO2e)', font: { size: 11 } },
            beginAtZero: true,
            grid: { color: '#f1f5f9' }
          },
          x: {
            ticks: { font: { size: 10 } },
            grid: { display: false }
          }
        }
      }
    });
  }

  // 5. Benchmark Comparison Chart (Horizontal Bar)
  renderBenchmarkComparison(canvasId, benchmarksData, actualIntensity) {
    this.destroyChart(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const comps = benchmarksData.benchmark_comparisons || [];
    const labels = ['Your Project Mix', ...comps.map(c => c.name)];
    const values = [actualIntensity, ...comps.map(c => c.benchmark_intensity)];
    const colors = ['#2563eb', '#dc2626', '#16a34a', '#059669', '#d97706'];

    this.chartInstances[canvasId] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Carbon Intensity (kgCO2e/m³)',
          data: values,
          backgroundColor: colors,
          borderRadius: 4
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (c) => ` Intensity: ${(Number(c.raw) || 0).toFixed(1)} kgCO2e/m³`
            }
          }
        },
        scales: {
          x: {
            title: { display: true, text: 'kgCO2e / m³ concrete', font: { size: 11 } },
            beginAtZero: true,
            grid: { color: '#f1f5f9' }
          },
          y: {
            ticks: { font: { size: 11, weight: 'bold' } },
            grid: { display: false }
          }
        }
      }
    });
  }
}

window.DashboardCharts = DashboardCharts;
