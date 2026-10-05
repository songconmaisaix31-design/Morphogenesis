/* ============================================================
 * 背景层 · 黏菌拓扑场（观测台背景，持续生长，永不停止的网络重塑）
 *
 * 基于普通 WebGL2 vertex/fragment shader 的 Physarum 引擎，
 * 复用开场页 physarum-landing.html 已验证的 PhysarumSim 实现
 * （源：Bewelge/Physarum-WebGL, MIT License, Copyright (c) 2021-2022
 *  Benjamin Welge，commit e621c3ecb60c5c8a4d1b3446c7b389b083ea1908）。
 *
 * 观测台改造：
 *   · 目标 canvas 为 #bgPhysarum（index.html 内已声明）
 *   · 亮底淡金痕：纸色 #f5f5f1 白底 + 金色系痕迹（低对比，不干扰前景阅读）
 *   · grid 256 = 65,536 agents 常驻低耗
 *   · 无指针交互（不注册任何 pointer 事件，背景不抢输入）
 *   · WebGL2 不可用 / shader 编译失败时静默降级（canvas.remove()，不抛错）
 *
 * 独立自包含：不依赖 data.js / app.js。
 * 许可文本：viz/static/licenses/physarum/Physarum-WebGL.LICENSE.MIT.txt
 * ============================================================ */
(function () {
  'use strict';

  var canvas = document.getElementById('bgPhysarum');
  if (!canvas) return;

  /* ================= shaders（GLSL ES 3.00，普通 shader） ================= */

  var PASS_THROUGH_VERTEX = '#version 300 es\n' +
    'in vec2 position;\n' +
    'out vec2 vUv;\n' +
    'void main() {\n' +
    '    vUv = position * 0.5 + 0.5;\n' +
    '    gl_Position = vec4(position, 0.0, 1.0);\n' +
    '}\n';

  var UPDATE_AGENTS_FRAGMENT = '#version 300 es\n' +
    'precision highp float;\n' +
    'uniform sampler2D inputTexture;\n' +
    'uniform sampler2D trailTexture;\n' +
    'uniform sampler2D pointsTexture;\n' +
    'uniform vec2 resolution;\n' +
    'uniform vec3 moveSpeed;\n' +
    'uniform vec3 rotationAngle;\n' +
    'uniform vec3 sensorDistance;\n' +
    'uniform vec3 sensorAngle;\n' +
    'uniform vec3 attract0;\n' +
    'uniform vec3 attract1;\n' +
    'uniform vec3 attract2;\n' +
    'out vec4 outColor;\n' +
    'const float PI  = 3.14159265358979323846264;\n' +
    'const float PI2 = PI * 2.0;\n' +
    'float sampleTrail(vec2 pos, float team) {\n' +
    '    vec3 attract = attract0;\n' +
    '    if (team == 1.0) { attract = attract1; }\n' +
    '    else if (team == 2.0) { attract = attract2; }\n' +
    '    float val = 0.0;\n' +
    '    const float searchArea = 1.0;\n' +
    '    vec2 uv = pos / resolution + 0.5;\n' +
    '    for (float i = 0.0; i < searchArea * 2.0 + 1.0; i++) {\n' +
    '        for (float j = 0.0; j < searchArea * 2.0 + 1.0; j++) {\n' +
    '            vec3 pixel = texture(trailTexture, uv + vec2(i - searchArea, j - searchArea) / resolution).rgb;\n' +
    '            val += dot(pixel, attract) * (1.0 / pow(2.0 * searchArea + 1.0, 2.0));\n' +
    '        }\n' +
    '    }\n' +
    '    return val;\n' +
    '}\n' +
    'float occupancy(vec2 pos) {\n' +
    '    vec3 pixel = texture(pointsTexture, pos / resolution + 0.5).rgb;\n' +
    '    return pixel.r + pixel.g + pixel.b;\n' +
    '}\n' +
    'vec2 wrapPos(vec2 pos) {\n' +
    '    return fract((pos + resolution * 0.5) / resolution) * resolution - resolution * 0.5;\n' +
    '}\n' +
    'void main() {\n' +
    '    vec4 data = texelFetch(inputTexture, ivec2(gl_FragCoord.xy), 0);\n' +
    '    vec2 position = data.xy;\n' +
    '    float direction = data.z;\n' +
    '    float team = data.w;\n' +
    '    int teamInt = int(team + 0.5);\n' +
    '    float angDif = sensorAngle[teamInt];\n' +
    '    float sensorDist = sensorDistance[teamInt];\n' +
    '    float leftAng = direction - angDif;\n' +
    '    float rightAng = direction + angDif;\n' +
    '    vec2 leftPos  = position + vec2(cos(leftAng),  sin(leftAng))  * sensorDist;\n' +
    '    vec2 midPos   = position + vec2(cos(direction), sin(direction)) * sensorDist;\n' +
    '    vec2 rightPos = position + vec2(cos(rightAng), sin(rightAng)) * sensorDist;\n' +
    '    float leftVal  = sampleTrail(leftPos, team);\n' +
    '    float midVal   = sampleTrail(midPos, team);\n' +
    '    float rightVal = sampleTrail(rightPos, team);\n' +
    '    float rotationAng = rotationAngle[teamInt];\n' +
    '    if (midVal > rightVal && midVal > leftVal) {\n' +
    '    } else if (midVal < rightVal && midVal < leftVal) {\n' +
    '        direction += (0.5 - floor(fract(sin(dot(position + gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453) + 0.5)) * rotationAng;\n' +
    '    } else if (rightVal > midVal && rightVal > leftVal) {\n' +
    '        direction += rotationAng;\n' +
    '    } else if (leftVal > midVal && leftVal > rightVal) {\n' +
    '        direction -= rotationAng;\n' +
    '    }\n' +
    '    float speed = moveSpeed[teamInt];\n' +
    '    vec2 newPosition = position + vec2(cos(direction), sin(direction)) * speed;\n' +
    '    bool blocked = occupancy(newPosition) > 0.0;\n' +
    '    if (blocked) {\n' +
    '        newPosition = position;\n' +
    '        direction += PI2 / 4.0;\n' +
    '    }\n' +
    '    newPosition = wrapPos(newPosition);\n' +
    '    outColor = vec4(newPosition, direction, team);\n' +
    '}\n';

  var RENDER_POINTS_VERTEX = '#version 300 es\n' +
    'in vec2 uv;\n' +
    'uniform sampler2D positionTexture;\n' +
    'uniform vec2 resolution;\n' +
    'uniform vec3 dotSizes;\n' +
    'out float team;\n' +
    'void main() {\n' +
    '    vec4 data = texture(positionTexture, uv);\n' +
    '    gl_Position = vec4(data.xy / (resolution * 0.5), 0.0, 1.0);\n' +
    '    team = data.w;\n' +
    '    gl_PointSize = dotSizes[int(data.w + 0.5)];\n' +
    '}\n';

  var RENDER_POINTS_FRAGMENT = '#version 300 es\n' +
    'precision highp float;\n' +
    'in float team;\n' +
    'out vec4 outColor;\n' +
    'void main() {\n' +
    '    vec3 c = team < 0.5 ? vec3(1.0, 0.0, 0.0) : team < 1.5 ? vec3(0.0, 1.0, 0.0) : vec3(0.0, 0.0, 1.0);\n' +
    '    outColor = vec4(c, 1.0);\n' +
    '}\n';

  var DIFFUSE_DECAY_FRAGMENT = '#version 300 es\n' +
    'precision highp float;\n' +
    'uniform sampler2D points;\n' +
    'uniform sampler2D inputTexture;\n' +
    'uniform vec2 resolution;\n' +
    'uniform float decay;\n' +
    'in vec2 vUv;\n' +
    'out vec4 outColor;\n' +
    'void main() {\n' +
    '    vec3 pixelPoint = texture(points, vUv).rgb;\n' +
    '    vec3 col = vec3(0.0);\n' +
    '    const float dim = 1.0;\n' +
    '    float weight = 1.0 / pow(2.0 * dim + 1.0, 2.0);\n' +
    '    for (float i = -dim; i <= dim; i++) {\n' +
    '        for (float j = -dim; j <= dim; j++) {\n' +
    '            col += texture(inputTexture, (gl_FragCoord.xy + vec2(i, j)) / resolution).rgb * weight;\n' +
    '        }\n' +
    '    }\n' +
    '    outColor = vec4(clamp(col * decay + pixelPoint, 0.0, 1.0), 1.0);\n' +
    '}\n';

  /* 亮底淡金痕：纸色底 → 金色痕迹（轨迹越浓越靠近金色，整体低对比） */
  var DISPLAY_FRAGMENT = '#version 300 es\n' +
    'precision highp float;\n' +
    'uniform sampler2D diffuseTexture;\n' +
    'uniform sampler2D pointsTexture;\n' +
    'uniform vec3 col0;\n' +
    'uniform vec3 col1;\n' +
    'uniform vec3 col2;\n' +
    'uniform vec3 bgColor;\n' +
    'uniform float trailOpacity;\n' +
    'uniform float dotOpacity;\n' +
    'in vec2 vUv;\n' +
    'out vec4 outColor;\n' +
    'void main() {\n' +
    '    vec3 trail = texture(diffuseTexture, vUv).rgb;\n' +
    '    vec3 dots = texture(pointsTexture, vUv).rgb;\n' +
    '    vec3 mixed = trail * trailOpacity + dots * dotOpacity;\n' +
    '    vec3 gold = mixed.r * col0 + mixed.g * col1 + mixed.b * col2;\n' +
    '    float density = clamp(mixed.r + mixed.g + mixed.b, 0.0, 1.0);\n' +
    '    vec3 col = mix(bgColor, gold, density * 0.55);\n' +
    '    outColor = vec4(col, 1.0);\n' +
    '}\n';

  /* ================= simulation engine ================= */

  function PhysarumUnavailable(reason, message) {
    var e = new Error(message);
    e.name = 'PhysarumUnavailable';
    e.reason = reason;
    return e;
  }

  var SETTINGS = {
    decay: 0.95,
    trailOpacity: 1.0,
    dotOpacity: 0.2,
    dotSizes: [1, 1, 1],
    moveSpeed: [1.7, 2.1, 1.4],
    sensorDistance: [6.0, 9.0, 4.5],
    rotationAngle: [0.5, 0.65, 0.4],
    sensorAngle: [0.5, 0.7, 0.45],
    attract0: [1.0, -0.15, -0.15],
    attract1: [-0.15, 1.0, -0.15],
    attract2: [-0.15, -0.15, 1.0],
    /* 金色族三物种：亮金 / 强调金 / 深金（痕迹整体克制，不抢前景） */
    col0: [0.961, 0.765, 0.231], /* #f5c33b 亮金 */
    col1: [0.788, 0.576, 0.039], /* #c9930a 强调金 */
    col2: [0.722, 0.525, 0.043], /* #b8860b 深金 */
    bgColor: [0.961, 0.961, 0.945], /* #f5f5f1 纸色白底 */
  };

  function rndFloat(min, max) { return min + (max - min) * Math.random(); }
  function rndInt(min, max) { return Math.round(min + (max - min) * Math.random()); }

  function compileShader(gl, type, source) {
    var shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      var log = gl.getShaderInfoLog(shader);
      gl.deleteShader(shader);
      throw PhysarumUnavailable('shader-compile', log || 'shader compile failed');
    }
    return shader;
  }

  function createProgram(gl, vertexSource, fragmentSource) {
    var program = gl.createProgram();
    gl.attachShader(program, compileShader(gl, gl.VERTEX_SHADER, vertexSource));
    gl.attachShader(program, compileShader(gl, gl.FRAGMENT_SHADER, fragmentSource));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      var log = gl.getProgramInfoLog(program);
      gl.deleteProgram(program);
      throw PhysarumUnavailable('program-link', log || 'program link failed');
    }
    return program;
  }

  function createFloatTexture(gl, width, height, data) {
    var texture = gl.createTexture();
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
    var texture = createFloatTexture(gl, width, height, data);
    var fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);
    var ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE;
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    if (!ok) {
      gl.deleteFramebuffer(fbo);
      gl.deleteTexture(texture);
      throw PhysarumUnavailable('framebuffer', 'float framebuffer incomplete');
    }
    return { texture: texture, fbo: fbo, width: width, height: height };
  }

  function disposeTarget(gl, target) {
    if (!target) return;
    gl.deleteFramebuffer(target.fbo);
    gl.deleteTexture(target.texture);
  }

  function seedAgents(grid, viewWidth, viewHeight) {
    var count = grid * grid;
    var data = new Float32Array(count * 4);
    var marg = Math.min(viewWidth, viewHeight) * 0.2;
    var clusters = [0, 1, 2].map(function () {
      return {
        x: rndFloat(marg, Math.max(marg + 1, viewWidth - marg)) - viewWidth * 0.5,
        y: rndFloat(marg, Math.max(marg + 1, viewHeight - marg)) - viewHeight * 0.5,
      };
    });
    for (var i = 0; i < count; i++) {
      var id = i * 4;
      var team = Math.min(2, Math.floor((i / count) * 3));
      var base = clusters[team];
      var ang = rndFloat(0, Math.PI * 2);
      var dis = rndFloat(30, 90) + team * 50 + rndFloat(0, 40);
      data[id] = base.x + dis * Math.cos(ang);
      data[id + 1] = base.y + dis * Math.sin(ang);
      data[id + 2] = ang;
      data[id + 3] = team;
    }
    return data;
  }

  function PhysarumSim(canvas, opts) {
    opts = opts || {};
    this.canvas = canvas;
    this.grid = opts.grid || 256;
    this.maxDpr = opts.maxDpr || 1.5;
    this.settings = Object.assign({}, SETTINGS);
    this.time = 0;
    this.running = false;
    this.disposed = false;
    this.viewWidth = 0;
    this.viewHeight = 0;
    this._lastTs = 0;
    this._raf = 0;
    this._frame = this._frame.bind(this);

    var gl = canvas.getContext('webgl2', {
      alpha: false,
      antialias: false,
      depth: false,
      stencil: false,
      preserveDrawingBuffer: false,
      powerPreference: 'high-performance',
    });
    if (!gl) throw PhysarumUnavailable('webgl2-unavailable', 'WebGL2 context could not be created');
    if (!gl.getExtension('EXT_color_buffer_float')) {
      throw PhysarumUnavailable('float-buffer-unavailable', 'EXT_color_buffer_float missing');
    }
    this.gl = gl;

    this._buildPrograms();
    this._buildGeometry();

    this._onContextLost = function (ev) {
      ev.preventDefault();
      this.stop();
      this.disposed = true;
    }.bind(this);
    canvas.addEventListener('webglcontextlost', this._onContextLost);
  }

  PhysarumSim.prototype._buildPrograms = function () {
    var gl = this.gl;
    this.updateProgram = createProgram(gl, PASS_THROUGH_VERTEX, UPDATE_AGENTS_FRAGMENT);
    this.pointsProgram = createProgram(gl, RENDER_POINTS_VERTEX, RENDER_POINTS_FRAGMENT);
    this.diffuseProgram = createProgram(gl, PASS_THROUGH_VERTEX, DIFFUSE_DECAY_FRAGMENT);
    this.displayProgram = createProgram(gl, PASS_THROUGH_VERTEX, DISPLAY_FRAGMENT);
    this.uniforms = {};
    var self = this;
    [['update', this.updateProgram], ['points', this.pointsProgram], ['diffuse', this.diffuseProgram], ['display', this.displayProgram]].forEach(function (pair) {
      var name = pair[0], program = pair[1];
      var map = {};
      var n = gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS);
      for (var i = 0; i < n; i++) {
        var info = gl.getActiveUniform(program, i);
        map[info.name] = gl.getUniformLocation(program, info.name);
      }
      self.uniforms[name] = map;
    });
  };

  PhysarumSim.prototype._buildGeometry = function () {
    var gl = this.gl;
    this.quadVao = gl.createVertexArray();
    gl.bindVertexArray(this.quadVao);
    var quadBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, quadBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    [this.updateProgram, this.diffuseProgram, this.displayProgram].forEach(function (program) {
      var loc = gl.getAttribLocation(program, 'position');
      if (loc >= 0) {
        gl.enableVertexAttribArray(loc);
        gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
      }
    });
    gl.bindVertexArray(null);

    var count = this.grid * this.grid;
    var uvs = new Float32Array(count * 2);
    for (var i = 0; i < count; i++) {
      uvs[i * 2] = ((i % this.grid) + 0.5) / this.grid;
      uvs[i * 2 + 1] = (Math.floor(i / this.grid) + 0.5) / this.grid;
    }
    this.pointsVao = gl.createVertexArray();
    gl.bindVertexArray(this.pointsVao);
    var uvBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, uvBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, uvs, gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(this.pointsProgram, 'uv');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    gl.bindVertexArray(null);
    gl.bindBuffer(gl.ARRAY_BUFFER, null);
    this.agentCount = count;
  };

  PhysarumSim.prototype._buildAgentTargets = function () {
    var gl = this.gl;
    var data = seedAgents(this.grid, Math.max(this.viewWidth, 2), Math.max(this.viewHeight, 2));
    this.agentRead = createTarget(gl, this.grid, this.grid, data);
    this.agentWrite = createTarget(gl, this.grid, this.grid, null);
  };

  PhysarumSim.prototype.resize = function (cssWidth, cssHeight) {
    if (this.disposed || cssWidth < 2 || cssHeight < 2) return;
    var dpr = Math.min(window.devicePixelRatio || 1, this.maxDpr);
    var w = Math.max(2, Math.round(cssWidth * dpr));
    var h = Math.max(2, Math.round(cssHeight * dpr));
    if (w === this.viewWidth && h === this.viewHeight) return;
    this.viewWidth = w;
    this.viewHeight = h;
    this.canvas.width = w;
    this.canvas.height = h;
    var gl = this.gl;
    if (!this.agentRead) this._buildAgentTargets();
    disposeTarget(gl, this.trailRead);
    disposeTarget(gl, this.trailWrite);
    disposeTarget(gl, this.pointsTarget);
    this.trailRead = createTarget(gl, w, h, null);
    this.trailWrite = createTarget(gl, w, h, null);
    this.pointsTarget = createTarget(gl, w, h, null);
  };

  PhysarumSim.prototype.start = function () {
    if (this.running || this.disposed || !this.trailRead || !this.agentRead) return;
    this.running = true;
    this._lastTs = 0;
    this._raf = requestAnimationFrame(this._frame);
  };

  PhysarumSim.prototype.stop = function () {
    this.running = false;
    if (this._raf) { cancelAnimationFrame(this._raf); this._raf = 0; }
  };

  PhysarumSim.prototype._frame = function (ts) {
    if (!this.running) return;
    this._raf = requestAnimationFrame(this._frame);
    this._lastTs = ts;
    this._step();
  };

  PhysarumSim.prototype._bindTexture = function (unit, texture, location) {
    var gl = this.gl;
    gl.activeTexture(gl.TEXTURE0 + unit);
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.uniform1i(location, unit);
  };

  PhysarumSim.prototype._step = function () {
    var gl = this.gl;
    var s = this.settings;
    var w = this.viewWidth;
    var h = this.viewHeight;
    this.time += 1;

    gl.bindFramebuffer(gl.FRAMEBUFFER, this.agentWrite.fbo);
    gl.viewport(0, 0, this.grid, this.grid);
    gl.useProgram(this.updateProgram);
    gl.bindVertexArray(this.quadVao);
    var u = this.uniforms.update;
    this._bindTexture(0, this.agentRead.texture, u.inputTexture);
    this._bindTexture(1, this.trailRead.texture, u.trailTexture);
    this._bindTexture(2, this.pointsTarget.texture, u.pointsTexture);
    gl.uniform2f(u.resolution, w, h);
    gl.uniform3fv(u.moveSpeed, s.moveSpeed);
    gl.uniform3fv(u.rotationAngle, s.rotationAngle);
    gl.uniform3fv(u.sensorDistance, s.sensorDistance);
    gl.uniform3fv(u.sensorAngle, s.sensorAngle);
    gl.uniform3fv(u.attract0, s.attract0);
    gl.uniform3fv(u.attract1, s.attract1);
    gl.uniform3fv(u.attract2, s.attract2);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    var ar = this.agentRead; this.agentRead = this.agentWrite; this.agentWrite = ar;

    gl.bindFramebuffer(gl.FRAMEBUFFER, this.pointsTarget.fbo);
    gl.viewport(0, 0, w, h);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(this.pointsProgram);
    gl.bindVertexArray(this.pointsVao);
    var p = this.uniforms.points;
    this._bindTexture(0, this.agentRead.texture, p.positionTexture);
    gl.uniform2f(p.resolution, w, h);
    gl.uniform3fv(p.dotSizes, s.dotSizes);
    gl.drawArrays(gl.POINTS, 0, this.agentCount);

    gl.bindFramebuffer(gl.FRAMEBUFFER, this.trailWrite.fbo);
    gl.viewport(0, 0, w, h);
    gl.useProgram(this.diffuseProgram);
    gl.bindVertexArray(this.quadVao);
    var d = this.uniforms.diffuse;
    this._bindTexture(0, this.pointsTarget.texture, d.points);
    this._bindTexture(1, this.trailRead.texture, d.inputTexture);
    gl.uniform2f(d.resolution, w, h);
    gl.uniform1f(d.decay, s.decay);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    var tr = this.trailRead; this.trailRead = this.trailWrite; this.trailWrite = tr;

    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, w, h);
    gl.useProgram(this.displayProgram);
    gl.bindVertexArray(this.quadVao);
    var f = this.uniforms.display;
    this._bindTexture(0, this.trailRead.texture, f.diffuseTexture);
    this._bindTexture(1, this.pointsTarget.texture, f.pointsTexture);
    gl.uniform3fv(f.col0, s.col0);
    gl.uniform3fv(f.col1, s.col1);
    gl.uniform3fv(f.col2, s.col2);
    gl.uniform3fv(f.bgColor, s.bgColor);
    gl.uniform1f(f.trailOpacity, s.trailOpacity);
    gl.uniform1f(f.dotOpacity, s.dotOpacity);
    gl.drawArrays(gl.TRIANGLES, 0, 3);

    gl.bindVertexArray(null);
  };

  PhysarumSim.prototype.dispose = function () {
    if (this.disposed) return;
    this.stop();
    this.disposed = true;
    var gl = this.gl;
    this.canvas.removeEventListener('webglcontextlost', this._onContextLost);
    disposeTarget(gl, this.agentRead);
    disposeTarget(gl, this.agentWrite);
    disposeTarget(gl, this.trailRead);
    disposeTarget(gl, this.trailWrite);
    disposeTarget(gl, this.pointsTarget);
    gl.deleteVertexArray(this.quadVao);
    gl.deleteVertexArray(this.pointsVao);
    [this.updateProgram, this.pointsProgram, this.diffuseProgram, this.displayProgram].forEach(function (program) {
      gl.deleteProgram(program);
    });
    var lose = gl.getExtension('WEBGL_lose_context');
    if (lose) lose.loseContext();
  };

  /* ================= bootstrap ================= */

  var sim;
  try {
    sim = new PhysarumSim(canvas, { grid: 256, maxDpr: 1.5 });
  } catch (err) {
    canvas.remove();
    return;
  }

  var applySize = function () { sim.resize(window.innerWidth, window.innerHeight); };
  applySize();
  window.addEventListener('resize', applySize);

  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduced) {
    /* 静态降级：渲染固定帧后定格，不持续动画 */
    for (var i = 0; i < 220; i++) sim._step();
  } else {
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) sim.stop(); else sim.start();
    });
    sim.start();
  }
})();
