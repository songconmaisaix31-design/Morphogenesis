import React from 'react';
import './growth-intro.css';

// This fixed drawing is an introduction motif. It never reads dashboard data.
const NODES = [
  [600, 340], [536, 318], [665, 318], [584, 274], [617, 413],
  [465, 292], [485, 376], [718, 277], [735, 374], [533, 224],
  [645, 227], [558, 458], [694, 459], [389, 250], [418, 346],
  [459, 441], [768, 214], [807, 313], [802, 424], [746, 502],
  [470, 182], [584, 171], [688, 164], [351, 318], [366, 419],
  [433, 505], [839, 190], [893, 290], [882, 464], [813, 531],
];

// Parent-to-child order gives each new branch a visible origin.
const BRANCHES = [
  [0, 1], [0, 2], [0, 3], [0, 4],
  [1, 5], [1, 6], [2, 7], [2, 8], [3, 9], [3, 10],
  [4, 11], [4, 12], [5, 13], [5, 14], [6, 15],
  [7, 16], [7, 17], [8, 18], [12, 19], [9, 20],
  [9, 21], [10, 22], [13, 23], [14, 24], [15, 25],
  [16, 26], [17, 27], [18, 28], [19, 29],
];

// A few later links suggest an emerging network instead of a rigid tree.
const CROSS_LINKS = [
  [5, 9], [6, 11], [7, 10], [8, 12], [13, 14],
  [16, 22], [17, 18], [18, 19], [20, 21], [27, 28],
];

const toPath = (from, to, bent = false) => {
  const [x1, y1] = NODES[from];
  const [x2, y2] = NODES[to];
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const bend = bent ? -12 : 8;
  return `M ${x1} ${y1} Q ${mx} ${my + bend} ${x2} ${y2}`;
};

export default function GrowthIntro({ active = true, reducedMotion = false }) {
  const mode = reducedMotion ? ' is-static' : '';
  const playback = active ? ' is-active' : ' is-paused';

  return (
    <section
      className={`growth-intro${mode}${playback}`}
      aria-label='自生长，Agent Swarm，概念动画'
      data-concept-animation='true'
      data-active={active ? 'true' : 'false'}
    >
      <svg className='growth-intro__graph' viewBox='0 0 1200 680' preserveAspectRatio='xMidYMid meet' aria-hidden='true'>
        <g className='growth-intro__orbit'>
          <circle cx='600' cy='340' r='150' />
          <circle cx='600' cy='340' r='255' />
        </g>
        <g className='growth-intro__links'>
          {BRANCHES.map(([from, to], index) => (
            <path
              key={`branch-${from}-${to}`}
              className='growth-intro__branch'
              d={toPath(from, to)}
              pathLength='1'
              style={{ '--growth-delay': `${(0.15 + index * 0.105).toFixed(3)}s` }}
            />
          ))}
          {CROSS_LINKS.map(([from, to], index) => (
            <path
              key={`link-${from}-${to}`}
              className='growth-intro__cross-link'
              d={toPath(from, to, true)}
              pathLength='1'
              style={{ '--growth-delay': `${(2.15 + index * 0.12).toFixed(3)}s` }}
            />
          ))}
        </g>
        <g className='growth-intro__nodes'>
          {NODES.map(([x, y], index) => (
            <g
              key={`node-${index}`}
              className={`growth-intro__node${index === 0 ? ' growth-intro__node--origin' : ''}`}
              style={{ '--growth-delay': `${index === 0 ? 0 : (0.42 + (index - 1) * 0.105).toFixed(3)}s` }}
            >
              {index % 7 === 0 && <circle className='growth-intro__node-halo' cx={x} cy={y} r='13' />}
              <circle cx={x} cy={y} r={index === 0 ? 5 : index % 4 === 0 ? 4 : 3} />
            </g>
          ))}
        </g>
      </svg>

      <div className='growth-intro__caption'>
        <span className='growth-intro__caption-cn'>自生长</span>
        <span className='growth-intro__caption-en'>AGENT SWARM</span>
        <span className='growth-intro__concept'>概念动画</span>
      </div>
    </section>
  );
}
