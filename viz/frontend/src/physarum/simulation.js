// Raw WebGL2 Physarum (slime mold) simulation engine, framework-free.
//
// Rendering pipeline adapted from Bewelge/Physarum-WebGL (MIT License,
// Copyright (c) 2021-2022 Benjamin Welge), commit
// e621c3ecb60c5c8a4d1b3446c7b389b083ea1908 (src/js/physarumRender.js,
// PingPongShader.js, Shader.js), re-implemented without Three.js so the
// component carries no new runtime dependency. Ping-pong float textures,
// agent update -> points -> diffuse/decay -> display passes are preserved,
// as are branching (sensor steering), aggregation (occupancy
// displacement) and trails (diffuse/decay). Food seeking, flowing front,
// smooth recovery, HiDPI coordinate mapping, visibility pause and disposal
// are new for Morphogenesis.
// License text: viz/static/licenses/physarum/Physarum-WebGL.LICENSE.MIT.txt

import {
  PASS_THROUGH_VERTEX,
  UPDATE_AGENTS_FRAGMENT,
  RENDER_POINTS_VERTEX,
  RENDER_POINTS_FRAGMENT,
  DIFFUSE_DECAY_FRAGMENT,
  DISPLAY_FRAGMENT,
} from './shaders';

export class PhysarumUnavailable extends Error {
  constructor(reason, message) {
    super(message);
    this.name = 'PhysarumUnavailable';
    this.reason = reason;
  }
}

// Species parameters, fixed for determinism (the reference randomizes per
// page load; ranges mirror its randomizeSettings()).
const SETTINGS = {
  decay: 0.975,
  dotSizes: [1, 1, 1],
  moveSpeed: [1.75, 1.85, 1.65],
  sensorDistance: [7.0, 8.5, 5.5],
  rotationAngle: [0.36, 0.43, 0.32],
  sensorAngle: [0.48, 0.56, 0.42],
  // All agents follow the same trail: one connected plasmodium, with varied
  // sensor geometry supplying small branching differences.
  attract0: [0.34, 0.34, 0.34],
  attract1: [0.34, 0.34, 0.34],
  attract2: [0.34, 0.34, 0.34],
  bgColor: [0x07 / 255, 0x0b / 255, 0x0d / 255], // page background #070b0d
  foodCoreRadius: 70, // px in view space
  foodTurn: 0.085, // gentle rad/frame chemotactic bias
  // Food strength easing rate (1/s): ~350 ms to converge, gives the smooth
  // recovery when the pointer leaves.
  foodEase: 3.0,
};

const rndFloat = (min, max) => min + (max - min) * Math.random();
const rndInt = (min, max) => Math.round(min + (max - min) * Math.random());

function compileShader(gl, type, source) {
  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(shader);
    gl.deleteShader(shader);
    throw new PhysarumUnavailable('shader-compile', log || 'shader compile failed');
  }
  return shader;
}

function createProgram(gl, vertexSource, fragmentSource) {
  const program = gl.createProgram();
  gl.attachShader(program, compileShader(gl, gl.VERTEX_SHADER, vertexSource));
  gl.attachShader(program, compileShader(gl, gl.FRAGMENT_SHADER, fragmentSource));
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    const log = gl.getProgramInfoLog(program);
    gl.deleteProgram(program);
    throw new PhysarumUnavailable('program-link', log || 'program link failed');
  }
  return program;
}

function createFloatTexture(gl, width, height, data) {
  const texture = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, texture);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32F, width, height, 0, gl.RGBA, gl.FLOAT, data || null);
  gl.bindTexture(gl.TEXTURE_2D, null);
  return texture;
}

function createTarget(gl, width, height, data) {
  const texture = createFloatTexture(gl, width, height, data);
  const fbo = gl.createFramebuffer();
  gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);
  const ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE;
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  if (!ok) {
    gl.deleteFramebuffer(fbo);
    gl.deleteTexture(texture);
    throw new PhysarumUnavailable('framebuffer', 'float framebuffer incomplete');
  }
  return { texture, fbo, width, height };
}

function disposeTarget(gl, target) {
  if (!target) return;
  gl.deleteFramebuffer(target.fbo);
  gl.deleteTexture(target.texture);
}

// A single elongated seed colony keeps the rear connected as its leading edge
// spreads into a fan. Sensor variants share one trail rather than separating.
function seedAgents(grid, viewWidth, viewHeight) {
  const count = grid * grid;
  const data = new Float32Array(count * 4);
  const cx = -Math.min(viewWidth * 0.18, 230);
  for (let i = 0; i < count; i++) {
    const id = i * 4;
    const team = Math.min(2, Math.floor((i / count) * 3));
    const ang = rndFloat(0, Math.PI * 2);
    const dis = Math.sqrt(Math.random()) * Math.min(viewHeight * 0.22, 145);
    data[id] = cx + dis * Math.cos(ang) * 1.25;
    data[id + 1] = dis * Math.sin(ang);
    data[id + 2] = rndFloat(-0.8, 0.8);
    data[id + 3] = team;
  }
  return data;
}

export class PhysarumSim {
  // grid: sim texture is grid x grid agents. maxDpr caps devicePixelRatio.
  constructor(canvas, { grid = 256, maxDpr = 2 } = {}) {
    this.canvas = canvas;
    this.grid = grid;
    this.maxDpr = maxDpr;
    this.settings = { ...SETTINGS };
    this.time = 0;
    this.running = false;
    this.disposed = false;
    this.food = { x: 0, y: 0, strength: 0, target: 0 };
    this.front = { x: 0, y: 0 };
    this.viewWidth = 0;
    this.viewHeight = 0;
    this.avgFrameMs = 0;
    this._lastTs = 0;
    this._raf = 0;
    this._frame = this._frame.bind(this);

    const gl = canvas.getContext('webgl2', {
      alpha: false,
      antialias: false,
      depth: false,
      stencil: false,
      preserveDrawingBuffer: false,
      powerPreference: 'high-performance',
    });
    if (!gl) {
      throw new PhysarumUnavailable('webgl2-unavailable', 'WebGL2 context could not be created');
    }
    if (!gl.getExtension('EXT_color_buffer_float')) {
      throw new PhysarumUnavailable('float-buffer-unavailable', 'EXT_color_buffer_float missing');
    }
    this.gl = gl;

    this._buildPrograms();
    this._buildGeometry();
    // Agent state textures are created lazily on the first resize(), once the
    // real view size is known, so clusters seed inside the actual viewport.

    this._onContextLost = (ev) => {
      ev.preventDefault();
      this.stop();
      this.disposed = true;
      if (this.onContextLost) this.onContextLost();
    };
    canvas.addEventListener('webglcontextlost', this._onContextLost);
  }

  _buildPrograms() {
    const gl = this.gl;
    this.updateProgram = createProgram(gl, PASS_THROUGH_VERTEX, UPDATE_AGENTS_FRAGMENT);
    this.pointsProgram = createProgram(gl, RENDER_POINTS_VERTEX, RENDER_POINTS_FRAGMENT);
    this.diffuseProgram = createProgram(gl, PASS_THROUGH_VERTEX, DIFFUSE_DECAY_FRAGMENT);
    this.displayProgram = createProgram(gl, PASS_THROUGH_VERTEX, DISPLAY_FRAGMENT);
    this.uniforms = {};
    for (const [name, program] of [
      ['update', this.updateProgram],
      ['points', this.pointsProgram],
      ['diffuse', this.diffuseProgram],
      ['display', this.displayProgram],
    ]) {
      const map = {};
      const n = gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS);
      for (let i = 0; i < n; i++) {
        const info = gl.getActiveUniform(program, i);
        map[info.name] = gl.getUniformLocation(program, info.name);
      }
      this.uniforms[name] = map;
    }
  }

  _buildGeometry() {
    const gl = this.gl;
    // Fullscreen triangle.
    this.quadVao = gl.createVertexArray();
    gl.bindVertexArray(this.quadVao);
    const quadBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, quadBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    for (const program of [this.updateProgram, this.diffuseProgram, this.displayProgram]) {
      const loc = gl.getAttribLocation(program, 'position');
      if (loc >= 0) {
        gl.enableVertexAttribArray(loc);
        gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
      }
    }
    gl.bindVertexArray(null);

    // Agent points: only a uv lookup attribute into the state texture.
    const count = this.grid * this.grid;
    const uvs = new Float32Array(count * 2);
    for (let i = 0; i < count; i++) {
      uvs[i * 2] = ((i % this.grid) + 0.5) / this.grid;
      uvs[i * 2 + 1] = (Math.floor(i / this.grid) + 0.5) / this.grid;
    }
    this.pointsVao = gl.createVertexArray();
    gl.bindVertexArray(this.pointsVao);
    const uvBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, uvBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, uvs, gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(this.pointsProgram, 'uv');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    gl.bindVertexArray(null);
    gl.bindBuffer(gl.ARRAY_BUFFER, null);
    this.agentCount = count;
  }

  _buildAgentTargets() {
    const gl = this.gl;
    const data = seedAgents(this.grid, Math.max(this.viewWidth, 2), Math.max(this.viewHeight, 2));
    this.agentRead = createTarget(gl, this.grid, this.grid, data);
    this.agentWrite = createTarget(gl, this.grid, this.grid, null);
  }

  // width/height are CSS pixels of the container.
  resize(cssWidth, cssHeight) {
    if (this.disposed || cssWidth < 2 || cssHeight < 2) return;
    const dpr = Math.min(window.devicePixelRatio || 1, this.maxDpr);
    const w = Math.max(2, Math.round(cssWidth * dpr));
    const h = Math.max(2, Math.round(cssHeight * dpr));
    if (w === this.viewWidth && h === this.viewHeight) return;
    this.viewWidth = w;
    this.viewHeight = h;
    if (!this.agentRead) {
      this.front.x = w * 0.2;
      this.front.y = h * 0.08;
    }
    this.canvas.width = w;
    this.canvas.height = h;
    const gl = this.gl;
    if (!this.agentRead) {
      this._buildAgentTargets();
    }
    disposeTarget(gl, this.trailRead);
    disposeTarget(gl, this.trailWrite);
    disposeTarget(gl, this.pointsTarget);
    this.trailRead = createTarget(gl, w, h, null);
    this.trailWrite = createTarget(gl, w, h, null);
    this.pointsTarget = createTarget(gl, w, h, null);
  }

  // Food position in view coordinates: centered origin, y up, backing pixels.
  setFood(x, y) {
    this.food.x = x;
    this.food.y = y;
  }

  // target 1 while the pointer is inside, 0 after it leaves; the strength
  // itself eases per frame so departure recovers smoothly.
  setFoodTarget(target) {
    this.food.target = target;
  }

  getAverageFrameMs() {
    return this.avgFrameMs;
  }

  // Read-only agent statistics (integration tests; also handy for tuning).
  // Returns null when float readback is unsupported.
  getAgentStats() {
    if (this.disposed || !this.agentRead) return null;
    const gl = this.gl;
    const count = this.grid * this.grid;
    const buf = new Float32Array(count * 4);
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.agentRead.fbo);
    try {
      gl.readPixels(0, 0, this.grid, this.grid, gl.RGBA, gl.FLOAT, buf);
    } catch (err) {
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      return null;
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    let cx = 0;
    let cy = 0;
    let foodDist = 0;
    for (let i = 0; i < count; i++) {
      const x = buf[i * 4];
      const y = buf[i * 4 + 1];
      cx += x;
      cy += y;
      foodDist += Math.hypot(x - this.food.x, y - this.food.y);
    }
    return {
      centroid: { x: cx / count, y: cy / count },
      meanFoodDistance: foodDist / count,
    };
  }

  start() {
    if (this.running || this.disposed || !this.trailRead || !this.agentRead) return;
    this.running = true;
    this._lastTs = 0;
    this._raf = requestAnimationFrame(this._frame);
  }

  stop() {
    this.running = false;
    if (this._raf) {
      cancelAnimationFrame(this._raf);
      this._raf = 0;
    }
  }

  _frame(ts) {
    if (!this.running) return;
    this._raf = requestAnimationFrame(this._frame);
    if (this._lastTs) {
      const dt = Math.min(100, ts - this._lastTs);
      this.avgFrameMs = this.avgFrameMs ? this.avgFrameMs * 0.95 + dt * 0.05 : dt;
      // Ease food strength toward target (time-based, frame-rate independent).
      const k = 1 - Math.exp(-this.settings.foodEase * (dt / 1000));
      this.food.strength += (this.food.target - this.food.strength) * k;
      if (Math.abs(this.food.strength - this.food.target) < 0.001) {
        this.food.strength = this.food.target;
      }
      // The anterior margin advances over time; the posterior anchor stays
      // connected, rather than teleporting the entire mass with the cursor.
      const frontEase = 1 - Math.exp(-(this.food.target ? 1.7 : 3.8) * (dt / 1000));
      // Departure immediately changes the destination to the home position.
      // Only the visual position is eased; old food coordinates cannot hold
      // the organism offscreen during the recovery interval.
      const targetX = this.food.target
        ? Math.max(-this.viewWidth * 0.15, Math.min(this.viewWidth * 0.35, this.food.x))
        : this.viewWidth * 0.2;
      const targetY = this.food.target
        ? Math.max(-this.viewHeight * 0.2, Math.min(this.viewHeight * 0.2, this.food.y))
        : this.viewHeight * 0.08;
      this.front.x += (targetX - this.front.x) * frontEase;
      this.front.y += (targetY - this.front.y) * frontEase;
    }
    this._lastTs = ts;
    this._step();
  }

  _bindTexture(unit, texture, location) {
    const gl = this.gl;
    gl.activeTexture(gl.TEXTURE0 + unit);
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.uniform1i(location, unit);
  }

  _step() {
    const gl = this.gl;
    const s = this.settings;
    const w = this.viewWidth;
    const h = this.viewHeight;
    this.time += 1;

    // 1. Agent update (ping-pong on the sim grid).
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.agentWrite.fbo);
    gl.viewport(0, 0, this.grid, this.grid);
    gl.useProgram(this.updateProgram);
    gl.bindVertexArray(this.quadVao);
    const u = this.uniforms.update;
    this._bindTexture(0, this.agentRead.texture, u.inputTexture);
    this._bindTexture(1, this.trailRead.texture, u.trailTexture);
    this._bindTexture(2, this.pointsTarget.texture, u.pointsTexture);
    gl.uniform2f(u.resolution, w, h);
    gl.uniform1f(u.time, this.time);
    gl.uniform2f(u.foodPos, this.food.x, this.food.y);
    gl.uniform1f(u.foodStrength, this.food.strength);
    gl.uniform1f(u.foodCoreRadius, s.foodCoreRadius);
    gl.uniform1f(u.foodTurn, s.foodTurn);
    gl.uniform3fv(u.moveSpeed, s.moveSpeed);
    gl.uniform3fv(u.rotationAngle, s.rotationAngle);
    gl.uniform3fv(u.sensorDistance, s.sensorDistance);
    gl.uniform3fv(u.sensorAngle, s.sensorAngle);
    gl.uniform3fv(u.attract0, s.attract0);
    gl.uniform3fv(u.attract1, s.attract1);
    gl.uniform3fv(u.attract2, s.attract2);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    [this.agentRead, this.agentWrite] = [this.agentWrite, this.agentRead];

    // 2. Points pass: draw agents into the occupancy texture.
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.pointsTarget.fbo);
    gl.viewport(0, 0, w, h);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(this.pointsProgram);
    gl.bindVertexArray(this.pointsVao);
    const p = this.uniforms.points;
    this._bindTexture(0, this.agentRead.texture, p.positionTexture);
    gl.uniform2f(p.resolution, w, h);
    gl.uniform3fv(p.dotSizes, s.dotSizes);
    gl.drawArrays(gl.POINTS, 0, this.agentCount);

    // 3. Diffuse + decay the trail, adding fresh points (ping-pong).
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.trailWrite.fbo);
    gl.viewport(0, 0, w, h);
    gl.useProgram(this.diffuseProgram);
    gl.bindVertexArray(this.quadVao);
    const d = this.uniforms.diffuse;
    this._bindTexture(0, this.pointsTarget.texture, d.points);
    this._bindTexture(1, this.trailRead.texture, d.inputTexture);
    gl.uniform2f(d.resolution, w, h);
    gl.uniform1f(d.decay, s.decay);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    [this.trailRead, this.trailWrite] = [this.trailWrite, this.trailRead];

    // 4. Composite to the canvas.
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, w, h);
    gl.useProgram(this.displayProgram);
    gl.bindVertexArray(this.quadVao);
    const f = this.uniforms.display;
    this._bindTexture(0, this.trailRead.texture, f.diffuseTexture);
    this._bindTexture(1, this.pointsTarget.texture, f.pointsTexture);
    gl.uniform3fv(f.bgColor, s.bgColor);
    gl.uniform2f(f.resolution, w, h);
    gl.uniform1f(f.time, this.time);
    gl.uniform2f(f.frontPos, this.front.x, this.front.y);
    gl.drawArrays(gl.TRIANGLES, 0, 3);

    gl.bindVertexArray(null);
  }

  dispose() {
    if (this.disposed) return;
    this.stop();
    this.disposed = true;
    const gl = this.gl;
    this.canvas.removeEventListener('webglcontextlost', this._onContextLost);
    disposeTarget(gl, this.agentRead);
    disposeTarget(gl, this.agentWrite);
    disposeTarget(gl, this.trailRead);
    disposeTarget(gl, this.trailWrite);
    disposeTarget(gl, this.pointsTarget);
    gl.deleteVertexArray(this.quadVao);
    gl.deleteVertexArray(this.pointsVao);
    for (const program of [this.updateProgram, this.pointsProgram, this.diffuseProgram, this.displayProgram]) {
      gl.deleteProgram(program);
    }
    const lose = gl.getExtension('WEBGL_lose_context');
    if (lose) lose.loseContext();
  }
}

export const QUALITY_LEVELS = [
  { grid: 256, maxDpr: 2 }, // desktop default
  { grid: 128, maxDpr: 1 }, // degraded / touch default
];
