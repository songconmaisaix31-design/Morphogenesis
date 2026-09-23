// GLSL sources for the Physarum WebGL2 simulation.
//
// Adapted from Bewelge/Physarum-WebGL (MIT License, Copyright (c) 2021-2022
// Benjamin Welge), commit e621c3ecb60c5c8a4d1b3446c7b389b083ea1908,
// src/js/Shaders/*.js — which itself credits nicoptere/physarum for the
// ping-pong / diffuse-decay shader logic. Ported from GLSL ES 1.00 (Three.js
// ShaderMaterial) to raw GLSL ES 3.00.
// Full license text: viz/static/licenses/physarum/Physarum-WebGL.LICENSE.MIT.txt

// Fullscreen triangle. `position` is a vec2 in clip space.
export const PASS_THROUGH_VERTEX = `#version 300 es
in vec2 position;
out vec2 vUv;
void main() {
    vUv = position * 0.5 + 0.5;
    gl_Position = vec4(position, 0.0, 1.0);
}
`;

// Agent update pass. One fragment per particle on the sim grid; rg = position
// (centered coords, y up), b = heading, a = species. Sensor/turn structure
// follows UpdateDotsFragment.js of the reference. No pointer input is used.
export const UPDATE_AGENTS_FRAGMENT = `#version 300 es
precision highp float;

uniform sampler2D inputTexture;   // previous agent states (sim grid)
uniform sampler2D trailTexture;   // aggregated pheromone trail (view sized)
uniform sampler2D pointsTexture;  // occupied pixels this frame (view sized)

uniform vec2 resolution;          // view (trail) resolution in px

uniform vec3 moveSpeed;
uniform vec3 rotationAngle;
uniform vec3 sensorDistance;
uniform vec3 sensorAngle;
uniform vec3 attract0;
uniform vec3 attract1;
uniform vec3 attract2;

out vec4 outColor;

const float PI  = 3.14159265358979323846264;
const float PI2 = PI * 2.0;

float sampleTrail(vec2 pos, float team) {
    vec3 attract = attract0;
    if (team == 1.0) {
        attract = attract1;
    } else if (team == 2.0) {
        attract = attract2;
    }
    float val = 0.0;
    const float searchArea = 1.0;
    vec2 uv = pos / resolution + 0.5;
    for (float i = 0.0; i < searchArea * 2.0 + 1.0; i++) {
        for (float j = 0.0; j < searchArea * 2.0 + 1.0; j++) {
            vec3 pixel = texture(trailTexture, uv + vec2(i - searchArea, j - searchArea) / resolution).rgb;
            val += dot(pixel, attract) * (1.0 / pow(2.0 * searchArea + 1.0, 2.0));
        }
    }
    return val;
}

float occupancy(vec2 pos) {
    vec3 pixel = texture(pointsTexture, pos / resolution + 0.5).rgb;
    return pixel.r + pixel.g + pixel.b;
}

vec2 wrapPos(vec2 pos) {
    return fract((pos + resolution * 0.5) / resolution) * resolution - resolution * 0.5;
}

void main() {
    vec4 data = texelFetch(inputTexture, ivec2(gl_FragCoord.xy), 0);
    vec2 position = data.xy;
    float direction = data.z;
    float team = data.w;
    int teamInt = int(team + 0.5);

    float angDif = sensorAngle[teamInt];
    float sensorDist = sensorDistance[teamInt];
    float leftAng = direction - angDif;
    float rightAng = direction + angDif;

    vec2 leftPos  = position + vec2(cos(leftAng),  sin(leftAng))  * sensorDist;
    vec2 midPos   = position + vec2(cos(direction), sin(direction)) * sensorDist;
    vec2 rightPos = position + vec2(cos(rightAng), sin(rightAng)) * sensorDist;

    float leftVal  = sampleTrail(leftPos, team);
    float midVal   = sampleTrail(midPos, team);
    float rightVal = sampleTrail(rightPos, team);

    float rotationAng = rotationAngle[teamInt];
    if (midVal > rightVal && midVal > leftVal) {
        // keep heading
    } else if (midVal < rightVal && midVal < leftVal) {
        direction += (0.5 - floor(fract(sin(dot(position + gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453) + 0.5)) * rotationAng;
    } else if (rightVal > midVal && rightVal > leftVal) {
        direction += rotationAng;
    } else if (leftVal > midVal && leftVal > rightVal) {
        direction -= rotationAng;
    }

    float speed = moveSpeed[teamInt];

    vec2 newPosition = position + vec2(cos(direction), sin(direction)) * speed;

    // One agent per pixel: hold position and turn away when occupied.
    bool blocked = occupancy(newPosition) > 0.0;
    if (blocked) {
        newPosition = position;
        direction += PI2 / 4.0;
    }

    newPosition = wrapPos(newPosition);

    outColor = vec4(newPosition, direction, team);
}
`;

// Points pass: draws every agent as a 1-3 px point into the view-sized
// occupancy texture; channel encodes species. Structure follows
// RenderDotsVertex.js / RenderDotsFragment.js of the reference.
export const RENDER_POINTS_VERTEX = `#version 300 es
in vec2 uv; // per-agent lookup into the state texture
uniform sampler2D positionTexture;
uniform vec2 resolution;
uniform vec3 dotSizes;
out float team;
void main() {
    vec4 data = texture(positionTexture, uv);
    gl_Position = vec4(data.xy / (resolution * 0.5), 0.0, 1.0);
    team = data.w;
    gl_PointSize = dotSizes[int(data.w + 0.5)];
}
`;

export const RENDER_POINTS_FRAGMENT = `#version 300 es
precision highp float;
in float team;
out vec4 outColor;
void main() {
    vec3 c = team < 0.5 ? vec3(1.0, 0.0, 0.0) : team < 1.5 ? vec3(0.0, 1.0, 0.0) : vec3(0.0, 0.0, 1.0);
    outColor = vec4(c, 1.0);
}
`;

// Diffuse + decay pass for the trail map, plus fresh agent points.
// Port of DiffuseDecayFragment.js (itself adapted from nicoptere/physarum).
export const DIFFUSE_DECAY_FRAGMENT = `#version 300 es
precision highp float;
uniform sampler2D points;
uniform sampler2D inputTexture;
uniform vec2 resolution;
uniform float decay;
in vec2 vUv;
out vec4 outColor;
void main() {
    vec3 pixelPoint = texture(points, vUv).rgb;

    vec3 col = vec3(0.0);
    const float dim = 1.0;
    float weight = 1.0 / pow(2.0 * dim + 1.0, 2.0);
    for (float i = -dim; i <= dim; i++) {
        for (float j = -dim; j <= dim; j++) {
            col += texture(inputTexture, (gl_FragCoord.xy + vec2(i, j)) / resolution).rgb * weight;
        }
    }

    outColor = vec4(clamp(col * decay + pixelPoint, 0.0, 1.0), 1.0);
}
`;

// Final composite to the canvas. Adapted from FinalRenderFragment.js: species
// channels map to the Morphogenesis palette over the fixed page background.
export const DISPLAY_FRAGMENT = `#version 300 es
precision highp float;
uniform sampler2D diffuseTexture;
uniform sampler2D pointsTexture;
uniform vec3 col0;
uniform vec3 col1;
uniform vec3 col2;
uniform vec3 bgColor;
uniform float trailOpacity;
uniform float dotOpacity;
in vec2 vUv;
out vec4 outColor;
void main() {
    vec3 trail = texture(diffuseTexture, vUv).rgb;
    vec3 dots = texture(pointsTexture, vUv).rgb;
    vec3 mixed = trail * trailOpacity + dots * dotOpacity;
    vec3 col = mixed.r * col0 + mixed.g * col1 + mixed.b * col2;
    col = bgColor + col / (1.0 + col * 0.8);
    outColor = vec4(col, 1.0);
}
`;
