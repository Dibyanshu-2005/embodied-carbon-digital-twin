/**
 * Main Client Application Controller for Concrete Embodied Carbon Digital Twin.
 * Purpose-built for Construction Project Managers with continuous periodic tracking
 * and central verified emission factor repository [1]–[6].
 */

let appState = null;
let charts = null;
let selectedStageId = null;
let emissionCatalog = null;
let lastSimResult = null;

// Safe number formatting helper to prevent any "Cannot read properties of undefined (reading 'toFixed')"
function fmt(val, dec = 2, fallback = '0.00') {
  if (val === null || val === undefined) return fallback;
  const num = Number(val);
  return (!isNaN(num) && isFinite(num)) ? num.toFixed(dec) : fallback;
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initCharts();
  initEventListeners();
  initModalEventListeners();
  initOcrPhotoIngestion();
  loadEmissionCatalog();
  loadProjectData();
});

function initTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      
      tab.classList.add('active');
      const targetId = tab.getAttribute('data-target');
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add('active');
        setTimeout(() => refreshAllCharts(), 40);
      }
    });
  });
}

function initCharts() {
  charts = new DashboardCharts();
}

function initEventListeners() {
  // Reset demo data button
  const btnReset = document.getElementById('btnResetDemo');
  if (btnReset) {
    btnReset.addEventListener('click', async () => {
      if (confirm('Reset Digital Twin to default demo dataset?')) {
        await resetDemoData();
      }
    });
  }

  // Project Baseline & Targets Modal Trigger
  const btnBaseline = document.getElementById('btnOpenBaselineModal');
  if (btnBaseline) {
    btnBaseline.addEventListener('click', () => {
      openBaselineModal();
    });
  }

  const btnSaveBase = document.getElementById('btnSaveBaseline');
  if (btnSaveBase) {
    btnSaveBase.addEventListener('click', async () => {
      await saveProjectBaseline();
    });
  }

  // Redirect button from detail view to Library tab
  const btnGoLibrary = document.getElementById('btnGoToLibraryTab');
  if (btnGoLibrary) {
    btnGoLibrary.addEventListener('click', () => {
      const libTabBtn = document.querySelector('.tab-btn[data-target="tab-library"]');
      if (libTabBtn) libTabBtn.click();
    });
  }

  // File Upload Dropzone
  const dropzone = document.getElementById('uploadDropzone');
  const fileInput = document.getElementById('fileInput');

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files.length > 0) {
        handleFileUpload(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
      }
    });
  }

  // Chart Sub-View Toggles (Pareto Hotspots, Planned vs Actual, A1-A5 Stages)
  const btnHotspots = document.getElementById('btnShowHotspots');
  const btnVariance = document.getElementById('btnShowVariance');
  const btnStages = document.getElementById('btnShowStages');

  const viewHotspots = document.getElementById('viewHotspots');
  const viewVariance = document.getElementById('viewVariance');
  const viewStages = document.getElementById('viewStages');

  const switchAnalyticsView = (activeBtn, activeView) => {
    [btnHotspots, btnVariance, btnStages].forEach(b => { if (b) b.classList.remove('active'); });
    [viewHotspots, viewVariance, viewStages].forEach(v => { if (v) v.style.display = 'none'; });
    if (activeBtn) activeBtn.classList.add('active');
    if (activeView) {
      activeView.style.display = 'block';
      if (!charts || !appState) return;
      if (activeBtn === btnHotspots) {
        charts.renderMaterialHotspots('chartHotspots', appState.summary.materials_module.items);
      } else if (activeBtn === btnVariance) {
        charts.renderPlannedVsActual('chartPlannedVsActual', appState.summary.materials_module.items);
      } else if (activeBtn === btnStages) {
        charts.renderStageBreakdown('chartStageBreakdown', appState.summary.stage_breakdown);
      }
    }
  };

  if (btnHotspots) btnHotspots.addEventListener('click', () => switchAnalyticsView(btnHotspots, viewHotspots));
  if (btnVariance) btnVariance.addEventListener('click', () => switchAnalyticsView(btnVariance, viewVariance));
  if (btnStages) btnStages.addEventListener('click', () => switchAnalyticsView(btnStages, viewStages));
}

// Modal open/close helpers
window.openModal = function(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('active');
};

window.closeModal = function(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('active');
};

window.openEmissionCatalogModal = function() {
  openModal('modalEmissionCatalogOverlay');
};

// Site Ingestion Master-Detail View Switching
window.changeStageStatus = async function(stageId, newStatus) {
  try {
    const res = await fetch('/api/stages/update-status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stage_id: stageId, status: newStatus })
    });
    const data = await res.json();
    if (data.success) {
      appState = data.project_state;
      updateUI(appState);
      const statusSelect = document.getElementById('activeLogStatusSelect');
      if (statusSelect && selectedStageId === stageId) {
        statusSelect.value = newStatus;
      }
      showToast(`Updated Log #${stageId} to ${newStatus}`, 'success');
    } else {
      showToast(data.error || 'Failed to update status', 'error');
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
};

window.openStageDetail = async function(stageId) {
  selectedStageId = stageId;
  const stages = appState && appState.stages ? appState.stages : (appState && appState.timeline ? appState.timeline.stages : []);
  const stg = stages.find(s => s.stage_id === stageId) || stages[0];
  if (!stg) return;

  const titleEl = document.getElementById('activeLogTitle');
  const metaEl = document.getElementById('activeLogMeta');
  const statusSelect = document.getElementById('activeLogStatusSelect');

  if (titleEl) titleEl.textContent = `Log #${stg.stage_id}: ${stg.name || stg.stage_name}`;
  if (metaEl) {
    metaEl.textContent = `Date: ${stg.date} | Log ID: #${stg.stage_id}`;
  }
  if (statusSelect) {
    statusSelect.value = stg.status || 'Scheduled';
    statusSelect.onchange = async () => {
      await changeStageStatus(stg.stage_id, statusSelect.value);
    };
  }

  // Switch active stage on backend to keep server state in sync
  try {
    const res = await fetch('/api/stages/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stage_id: stageId })
    });
    const data = await res.json();
    if (data.success) {
      appState = data.project_state;
      updateUI(appState);
    }
  } catch (err) {
    console.error('Error switching active stage:', err);
  }

  const listView = document.getElementById('viewSiteIngestionList');
  const detailView = document.getElementById('viewSiteIngestionDetail');
  if (listView) listView.style.display = 'none';
  if (detailView) {
    detailView.style.display = 'block';
    detailView.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
};

window.returnToLogList = function() {
  const listView = document.getElementById('viewSiteIngestionList');
  const detailView = document.getElementById('viewSiteIngestionDetail');
  if (detailView) detailView.style.display = 'none';
  if (listView) listView.style.display = 'block';
};

// Central Emission Factor Catalog Loading & Dropdown Management
async function loadEmissionCatalog() {
  try {
    const res = await fetch('/api/emission-factors');
    if (!res.ok) throw new Error('Failed to load emission database');
    emissionCatalog = await res.json();
    populateCatalogModal(emissionCatalog);
    populateAddMaterialDropdowns();
    populateAddTransportDropdowns();
    populateAddEquipmentDropdowns();
  } catch (err) {
    console.error('Error loading emission factor catalog:', err);
  }
}

function populateCatalogModal(catalog) {
  if (!catalog) return;
  // 1. Sources Index Footnotes [1]–[6]
  const sourcesContainer = document.getElementById('catalogSourcesList');
  if (sourcesContainer && catalog.sources) {
    sourcesContainer.innerHTML = '';
    catalog.sources.forEach(src => {
      const div = document.createElement('div');
      div.style.padding = '8px 10px';
      div.style.background = '#ffffff';
      div.style.border = '1px solid #e2e8f0';
      div.style.borderRadius = '6px';
      div.innerHTML = `
        <div style="display:flex; align-items:center; gap:6px; margin-bottom:2px;">
          <span class="source-pill">${src.code}</span>
          <strong style="color:#0f172a;">${src.title}</strong>
        </div>
        <div style="color:#64748b; font-size:10px;">${src.organization}</div>
        <div style="color:#475569; font-size:11px; margin-top:2px;">${src.description}</div>
      `;
      sourcesContainer.appendChild(div);
    });
  }

  // 2. Master Table Items with Search Filter
  renderCatalogTable(catalog, '');
  const searchInput = document.getElementById('catalogSearchInput');
  if (searchInput) {
    searchInput.oninput = (e) => renderCatalogTable(catalog, e.target.value);
  }
}

function renderCatalogTable(catalog, filterQuery = '') {
  const catalogTbody = document.getElementById('catalogTableBody');
  if (!catalogTbody || !catalog) return;
  catalogTbody.innerHTML = '';
  const q = (filterQuery || '').toLowerCase().trim();

  // Combine items
  const allItems = [
    ...(catalog.materials || []).map(m => ({ ...m, type: 'Material', badgeClass: 'badge-blue' })),
    ...(catalog.transport || []).map(t => ({ ...t, type: 'Transport (A4)', category: 'Transport (A4)', badgeClass: 'badge-green', unit: 't·km' })),
    ...(catalog.equipment || []).map(eq => ({ ...eq, type: 'Equipment (A5a)', category: 'Equipment (A5a)', badgeClass: 'badge-amber', description: `Fuel: ${eq.fuel_type}` }))
  ];

  const filtered = q ? allItems.filter(item => 
    (item.name || '').toLowerCase().includes(q) || 
    (item.category || '').toLowerCase().includes(q) ||
    (item.description || '').toLowerCase().includes(q)
  ) : allItems;

  filtered.forEach(item => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${item.name}</strong><br><span style="font-size:10px; color:#64748b;">${item.description || ''}</span></td>
      <td><span class="kpi-badge ${item.badgeClass || 'badge-blue'}">${item.category}</span></td>
      <td style="font-weight:700; color:#0f172a;">${fmt(item.emission_factor, 4)}</td>
      <td>kgCO2e / ${item.unit}</td>
      <td><span class="source-pill">${item.source_code}</span></td>
    `;
    catalogTbody.appendChild(tr);
  });
}

function formatSourceCode(rawSource, materialName) {
  if (!rawSource) rawSource = '';
  const match = rawSource.match(/\[[1-6]\]/);
  if (match) return match[0];
  
  if (emissionCatalog && emissionCatalog.materials && materialName) {
    const found = emissionCatalog.materials.find(m => 
      m.name.toLowerCase() === materialName.toLowerCase() ||
      materialName.toLowerCase().includes(m.name.toLowerCase())
    );
    if (found) return found.source_code;
  }
  
  const low = rawSource.toLowerCase();
  if (low.includes('cpwd')) return '[1]';
  if (low.includes('epd') || low.includes('steel') || low.includes('cma')) return '[2]';
  if (low.includes('ice')) return '[3]';
  if (low.includes('cea') || low.includes('ipcc')) return '[4]';
  if (low.includes('efca')) return '[5]';
  if (low.includes('defra') || low.includes('morth')) return '[6]';
  return '[1]';
}

function populateAddMaterialDropdowns() {
  if (!emissionCatalog || !emissionCatalog.materials) return;
  const catFilter = document.getElementById('matSelectCategory');
  const matSelect = document.getElementById('matSelectCatalog');
  if (!matSelect) return;

  const updateList = () => {
    const selectedCat = catFilter ? catFilter.value : 'all';
    matSelect.innerHTML = '';
    
    const filtered = selectedCat === 'all' 
      ? emissionCatalog.materials 
      : emissionCatalog.materials.filter(m => m.category === selectedCat);

    filtered.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m.id;
      opt.textContent = `${m.name} (${m.emission_factor} kgCO2e/${m.unit}) ${m.source_code}`;
      matSelect.appendChild(opt);
    });

    syncSelectedMaterial();
  };

  const syncSelectedMaterial = () => {
    const selectedId = matSelect.value;
    const item = emissionCatalog.materials.find(m => m.id === selectedId) || emissionCatalog.materials[0];
    if (item) {
      const uDisp = document.getElementById('matUnitDisplay');
      const uLabel = document.getElementById('matUnitLabel');
      const efDisp = document.getElementById('matEfDisplay');
      const srcDisp = document.getElementById('matSourceDisplay');

      if (uDisp) uDisp.textContent = item.unit;
      if (uLabel) uLabel.textContent = item.unit;
      if (efDisp) efDisp.textContent = `${item.emission_factor} kgCO2e/${item.unit}`;
      if (srcDisp) srcDisp.textContent = `${item.source_code} Ref`;
    }
  };

  if (catFilter) catFilter.addEventListener('change', updateList);
  matSelect.addEventListener('change', syncSelectedMaterial);
  updateList();
}

function populateAddTransportDropdowns() {
  if (!emissionCatalog || !emissionCatalog.transport) return;
  const trSelect = document.getElementById('trVehicleSelect');
  if (!trSelect) return;
  trSelect.innerHTML = '';

  emissionCatalog.transport.forEach(t => {
    const opt = document.createElement('option');
    opt.value = t.name;
    opt.textContent = `${t.name} (${t.emission_factor} kgCO2e/t·km) ${t.source_code}`;
    trSelect.appendChild(opt);
  });
}

function populateAddEquipmentDropdowns() {
  if (!emissionCatalog || !emissionCatalog.equipment) return;
  const eqSelect = document.getElementById('eqSelectCatalog');
  if (!eqSelect) return;
  eqSelect.innerHTML = '';

  emissionCatalog.equipment.forEach(eq => {
    const opt = document.createElement('option');
    opt.value = eq.name;
    opt.textContent = `${eq.name} (${eq.fuel_type} - ${eq.emission_factor} kgCO2e/${eq.unit}) ${eq.source_code}`;
    eqSelect.appendChild(opt);
  });

  const syncEqUnit = () => {
    const selectedName = eqSelect.value;
    const item = emissionCatalog.equipment.find(e => e.name === selectedName);
    const uLabel = document.getElementById('eqUnitLabel');
    if (uLabel && item) {
      uLabel.textContent = item.unit;
    }
  };

  eqSelect.addEventListener('change', syncEqUnit);
  syncEqUnit();
}

// Modal Click Handlers & Continuous Periodic Ingestion Flow
function initModalEventListeners() {
  // 1. Emission Factor Library Modal Button
  const btnOpenCat = document.getElementById('btnOpenEmissionCatalog');
  if (btnOpenCat) {
    btnOpenCat.addEventListener('click', () => {
      openModal('modalEmissionCatalogOverlay');
    });
  }

  // 2. View Navigation (Back to List / Save Detail)
  const btnBackList = document.getElementById('btnBackToLogList');
  const btnSaveBack = document.getElementById('btnSaveDetailAndBack');
  if (btnBackList) {
    btnBackList.addEventListener('click', returnToLogList);
  }
  if (btnSaveBack) {
    btnSaveBack.addEventListener('click', () => {
      returnToLogList();
      showToast('Periodic log synchronized and saved to Digital Twin!', 'success');
    });
  }

  // 3. New Site Progress Entry Modal Trigger
  const btnOpenNewEntry = document.getElementById('btnOpenNewEntryModal');
  const btnSubmitStage = document.getElementById('btnSubmitNewStage');

  if (btnOpenNewEntry) {
    btnOpenNewEntry.addEventListener('click', () => {
      const stages = appState && appState.timeline ? appState.timeline.stages : [];
      const newId = stages.length + 1;
      const nameInput = document.getElementById('newStageName');
      if (nameInput) {
        nameInput.value = `Site Milestone Pour #${newId}`;
      }
      const dateInput = document.getElementById('newStageDate');
      if (dateInput) {
        const lastStage = stages.length > 0 ? stages[stages.length - 1] : null;
        if (lastStage && lastStage.date) {
          try {
            const d = new Date(lastStage.date);
            d.setDate(d.getDate() + 30);
            dateInput.value = d.toISOString().split('T')[0];
          } catch(e) {
            dateInput.value = new Date().toISOString().split('T')[0];
          }
        } else {
          dateInput.value = new Date().toISOString().split('T')[0];
        }
      }
      const copyRadio = document.getElementById('modeCopyTemplate');
      if (copyRadio) copyRadio.checked = true;
      openModal('modalNewStageOverlay');
    });
  }

  if (btnSubmitStage) {
    btnSubmitStage.addEventListener('click', async () => {
      const name = document.getElementById('newStageName')?.value || 'Site Milestone Entry';
      const date = document.getElementById('newStageDate')?.value || new Date().toISOString().split('T')[0];
      const volume = parseFloat(document.getElementById('newStageVolume')?.value || 50.0);
      const status = document.getElementById('newStageStatus')?.value || 'In Progress';
      const copyTemplate = document.getElementById('modeCopyTemplate')?.checked || false;

      try {
        const res = await fetch('/api/stages/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, date, volume_m3: volume, status, copy_previous: copyTemplate })
        });
        const data = await res.json();
        if (data.success) {
          appState = data.project_state;
          updateUI(appState);
          closeModal('modalNewStageOverlay');
          showToast(`Logged ${name}!`, 'success');
          // Automatically transition to the newly created log's detail view!
          openStageDetail(data.stage.stage_id);
        } else {
          showToast(data.error || 'Failed to save entry', 'error');
        }
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  // 3. Add Material Modal
  const btnOpenAddMat = document.getElementById('btnOpenAddMaterialModal');
  const btnSubmitAddMat = document.getElementById('btnSubmitAddMaterial');

  if (btnOpenAddMat) {
    btnOpenAddMat.addEventListener('click', () => {
      openModal('modalAddMaterialOverlay');
    });
  }

  if (btnSubmitAddMat) {
    btnSubmitAddMat.addEventListener('click', async () => {
      const matSelect = document.getElementById('matSelectCatalog');
      if (!emissionCatalog || !matSelect) return;

      const item = emissionCatalog.materials.find(m => m.id === matSelect.value) || emissionCatalog.materials[0];
      const consumedQty = parseFloat(document.getElementById('matConsumedInput')?.value || 0);
      const wastePct = parseFloat(document.getElementById('matWasteInput')?.value || 3.0);

      const payload = {
        material_name: item.name,
        category: item.category,
        unit: item.unit,
        consumed_quantity: consumedQty,
        emission_factor: item.emission_factor,
        waste_percentage: wastePct,
        ef_source: item.source_code
      };

      try {
        const res = await fetch('/api/materials/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
          appState = data.project_state;
          updateUI(appState);
          closeModal('modalAddMaterialOverlay');
          showToast(`Added ${item.name} from Central Library!`, 'success');
        } else {
          showToast(data.error || 'Failed to add material', 'error');
        }
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  // 4. Add Transport Modal
  const btnOpenAddTr = document.getElementById('btnOpenAddTransportModal');
  const btnSubmitAddTr = document.getElementById('btnSubmitAddTransport');

  if (btnOpenAddTr) {
    btnOpenAddTr.addEventListener('click', () => {
      openModal('modalAddTransportOverlay');
    });
  }

  if (btnSubmitAddTr) {
    btnSubmitAddTr.addEventListener('click', async () => {
      const matDesc = document.getElementById('trMaterialInput')?.value || 'Bulk Material Haulage';
      const vehicle = document.getElementById('trVehicleSelect')?.value || 'Heavy Tipper Truck (16-32t)';
      const mass = parseFloat(document.getElementById('trMassInput')?.value || 20.0);
      const dist = parseFloat(document.getElementById('trDistanceInput')?.value || 50.0);

      try {
        const res = await fetch('/api/transport/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            material_name: matDesc,
            vehicle_type: vehicle,
            quantity_transported: mass,
            distance_km: dist
          })
        });
        const data = await res.json();
        if (data.success) {
          appState = data.project_state;
          updateUI(appState);
          closeModal('modalAddTransportOverlay');
          showToast(`Added haulage transport leg!`, 'success');
        } else {
          showToast(data.error || 'Failed to add transport', 'error');
        }
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  // 5. Add Equipment Modal
  const btnOpenAddEq = document.getElementById('btnOpenAddEquipmentModal');
  const btnSubmitAddEq = document.getElementById('btnSubmitAddEquipment');

  if (btnOpenAddEq) {
    btnOpenAddEq.addEventListener('click', () => {
      openModal('modalAddEquipmentOverlay');
    });
  }

  if (btnSubmitAddEq) {
    btnSubmitAddEq.addEventListener('click', async () => {
      const eqSelect = document.getElementById('eqSelectCatalog');
      if (!emissionCatalog || !eqSelect) return;

      const item = emissionCatalog.equipment.find(e => e.name === eqSelect.value) || emissionCatalog.equipment[0];
      const hours = parseFloat(document.getElementById('eqHoursInput')?.value || 40.0);
      const fuel = parseFloat(document.getElementById('eqFuelInput')?.value || 100.0);

      try {
        const res = await fetch('/api/equipment/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            equipment_name: item.name,
            fuel_type: item.fuel_type,
            hours_operated: hours,
            fuel_consumed: fuel,
            emission_factor: item.emission_factor
          })
        });
        const data = await res.json();
        if (data.success) {
          appState = data.project_state;
          updateUI(appState);
          closeModal('modalAddEquipmentOverlay');
          showToast(`Added plant equipment record!`, 'success');
        } else {
          showToast(data.error || 'Failed to add equipment', 'error');
        }
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }
}

// Delete Material Action
window.deleteMaterialItem = async function(idx) {
  if (!confirm('Remove this material from site consumption log?')) return;
  try {
    const res = await fetch('/api/materials/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ index: idx })
    });
    const data = await res.json();
    if (data.success) {
      appState = data.project_state;
      updateUI(appState);
      showToast('Material removed from site log', 'info');
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// Delete Transport Action
window.deleteTransportItem = async function(idx) {
  if (!confirm('Remove this haulage transport leg?')) return;
  try {
    const res = await fetch('/api/transport/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ index: idx })
    });
    const data = await res.json();
    if (data.success) {
      appState = data.project_state;
      updateUI(appState);
      showToast('Transport haulage leg removed', 'info');
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// Delete Equipment Action
window.deleteEquipmentItem = async function(idx) {
  if (!confirm('Remove this site equipment record?')) return;
  try {
    const res = await fetch('/api/equipment/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ index: idx })
    });
    const data = await res.json();
    if (data.success) {
      appState = data.project_state;
      updateUI(appState);
      showToast('Equipment plant record removed', 'info');
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// Delete Progress Stage / Entry Action
window.deleteStageItem = async function(stageId) {
  if (!confirm(`Delete Site Progress Log #${stageId}?`)) return;
  try {
    const res = await fetch('/api/stages/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stage_id: stageId })
    });
    const data = await res.json();
    if (data.success) {
      appState = data.project_state;
      updateUI(appState);
      showToast(`Site Progress Log #${stageId} deleted`, 'info');
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// Baseline Modal Helpers
window.openBaselineModal = function() {
  if (appState && appState.summary) {
    const summary = appState.summary;
    const nameInput = document.getElementById('baselineProjectName');
    const gradeInput = document.getElementById('baselineConcreteGrade');
    const volInput = document.getElementById('baselineVolumeInput');
    const budgetInput = document.getElementById('baselineBudgetInput');
    if (nameInput) nameInput.value = summary.project_name || 'Commercial Complex Construction Package';
    if (gradeInput) gradeInput.value = summary.concrete_grade || 'M30 Design Mix';
    if (volInput) volInput.value = summary.concrete_volume_m3 || 420;
    if (budgetInput) budgetInput.value = summary.carbon_budget_tonnes || 115;
  }
  openModal('modalBaselineOverlay');
};

async function saveProjectBaseline() {
  const name = document.getElementById('baselineProjectName')?.value || 'Commercial Complex Construction Package';
  const grade = document.getElementById('baselineConcreteGrade')?.value || 'M30 Design Mix';
  const volume = parseFloat(document.getElementById('baselineVolumeInput')?.value || 420);
  const budget = parseFloat(document.getElementById('baselineBudgetInput')?.value || 115);

  try {
    const res = await fetch('/api/update/meta', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_name: name,
        concrete_grade: grade,
        concrete_volume_m3: volume,
        carbon_budget_tonnes: budget
      })
    });
    const data = await res.json();
    if (data.success) {
      appState = data.project_state;
      updateUI(appState);
      closeModal('modalBaselineOverlay');
      showToast('Project baseline & budget targets updated!', 'success');
    } else {
      showToast(data.error || 'Failed to update baseline', 'error');
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadProjectData() {
  try {
    const res = await fetch('/api/project');
    if (!res.ok) throw new Error('Failed to load project state');
    appState = await res.json();
    updateUI(appState);
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}

function updateUI(state) {
  if (!state) return;
  const summary = state.summary || {};
  const benchmarks = state.benchmarks || {};
  const timeline = state.timeline || {};

  // 1. KPI Cards
  const kpiTotal = document.getElementById('kpiTotalCarbon');
  if (kpiTotal) kpiTotal.textContent = fmt(summary.total_emissions_tonnes, 2);
  const kpiKg = document.getElementById('kpiTotalKg');
  if (kpiKg) kpiKg.textContent = `${(Number(summary.total_emissions_kg) || 0).toLocaleString()} kgCO2e cumulative`;

  const kpiProg = document.getElementById('kpiProgress');
  if (kpiProg) kpiProg.textContent = `${fmt(timeline.overall_progress_pct, 1)}%`;
  const kpiVol = document.getElementById('kpiVolumePlaced');
  if (kpiVol) kpiVol.textContent = `${fmt(timeline.completed_volume_m3, 1)} / ${fmt(summary.concrete_volume_m3, 0)} m³ placed`;

  const budgetCard = document.getElementById('kpiBudgetStatus');
  if (budgetCard) budgetCard.textContent = benchmarks.budget_status || 'Within Carbon Budget';
  const budgetBadge = document.getElementById('kpiBudgetBadge');
  if (budgetBadge) {
    budgetBadge.className = `kpi-badge badge-${benchmarks.budget_health === 'good' ? 'green' : (benchmarks.budget_health === 'warning' ? 'amber' : 'red')}`;
    const variance = Number(benchmarks.budget_variance_pct) || 0;
    budgetBadge.textContent = variance <= 0 ? 'On Track' : `+${variance.toFixed(1)}%`;
  }

  const kpiWaste = document.getElementById('kpiWastePenalty');
  if (kpiWaste) kpiWaste.textContent = fmt(summary.waste_penalty_tonnes, 2);
  const kpiWasteP = document.getElementById('kpiWastePct');
  if (kpiWasteP) kpiWasteP.textContent = `${fmt(summary.waste_penalty_pct, 1)}% embedded loss`;

  // Status Bar Baseline Info
  const stProjectName = document.getElementById('statusProjectName');
  if (stProjectName) {
    stProjectName.textContent = summary.project_name || 'Commercial Complex Construction Package';
  }
  const stBaselineMeta = document.getElementById('statusBaselineMeta');
  if (stBaselineMeta) {
    stBaselineMeta.textContent = `Grade: ${summary.concrete_grade || 'M30'} | Planned Volume: ${fmt(summary.concrete_volume_m3, 0)} m³ | Budget: ${fmt(summary.carbon_budget_tonnes, 1)} tCO2e`;
  }

  // Activity Performance Summary Card
  const volPlacedEl = document.getElementById('summaryVolPlaced');
  if (volPlacedEl) {
    volPlacedEl.textContent = `${fmt(timeline.completed_volume_m3, 1)} / ${fmt(summary.concrete_volume_m3, 1)} m³ (${fmt(timeline.overall_progress_pct, 1)}%)`;
  }
  const volBar = document.getElementById('summaryVolBar');
  if (volBar) volBar.style.width = `${Math.min(100, Math.max(0, Number(timeline.overall_progress_pct) || 0))}%`;

  const carbonBurnEl = document.getElementById('summaryCarbonBurn');
  if (carbonBurnEl) {
    carbonBurnEl.textContent = `${fmt(summary.total_emissions_tonnes, 2)} / ${fmt(summary.carbon_budget_tonnes, 2)} tCO2e`;
  }
  const carbonBar = document.getElementById('summaryCarbonBar');
  if (carbonBar) {
    const totalEm = Number(summary.total_emissions_tonnes) || 0;
    const budgetEm = Number(summary.carbon_budget_tonnes) || 1;
    const burnPct = (totalEm / budgetEm) * 100.0;
    carbonBar.style.width = `${Math.min(100, Math.max(0, burnPct))}%`;
    carbonBar.style.backgroundColor = burnPct > 100 ? '#ef4444' : (burnPct > 85 ? '#f59e0b' : '#10b981');
  }

  const avgInt = document.getElementById('summaryAvgIntensity');
  if (avgInt) avgInt.textContent = `${fmt(summary.concrete_mix_intensity_kg_per_m3, 1)} kg/m³`;

  const projTotal = document.getElementById('summaryProjectedTotal');
  if (projTotal) projTotal.textContent = `${fmt(timeline.final_projected_carbon_tonnes, 2)} tCO2e`;

  // 2. Charts
  refreshAllCharts();

  // 3. Data Tables
  if (summary.materials_module && summary.materials_module.items) {
    renderMaterialsTable(summary.materials_module.items);
  }
  if (summary.transport_module && summary.transport_module.items) {
    renderTransportTable(summary.transport_module.items);
  }
  if (summary.equipment_module && summary.equipment_module.items) {
    renderEquipmentTable(summary.equipment_module.items);
  }
  if (timeline.stages) {
    renderStagesTable(timeline.stages);
  }
}

function renderTimelineStages(timeline) {
  const container = document.getElementById('stagePillsContainer');
  if (!container) return;
  container.innerHTML = '';

  const stages = timeline.stages || [];
  let defaultStage = stages[0];

  stages.forEach(stg => {
    const pill = document.createElement('div');
    const isSelected = selectedStageId === stg.stage_id;
    pill.className = `stage-pill ${stg.status.toLowerCase().replace(' ', '-')} ${isSelected ? 'selected' : ''}`;
    pill.style.cursor = 'pointer';
    pill.innerHTML = `
      <strong>Period ${stg.stage_id}:</strong> ${stg.stage_name}
      <span style="font-size:10px; color:#64748b;">(${stg.volume_m3} m³)</span>
      <span class="kpi-badge ${stg.status === 'Completed' ? 'badge-green' : (stg.status === 'In Progress' ? 'badge-amber' : 'badge-blue')}">${stg.status}</span>
    `;

    pill.addEventListener('click', () => {
      selectedStageId = stg.stage_id;
      document.querySelectorAll('.stage-pill').forEach(p => p.classList.remove('selected'));
      pill.classList.add('selected');
      const indicator = document.getElementById('activeStageIndicator');
      if (indicator) indicator.textContent = `Period ${stg.stage_id} Selected`;
      updateInspector(stg);
    });

    container.appendChild(pill);

    if (stg.status === 'In Progress') {
      defaultStage = stg;
    }
  });

  // Select initial stage
  if (!selectedStageId && defaultStage) {
    selectedStageId = defaultStage.stage_id;
    updateInspector(defaultStage);
  } else if (selectedStageId) {
    const found = stages.find(s => s.stage_id === selectedStageId);
    if (found) updateInspector(found);
  }
}

function refreshAllCharts() {
  if (!appState || !charts) return;
  const summary = appState.summary;
  const timeline = appState.timeline;
  const benchmarks = appState.benchmarks;

  charts.renderCumulativeTrend('chartCumulative', timeline, summary.carbon_budget_tonnes);
  charts.renderStageBreakdown('chartStageBreakdown', summary.stage_breakdown);
  charts.renderMaterialHotspots('chartHotspots', summary.materials_module.items);
  charts.renderPlannedVsActual('chartPlannedVsActual', summary.materials_module.items);
  charts.renderBenchmarkComparison('chartBenchmark', benchmarks, summary.concrete_mix_intensity_kg_per_m3);
}

function updateInspector(stg) {
  const panel = document.getElementById('inspectorPanel');
  if (!panel) return;

  if (!stg) {
    panel.innerHTML = `<p style="color:#64748b; font-size:12px; font-style:italic;">Click any reporting period above to inspect its volume placed, cumulative carbon, and burn rate.</p>`;
    return;
  }

  const totalVol = appState?.summary?.concrete_volume_m3 || 1;
  const volShare = fmt((Number(stg.volume_m3) / totalVol) * 100, 1);
  const cumCarbonStr = (stg.actual_cumulative_carbon_t !== null && stg.actual_cumulative_carbon_t !== undefined) ? `${fmt(stg.actual_cumulative_carbon_t, 2)} tCO2e` : 'Pending Pour Log';
  const plannedCarbonStr = `${fmt(stg.planned_cumulative_carbon_t, 2)} tCO2e`;
  const durLabel = stg.duration_days > 0 ? `${stg.duration_days} days continuous interval` : 'Baseline Interval';

  panel.innerHTML = `
    <div style="font-size:13px; font-weight:700; color:#1e293b; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
      <span>${stg.stage_name}</span>
      <span class="kpi-badge ${stg.status === 'Completed' ? 'badge-green' : (stg.status === 'In Progress' ? 'badge-amber' : 'badge-blue')}">${stg.status}</span>
    </div>
    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; font-size:12px;">
      <div style="background:#f8fafc; padding:6px 10px; border-radius:6px; border:1px solid #e2e8f0;">
        <span style="color:#64748b; font-size:11px;">Reporting Date:</span><br>
        <strong>${stg.date}</strong>
      </div>
      <div style="background:#f8fafc; padding:6px 10px; border-radius:6px; border:1px solid #e2e8f0;">
        <span style="color:#64748b; font-size:11px;">Continuous Duration:</span><br>
        <strong style="color:#2563eb;">${durLabel}</strong>
      </div>
      <div style="background:#f8fafc; padding:6px 10px; border-radius:6px; border:1px solid #e2e8f0;">
        <span style="color:#64748b; font-size:11px;">Volume Placed:</span><br>
        <strong>${stg.volume_m3} m³ (${volShare}%)</strong>
      </div>
      <div style="background:#f8fafc; padding:6px 10px; border-radius:6px; border:1px solid #e2e8f0;">
        <span style="color:#64748b; font-size:11px;">Actual Cumulative Carbon:</span><br>
        <strong style="color:#2563eb;">${cumCarbonStr}</strong>
      </div>
      <div style="background:#f8fafc; padding:6px 10px; border-radius:6px; border:1px solid #e2e8f0; grid-column:span 2;">
        <span style="color:#64748b; font-size:11px;">Planned Cumulative Carbon:</span><br>
        <strong>${plannedCarbonStr}</strong>
      </div>
    </div>
  `;
}

// Data Tables Rendering & Inline Editing
function renderMaterialsTable(items) {
  const tbody = document.getElementById('materialsTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';

  if (!items || items.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="10" style="text-align:center; padding:32px 16px; color:#64748b; background:#f8fafc;">
          <div style="font-size:13px; font-weight:600; color:#334155; margin-bottom:4px;">No materials recorded in this log yet</div>
          <div style="font-size:12px; color:#64748b;">Click <strong>Add Material</strong> above to record consumed materials one by one from the central library.</div>
        </td>
      </tr>
    `;
    return;
  }

  (items || []).forEach((m, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <span style="display:inline-flex; align-items:center; gap:6px;">
          <strong>${m.material_name}</strong>
          <button onclick="deleteMaterialItem(${idx})" title="Remove item" style="background:none; border:none; color:#94a3b8; cursor:pointer; font-size:16px; line-height:1; padding:0 4px;" onmouseover="this.style.color='#ef4444'" onmouseout="this.style.color='#94a3b8'">&times;</button>
        </span>
      </td>
      <td><span class="kpi-badge badge-blue">${m.category}</span></td>
      <td>${m.unit}</td>
      <td class="editable-cell" contenteditable="true" data-field="planned_quantity" data-index="${idx}">${m.planned_quantity || 0}</td>
      <td class="editable-cell" contenteditable="true" data-field="consumed_quantity" data-index="${idx}">${m.consumed_quantity}</td>
      <td class="editable-cell" contenteditable="true" data-field="emission_factor" data-index="${idx}">${m.emission_factor}</td>
      <td class="editable-cell" contenteditable="true" data-field="waste_percentage" data-index="${idx}">${m.waste_percentage}%</td>
      <td>${fmt(m.carbon_emission_tonnes, 3)} t</td>
      <td>${fmt(m.share_pct, 1)}%</td>
      <td><span class="source-pill" title="View reference in Central Library">${formatSourceCode(m.ef_source, m.material_name)}</span></td>
    `;
    tbody.appendChild(tr);
  });

  // Attach blur listener to editable cells
  tbody.querySelectorAll('.editable-cell').forEach(cell => {
    cell.addEventListener('blur', async (e) => {
      const idx = parseInt(cell.getAttribute('data-index'));
      const field = cell.getAttribute('data-field');
      let val = cell.textContent.trim().replace('%', '');
      val = parseFloat(val) || 0.0;
      
      const updates = {};
      updates[field] = val;
      await updateMaterialParam(idx, updates);
    });

    cell.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        cell.blur();
      }
    });
  });
}

function renderTransportTable(items) {
  const tbody = document.getElementById('transportTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';

  if (!items || items.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" style="text-align:center; padding:24px 16px; color:#64748b; background:#f8fafc;">
          <div style="font-size:13px; font-weight:600; color:#334155; margin-bottom:4px;">No haulage transport legs recorded</div>
          <div style="font-size:12px; color:#64748b;">Click <strong>Add Transport Leg</strong> above to log material delivery distances.</div>
        </td>
      </tr>
    `;
    return;
  }

  (items || []).forEach((t, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <span style="display:inline-flex; align-items:center; gap:6px;">
          <strong>${t.material_name}</strong>
          <button onclick="deleteTransportItem(${idx})" title="Remove transport leg" style="background:none; border:none; color:#94a3b8; cursor:pointer; font-size:16px; line-height:1; padding:0 4px;" onmouseover="this.style.color='#ef4444'" onmouseout="this.style.color='#94a3b8'">&times;</button>
        </span>
      </td>
      <td>${t.vehicle_type}</td>
      <td class="editable-cell" contenteditable="true" data-field="quantity_transported" data-index="${idx}">${t.quantity_tonnes} t</td>
      <td class="editable-cell" contenteditable="true" data-field="distance_km" data-index="${idx}">${t.distance_km} km</td>
      <td>${t.effective_distance_km} km</td>
      <td class="editable-cell" contenteditable="true" data-field="transport_ef" data-index="${idx}">${t.transport_ef}</td>
      <td>${fmt(t.carbon_emission_tonnes, 3)} t</td>
      <td>${fmt(t.share_pct, 1)}%</td>
    `;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll('.editable-cell').forEach(cell => {
    cell.addEventListener('blur', async () => {
      const idx = parseInt(cell.getAttribute('data-index'));
      const field = cell.getAttribute('data-field');
      const val = parseFloat(cell.textContent.trim().replace(/[^\d.]/g, '')) || 0.0;
      const updates = {};
      updates[field] = val;
      await updateTransportParam(idx, updates);
    });
  });
}

function renderEquipmentTable(items) {
  const tbody = document.getElementById('equipmentTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';

  if (!items || items.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align:center; padding:24px 16px; color:#64748b; background:#f8fafc;">
          <div style="font-size:13px; font-weight:600; color:#334155; margin-bottom:4px;">No plant equipment recorded</div>
          <div style="font-size:12px; color:#64748b;">Click <strong>Add Equipment</strong> above to log equipment operating hours.</div>
        </td>
      </tr>
    `;
    return;
  }

  (items || []).forEach((eq, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <span style="display:inline-flex; align-items:center; gap:6px;">
          <strong>${eq.equipment_name}</strong>
          <button onclick="deleteEquipmentItem(${idx})" title="Remove equipment" style="background:none; border:none; color:#94a3b8; cursor:pointer; font-size:16px; line-height:1; padding:0 4px;" onmouseover="this.style.color='#ef4444'" onmouseout="this.style.color='#94a3b8'">&times;</button>
        </span>
      </td>
      <td><span class="kpi-badge ${eq.fuel_type === 'Diesel' ? 'badge-amber' : 'badge-green'}">${eq.fuel_type}</span></td>
      <td class="editable-cell" contenteditable="true" data-field="hours_operated" data-index="${idx}">${eq.hours_operated} hrs</td>
      <td class="editable-cell" contenteditable="true" data-field="fuel_consumed" data-index="${idx}">${eq.energy_consumed} ${eq.energy_unit}</td>
      <td>${eq.emission_factor}</td>
      <td>${fmt(eq.carbon_emission_tonnes, 3)} t</td>
      <td>${fmt(eq.share_pct, 1)}%</td>
    `;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll('.editable-cell').forEach(cell => {
    cell.addEventListener('blur', async () => {
      const idx = parseInt(cell.getAttribute('data-index'));
      const field = cell.getAttribute('data-field');
      const val = parseFloat(cell.textContent.trim().replace(/[^\d.]/g, '')) || 0.0;
      const updates = {};
      updates[field] = val;
      await updateEquipmentParam(idx, updates);
    });
  });
}

function renderStagesTable(stages) {
  const tbody = document.getElementById('stagesTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';

  (stages || []).forEach(stg => {
    const tr = document.createElement('tr');
    let carbonStr = '-';
    if (stg.status !== 'Scheduled') {
      const stageVal = (stg.stage_carbon_t !== undefined && stg.stage_carbon_t !== null)
        ? stg.stage_carbon_t
        : 0.0;
      carbonStr = fmt(stageVal, 2) + ' t';
    }

    const statusStyle = stg.status === 'Completed'
      ? 'border-color:#86efac; background:#f0fdf4; color:#15803d;'
      : (stg.status === 'In Progress'
        ? 'border-color:#93c5fd; background:#eff6ff; color:#1d4ed8;'
        : 'border-color:#e2e8f0; background:#f8fafc; color:#64748b;');

    tr.innerHTML = `
      <td>Log #${stg.stage_id}</td>
      <td><strong>${stg.stage_name}</strong></td>
      <td>${stg.date}</td>
      <td>
        <select onchange="changeStageStatus(${stg.stage_id}, this.value)" style="font-size:11px; font-weight:600; padding:3px 6px; border-radius:4px; border:1px solid; ${statusStyle} cursor:pointer;">
          <option value="Completed" ${stg.status === 'Completed' ? 'selected' : ''}>Completed</option>
          <option value="In Progress" ${stg.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
          <option value="Scheduled" ${stg.status === 'Scheduled' ? 'selected' : ''}>Scheduled</option>
        </select>
      </td>
      <td style="font-weight:700;">${carbonStr}</td>
      <td>
        <div style="display:inline-flex; align-items:center; gap:6px;">
          <button class="btn btn-sm btn-outline" style="border-color:#2563eb; color:#2563eb; font-weight:600; padding:4px 10px; border-radius:4px; white-space:nowrap;" onclick="openStageDetail(${stg.stage_id})">
            View / Edit Details →
          </button>
          <button class="btn btn-sm btn-outline" style="border-color:#fca5a5; color:#ef4444; font-weight:600; padding:4px 8px; border-radius:4px;" onclick="deleteStageItem(${stg.stage_id})" title="Delete this entry">
            Delete
          </button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderSnapshotsTable(snapshots) {
  const tbody = document.getElementById('snapshotsTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';

  snapshots.forEach(s => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="kpi-badge badge-blue">v${s.version}</span></td>
      <td style="font-size:11px; color:#64748b;">${s.timestamp}</td>
      <td><strong>${s.label}</strong></td>
      <td>${s.author}</td>
      <td><strong>${fmt(s.total_carbon_tonnes, 2)} t</strong></td>
      <td>${fmt(s.carbon_intensity_kg_per_m3, 1)} kg/m³</td>
      <td><span class="kpi-badge badge-green">${s.mix_category}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// API Parameter Updates
async function updateMaterialParam(index, updates) {
  try {
    const res = await fetch('/api/update/material', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ index, updates, reason: 'Live Table Edit' })
    });
    const data = await res.json();
    if (data.success) {
      appState = data.project_state;
      updateUI(appState);
      showToast('Material parameter updated and twin recalculated!', 'success');
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function updateTransportParam(index, updates) {
  try {
    const res = await fetch('/api/update/transport', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ index, updates, reason: 'Live Transport Edit' })
    });
    const data = await res.json();
    if (data.success) {
      appState = data.project_state;
      updateUI(appState);
      showToast('Transport haulage updated and twin recalculated!', 'success');
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function updateEquipmentParam(index, updates) {
  try {
    const res = await fetch('/api/update/equipment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ index, updates, reason: 'Live Equipment Edit' })
    });
    const data = await res.json();
    if (data.success) {
      appState = data.project_state;
      updateUI(appState);
      showToast('Equipment energy updated and twin recalculated!', 'success');
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}



// File Upload Handler
async function handleFileUpload(file) {
  showToast(`Uploading and analyzing ${file.name}...`, 'info');
  const reader = new FileReader();
  reader.onload = async (e) => {
    try {
      const base64 = e.target.result.split(',')[1];
      const res = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: file.name, data: base64 })
      });
      const data = await res.json();
      if (data.success) {
        appState = data.project_state;
        updateUI(appState);
        showToast(data.message || 'File parsed & Twin updated successfully!', 'success');
      } else {
        showToast(data.error || 'Failed to parse file', 'error');
      }
    } catch (err) {
      showToast(err.message, 'error');
    }
  };
  reader.readAsDataURL(file);
}

// Reset Demo Data
async function resetDemoData() {
  try {
    const res = await fetch('/api/reset', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      appState = data.project_state;
      updateUI(appState);
      showToast('Digital Twin reset to default demo data', 'success');
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Snapshot Modal
function openSnapshotModal() {
  const label = prompt('Enter a label for this version snapshot:', 'Design Optimization Checkpoint');
  if (label) {
    createSnapshot(label);
  }
}

async function createSnapshot(label) {
  try {
    const res = await fetch('/api/snapshot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ label, author: 'Engineer' })
    });
    const data = await res.json();
    if (data.success) {
      appState.snapshots = data.snapshots;
      renderSnapshotsTable(data.snapshots);
      showToast(`Snapshot "${label}" saved to version history!`, 'success');
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Toast Notification
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ==========================================
// PHOTO OCR INGESTION
// ==========================================
let latestOcrResult = null;

function initOcrPhotoIngestion() {
  // Dropzone for Challan Photos
  const pDropzone = document.getElementById('photoDropzone');
  const pFileInput = document.getElementById('photoFileInput');

  if (pDropzone && pFileInput) {
    pDropzone.addEventListener('click', () => pFileInput.click());
    pDropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      pDropzone.classList.add('dragover');
    });
    pDropzone.addEventListener('dragleave', () => pDropzone.classList.remove('dragover'));
    pDropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      pDropzone.classList.remove('dragover');
      if (e.dataTransfer.files.length > 0) {
        handlePhotoUpload(Array.from(e.dataTransfer.files));
      }
    });

    pFileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        handlePhotoUpload(Array.from(e.target.files));
      }
    });
  }

  // Download Partial CSV button
  const btnDownloadCsv = document.getElementById('btnDownloadOcrCsv');
  if (btnDownloadCsv) {
    btnDownloadCsv.addEventListener('click', () => {
      if (!latestOcrResult || !latestOcrResult.csv_content) {
        showToast('No parsed CSV data available.', 'error');
        return;
      }
      const blob = new Blob([latestOcrResult.csv_content], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', 'site_delivery_challan_materials.csv');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      showToast('Downloaded partial CSV template!', 'success');
    });
  }

  // Add to Active Log button
  const btnAddStage = document.getElementById('btnAddOcrToStage');
  if (btnAddStage) {
    btnAddStage.addEventListener('click', async () => {
      if (!latestOcrResult || !latestOcrResult.verified_materials || latestOcrResult.verified_materials.length === 0) {
        showToast('No verified materials to add.', 'error');
        return;
      }
      try {
        btnAddStage.disabled = true;
        btnAddStage.textContent = 'Adding...';
        const res = await fetch('/api/ocr/add-verified', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ materials: latestOcrResult.verified_materials })
        });
        const data = await res.json();
        if (data.success) {
          appState = data.project_state;
          updateUI(appState);
          showToast(`Added ${data.added_count} materials to active site log!`, 'success');
          // Switch to detail view of current active stage to inspect
          if (appState.timeline && appState.timeline.stages && appState.timeline.stages.length > 0) {
            const activeId = appState.timeline.active_stage_id || appState.timeline.stages[appState.timeline.stages.length - 1].stage_id;
            openStageDetail(activeId);
          }
        } else {
          showToast(data.error || 'Failed to add materials', 'error');
        }
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        btnAddStage.disabled = false;
        btnAddStage.textContent = 'Add to Active Log';
      }
    });
  }
}

async function handlePhotoUpload(files) {
  const imageFiles = files.filter(f => f.type.startsWith('image/'));
  if (imageFiles.length === 0) {
    showToast('Please select valid image files (JPG, PNG, WebP).', 'error');
    return;
  }

  const spinner = document.getElementById('ocrLoading');
  const resultsBox = document.getElementById('ocrResultsContainer');
  if (spinner) spinner.style.display = 'block';
  if (resultsBox) resultsBox.style.display = 'none';

  try {
    const photoPayloads = await Promise.all(imageFiles.map(file => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve({
          name: file.name,
          type: file.type || 'image/jpeg',
          data: reader.result
        });
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    }));

    const res = await fetch('/api/ocr/parse-photos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ photos: photoPayloads })
    });

    const data = await res.json();
    if (!res.ok || !data.success) {
      showToast(data.error || 'Failed to process photos', 'error');
      return;
    }

    latestOcrResult = data;
    renderOcrResults(data);
    showToast(`Extracted ${data.verified_count} verified material(s) from challan photo(s)!`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (spinner) spinner.style.display = 'none';
  }
}

function renderOcrResults(data) {
  const resultsBox = document.getElementById('ocrResultsContainer');
  const title = document.getElementById('ocrResultsTitle');
  const tbody = document.getElementById('ocrVerifiedTableBody');
  const omittedBox = document.getElementById('ocrOmittedNotice');
  const omittedList = document.getElementById('ocrOmittedList');

  if (!resultsBox || !tbody) return;

  title.textContent = `Detected Materials (${data.verified_count})`;
  tbody.innerHTML = '';

  if (data.verified_materials.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#64748b; padding:12px;">No unambiguous civil construction materials identified in uploaded photos.</td></tr>`;
  } else {
    data.verified_materials.forEach(item => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="font-weight:600; color:#0f172a;">${item.material_name}</td>
        <td><span class="badge" style="background:#f1f5f9; color:#475569; font-size:11px;">${item.category}</span></td>
        <td style="font-weight:600;">${item.consumed_quantity.toLocaleString()}</td>
        <td>${item.unit}</td>
        <td>${item.emission_factor} <span style="font-size:10px; color:#64748b;">${item.ef_source}</span></td>
        <td style="color:#2563eb; font-weight:700;">${item.carbon_tonnes} tCO2e</td>
      `;
      tbody.appendChild(tr);
    });
  }

  // Handle omitted / ambiguous lines
  if (omittedBox && omittedList) {
    if (data.omitted_items && data.omitted_items.length > 0) {
      omittedList.innerHTML = '';
      data.omitted_items.forEach(o => {
        const li = document.createElement('li');
        li.textContent = `"${o.raw_text}" — ${o.reason}`;
        omittedList.appendChild(li);
      });
      omittedBox.style.display = 'block';
    } else {
      omittedBox.style.display = 'none';
    }
  }

  resultsBox.style.display = 'block';
}
