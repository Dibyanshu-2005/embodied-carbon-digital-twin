/**
 * 3D / Isometric Structural Digital Twin Visualizer
 * Renders concrete building elements (Footings, Columns, Slabs, Beams)
 * Supports dynamic orbit rotation, zoom, inspection, and carbon intensity heatmap coloring.
 */

class StructuralDigitalTwin {
  constructor(canvasId, onSelectElementCallback) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.onSelectElement = onSelectElementCallback;

    // Viewport & Camera state
    this.rotX = 0.55; // Angle of elevation (radians)
    this.rotY = -0.75; // Azimuth angle (radians)
    this.zoom = 28;   // Pixels per meter scale
    this.panX = 0;
    this.panY = -30;

    this.elements = [];
    this.selectedElementId = null;
    this.hoveredElementId = null;
    this.viewMode = 'carbon'; // 'carbon' | 'status' | 'type'

    this.isDragging = false;
    this.lastMouseX = 0;
    this.lastMouseY = 0;

    this.initCanvasSize();
    this.bindEvents();
    this.render();
  }

  initCanvasSize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.ctx.scale(dpr, dpr);
    this.displayWidth = rect.width;
    this.displayHeight = rect.height;
  }

  setElements(elements) {
    this.elements = elements || [];
    this.render();
  }

  setViewMode(mode) {
    this.viewMode = mode;
    this.render();
  }

  resetCamera() {
    this.rotX = 0.55;
    this.rotY = -0.75;
    this.zoom = 28;
    this.panX = 0;
    this.panY = -30;
    this.render();
  }

  bindEvents() {
    window.addEventListener('resize', () => {
      this.initCanvasSize();
      this.render();
    });

    this.canvas.addEventListener('mousedown', (e) => {
      this.isDragging = true;
      this.lastMouseX = e.clientX;
      this.lastMouseY = e.clientY;
    });

    window.addEventListener('mouseup', () => {
      this.isDragging = false;
    });

    this.canvas.addEventListener('mousemove', (e) => {
      if (this.isDragging) {
        const dx = e.clientX - this.lastMouseX;
        const dy = e.clientY - this.lastMouseY;
        this.rotY += dx * 0.008;
        this.rotX = Math.max(0.1, Math.min(1.4, this.rotX + dy * 0.008));
        this.lastMouseX = e.clientX;
        this.lastMouseY = e.clientY;
        this.render();
      } else {
        this.handleHover(e);
      }
    });

    this.canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
      this.zoom = Math.max(12, Math.min(80, this.zoom * zoomFactor));
      this.render();
    }, { passive: false });

    this.canvas.addEventListener('click', (e) => {
      this.handleClick(e);
    });
  }

  project(x, y, z) {
    // 3D Cartesian (x, y=height, z) to 2D isometric screen projection
    const cosY = Math.cos(this.rotY);
    const sinY = Math.sin(this.rotY);
    const cosX = Math.cos(this.rotX);
    const sinX = Math.sin(this.rotX);

    // Rotate around Y-axis
    const x1 = x * cosY - z * sinY;
    const z1 = x * sinY + z * cosY;

    // Rotate around X-axis (elevation tilt)
    const y2 = y * cosX - z1 * sinX;
    const z2 = y * sinX + z1 * cosX;

    const screenX = (this.displayWidth / 2) + this.panX + (x1 * this.zoom);
    const screenY = (this.displayHeight / 2) + this.panY - (y2 * this.zoom);

    return { x: screenX, y: screenY, depth: z2 };
  }

  getElementColor(el) {
    const isSelected = el.id === this.selectedElementId;
    const isHovered = el.id === this.hoveredElementId;

    if (this.viewMode === 'status') {
      if (el.status === 'Completed') return isSelected ? '#22c55e' : '#16a34a';
      if (el.status === 'In Progress') return isSelected ? '#60a5fa' : '#3b82f6';
      return isSelected ? '#94a3b8' : '#64748b';
    }

    if (this.viewMode === 'type') {
      if (el.type === 'footing') return '#8b5cf6';
      if (el.type === 'column') return '#3b82f6';
      if (el.type === 'slab') return '#0d9488';
      return '#64748b';
    }

    // Default 'carbon' intensity heatmap
    const intensity = el.carbon_intensity_kg_m3 || 300;
    if (intensity < 260) return isSelected ? '#34d399' : '#10b981'; // Low Carbon / Green
    if (intensity < 340) return isSelected ? '#fbbf24' : '#f59e0b'; // Moderate / Amber
    return isSelected ? '#f87171' : '#ef4444'; // Hotspot / Red
  }

  render() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.displayWidth, this.displayHeight);

    // 1. Draw Grid Ground Plane
    this.drawGroundGrid();

    // 2. Sort elements by depth (Painter's algorithm: draw back-to-front)
    const sorted = [...this.elements].map(el => {
      const projCenter = this.project(el.x, el.y, el.z);
      return { el, depth: projCenter.depth };
    }).sort((a, b) => b.depth - a.depth);

    // 3. Render 3D Cuboids for each structural element
    for (const item of sorted) {
      this.drawCuboid(item.el);
    }
  }

  drawGroundGrid() {
    const ctx = this.ctx;
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;
    const gridRange = 7;
    const step = 2;

    for (let i = -gridRange; i <= gridRange; i += step) {
      const p1 = this.project(i, -1.2, -gridRange);
      const p2 = this.project(i, -1.2, gridRange);
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();

      const p3 = this.project(-gridRange, -1.2, i);
      const p4 = this.project(gridRange, -1.2, i);
      ctx.beginPath();
      ctx.moveTo(p3.x, p3.y);
      ctx.lineTo(p4.x, p4.y);
      ctx.stroke();
    }
  }

  drawCuboid(el) {
    const ctx = this.ctx;
    const hw = el.w / 2;
    const hh = el.h / 2;
    const hd = el.d / 2;

    // 8 vertices of the cuboid box
    const v = [
      this.project(el.x - hw, el.y - hh, el.z - hd), // 0: bottom-left-back
      this.project(el.x + hw, el.y - hh, el.z - hd), // 1: bottom-right-back
      this.project(el.x + hw, el.y - hh, el.z + hd), // 2: bottom-right-front
      this.project(el.x - hw, el.y - hh, el.z + hd), // 3: bottom-left-front
      this.project(el.x - hw, el.y + hh, el.z - hd), // 4: top-left-back
      this.project(el.x + hw, el.y + hh, el.z - hd), // 5: top-right-back
      this.project(el.x + hw, el.y + hh, el.z + hd), // 6: top-right-front
      this.project(el.x - hw, el.y + hh, el.z + hd)  // 7: top-left-front
    ];

    const isSelected = el.id === this.selectedElementId;
    const isScheduled = el.status === 'Scheduled';
    const baseColor = this.getElementColor(el);

    // Faces with normal-based shading
    const faces = [
      { indices: [4, 5, 6, 7], shade: 1.15 }, // Top Face (brightest)
      { indices: [2, 6, 7, 3], shade: 0.95 }, // Front Face
      { indices: [1, 5, 6, 2], shade: 0.80 }, // Right Face
      { indices: [0, 4, 7, 3], shade: 0.70 }, // Left Face
      { indices: [0, 1, 5, 4], shade: 0.60 }  // Back Face
    ];

    // Check if face is facing camera (back-face culling)
    for (const face of faces) {
      const p0 = v[face.indices[0]];
      const p1 = v[face.indices[1]];
      const p2 = v[face.indices[2]];
      const signedArea = (p1.x - p0.x) * (p2.y - p0.y) - (p1.y - p0.y) * (p2.x - p0.x);

      if (signedArea < 0) { // Visible face
        ctx.beginPath();
        ctx.moveTo(p0.x, p0.y);
        for (let i = 1; i < face.indices.length; i++) {
          const pt = v[face.indices[i]];
          ctx.lineTo(pt.x, pt.y);
        }
        ctx.closePath();

        if (isScheduled) {
          ctx.fillStyle = 'rgba(71, 85, 105, 0.25)';
          ctx.fill();
          ctx.strokeStyle = '#64748b';
          ctx.lineWidth = 1;
          ctx.stroke();
        } else {
          ctx.fillStyle = this.adjustBrightness(baseColor, face.shade);
          ctx.fill();
          ctx.strokeStyle = isSelected ? '#ffffff' : 'rgba(15, 23, 42, 0.4)';
          ctx.lineWidth = isSelected ? 2.5 : 1;
          ctx.stroke();
        }
      }
    }

    // If selected, draw glowing label
    if (isSelected) {
      const topCenter = this.project(el.x, el.y + hh + 0.3, el.z);
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 11px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(el.name, topCenter.x, topCenter.y);
    }
  }

  adjustBrightness(hex, factor) {
    if (!hex.startsWith('#')) return hex;
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    const nr = Math.min(255, Math.floor(r * factor));
    const ng = Math.min(255, Math.floor(g * factor));
    const nb = Math.min(255, Math.floor(b * factor));
    return `rgb(${nr}, ${ng}, ${nb})`;
  }

  handleHover(e) {
    const rect = this.canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    let foundId = null;
    for (const el of this.elements) {
      const center = this.project(el.x, el.y, el.z);
      const rad = Math.max(15, (el.w + el.h) * this.zoom * 0.3);
      const dist = Math.hypot(mx - center.x, my - center.y);
      if (dist < rad) {
        foundId = el.id;
        break;
      }
    }

    if (this.hoveredElementId !== foundId) {
      this.hoveredElementId = foundId;
      this.canvas.style.cursor = foundId ? 'pointer' : 'default';
      this.render();
    }
  }

  handleClick(e) {
    const rect = this.canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    let selected = null;
    for (const el of this.elements) {
      const center = this.project(el.x, el.y, el.z);
      const rad = Math.max(15, (el.w + el.h) * this.zoom * 0.3);
      const dist = Math.hypot(mx - center.x, my - center.y);
      if (dist < rad) {
        selected = el;
        break;
      }
    }

    if (selected) {
      this.selectedElementId = selected.id;
      if (this.onSelectElement) this.onSelectElement(selected);
    } else {
      this.selectedElementId = null;
      if (this.onSelectElement) this.onSelectElement(null);
    }
    this.render();
  }
}

window.StructuralDigitalTwin = StructuralDigitalTwin;
