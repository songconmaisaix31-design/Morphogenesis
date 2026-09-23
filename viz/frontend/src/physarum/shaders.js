// GLSL sources for the Physarum WebGL2 simulation.
//
// Adapted from Bewelge/Physarum-WebGL (MIT License, Copyright (c) 2021-2022
// Benjamin Welge), commit e621c3ecb60c5c8a4d1b3446c7b389b083ea1908,
// src/js/Shaders/*.js — which itself credits nicoptere/physarum for the
// ping-pong / diffuse-decay shader logic. Ported from GLSL ES 1.00 (Three.js
// ShaderMaterial) to raw GLSL ES 3.00 and extended with food-seeking
// (cursor attraction), a connected feeding front and smooth-recovery uniforms.
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
// follows UpdateDotsFragment.js of the reference; the mouse repulsion there is
// replaced by gentle food-seeking steering. Agents retain motion through the
// feeding front instead of being trapped at the pointer.
export const UPDATE_AGENTS_FRAGMENT = `#version 300 es
precision highp float;

uniform sampler2D inputTexture;   // previous agent states (sim grid)
uniform sampler2D trailTexture;   // aggregated pheromone trail (view sized)
uniform sampler2D pointsTexture;  // occupied pixels this frame (view sized)

uniform vec2 resolution;          // view (trail) resolution in px
uniform float time;               // frame counter

uniform vec2 foodPos;             // cursor, centered coords, y up
uniform float foodStrength;       // 0..1, eased on CPU for smooth recovery
uniform float foodCoreRadius;     // radius of the spreading feeding front
uniform float foodTurn;           // max steering per frame toward food (rad)

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

    // A chemotactic bias bends an existing connected colony toward food.
    // Its falloff near food lets the leading sheet spread past the target.
    vec2 seg = foodPos - position;
    float fdist = length(seg);
    if (foodStrength > 0.0001 && fdist > 0.0001) {
        float target = atan(seg.y, seg.x);
        float diff = atan(sin(target - direction), cos(target - direction));
        float front = smoothstep(foodCoreRadius * 0.65, foodCoreRadius * 2.5, fdist);
        float reach = 1.0 - smoothstep(360.0, 820.0, fdist);
        direction += clamp(diff, -1.0, 1.0) * foodTurn * foodStrength * front * reach;
    }

    // Keep cytoplasm moving. A slight rhythm evokes contraction and release,
    // without collapsing the front into a stationary cursor-sized dot.
    float speed = moveSpeed[teamInt] * (1.0 + 0.12 * sin(time * 0.055 - position.x * 0.018));

    vec2 newPosition = position + vec2(cos(direction), sin(direction)) * speed;

    // Occupancy spreads the advancing sheet and prevents a point pile.
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

// Final composite: close trail samples form a translucent advancing sheet;
// concentrated tracks remain brighter as posterior veins. Phase modulation
// gives the veins a reversible contraction/streaming rhythm.
export const DISPLAY_FRAGMENT = `#version 300 es
precision highp float;
uniform sampler2D diffuseTexture;
uniform sampler2D pointsTexture;
uniform vec3 bgColor;
uniform vec2 resolution;
uniform float time;
uniform vec2 frontPos;
in vec2 vUv;
out vec4 outColor;
void main() {
    vec2 p = (vUv - 0.5) * resolution;
    vec2 rear = vec2(-resolution.x * 0.38, -resolution.y * 0.07);
    vec2 axis = frontPos - rear;
    float len = max(length(axis), 1.0);
    vec2 along = axis / len;
    vec2 across = vec2(-along.y, along.x);
    float t = dot(p - rear, along) / len;
    float side = dot(p - rear, across);
    float bend = 14.0 * sin(t * 5.1 + 0.4) + 8.0 * sin(t * 12.7);
    float y = side - bend;
    float flow = sin(time * 0.045 - t * 8.0);

    // A wide, irregular anterior sheet grows from a narrow rear trunk.
    float fanWidth = min(resolution.y * 0.17, 110.0) * smoothstep(0.44, 0.84, t)
        * mix(1.1, 0.84, step(0.0, y));
    float ripple = 8.0 * sin(y * 0.046 + time * 0.012) + 5.0 * sin(y * 0.13 - t * 12.0);
    float frontEdge = 1.01 + 0.07 * sin(y * 0.044 + 0.7) + 0.04 * sin(y * 0.11);
    float sheet = smoothstep(0.43, 0.7, t) * (1.0 - smoothstep(frontEdge - 0.04, frontEdge + 0.035, t))
        * (1.0 - smoothstep(fanWidth - 4.0 + ripple, fanWidth + 4.0 + ripple, abs(y)));

    // Posterior veins join the same trunk and gradually enter the fan.
    float trunkWidth = 3.0 + 1.5 * sin(t * 18.0) + 2.0 * smoothstep(0.2, 0.8, t);
    float trunk = (1.0 - smoothstep(trunkWidth, trunkWidth + 2.2, abs(y)))
        * smoothstep(-0.05, 0.04, t) * (1.0 - smoothstep(0.86, 1.0, t));
    float branches = 0.0;
    for (int i = 0; i < 7; i++) {
        float q = float(i);
        float split = 0.035 + 0.048 * q;
        float join = 0.6 + 0.045 * mod(q * 3.0, 5.0);
        float reach = smoothstep(split, split + 0.035, t) * (1.0 - smoothstep(join - 0.07, join, t));
        float progress = clamp((t - split) / (join - split), 0.0, 1.0);
        float sign = mod(q, 2.0) < 0.5 ? 1.0 : -1.0;
        float lane = sign * (16.0 + q * 9.0) * sin(progress * 3.14159265)
            + (6.0 * sin(t * (17.0 + q * 2.7) + q * 1.9)
            + 3.2 * sin(t * 43.0 + q * 3.4)) * sin(progress * 3.14159265);
        float width = max(0.8, 1.8 + 0.35 * mod(q * 3.0, 4.0)
            + 0.6 * sin(time * 0.045 - t * 8.0 + q)
            + 1.25 * sin(t * (24.0 + q) + q * 2.7));
        branches = max(branches, reach * (1.0 - smoothstep(width, width + 2.0, abs(y - lane))));
    }
    // Short transverse anastomoses connect neighboring veins.
    float crossA = (1.0 - smoothstep(0.31, 0.335, t)) * smoothstep(0.26, 0.285, t)
        * (1.0 - smoothstep(1.3, 3.0, abs(y - (t - 0.28) * 800.0 - 11.0)));
    float crossB = (1.0 - smoothstep(0.55, 0.575, t)) * smoothstep(0.5, 0.525, t)
        * (1.0 - smoothstep(1.3, 3.0, abs(y + (t - 0.51) * 650.0 + 27.0)));
    float veins = max(trunk, max(branches, max(crossA, crossB) * 0.65));
    float trail = dot(texture(diffuseTexture, vUv).rgb, vec3(0.3333));
    float mottling = sin(p.x * 0.067 + sin(p.y * 0.027) * 2.0) * sin(p.y * 0.075 - t * 7.0);
    float grain = 0.7 + 0.18 * mottling + 0.12 * smoothstep(0.02, 0.4, trail);
    // Within the thin fan, two warped vein families intersect repeatedly.
    // The darker open spaces prevent it reading as a solid painted leaf.
    float warp = 7.0 * sin(t * 17.0 + y * 0.025) + 3.0 * sin(t * 31.0 - y * 0.046);
    float ribA = 1.0 - smoothstep(0.08, 0.3, abs(sin((y + warp) * 0.115 + t * 5.0)));
    float ribB = 1.0 - smoothstep(0.055, 0.24, abs(sin((y - warp) * 0.14 - t * 8.0)));
    float fanWeb = sheet * max(ribA * 0.35, ribB * 0.25);
    float lip = sheet * smoothstep(frontEdge - 0.095, frontEdge - 0.01, t);
    float fill = sheet * (0.075 + 0.015 * flow) + fanWeb + veins * (0.57 + 0.12 * flow)
        + lip * 0.19;
    vec3 gold = vec3(0.95, 0.66, 0.07);
    vec3 amber = vec3(1.0, 0.85, 0.26);
    vec3 col = bgColor + mix(gold, amber, veins * 0.72) * clamp(fill * grain, 0.0, 0.88);
    outColor = vec4(col, 1.0);
}
`;
