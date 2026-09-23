import React, { useState } from 'react';
import { useTrackComponent } from './hooks';

// Placeholder field for a module load failure. PhysarumField handles its own
// runtime failures and renders the yellow static network in that case.
const FallbackField = () => (
  <div className='physarum-fallback' aria-hidden='true'>
    <i /><i /><i /><i /><i />
  </div>
);

// First screen hard constraint: the big MORPHOGENESIS word plus the two
// minimal PHYSARUM / AGENT SWARM markers are the only normal-state text.
const Hero = ({ active, reducedMotion, onEnterSwarm }) => {
  const { Component: PhysarumField, error: loadError } = useTrackComponent('physarum');
  const [runtimeError, setRuntimeError] = useState(null);
  const failed = Boolean(loadError || runtimeError);

  return (
    <div className='morph-hero'>
      <div className='morph-hero-field'>
        {PhysarumField
          ? <PhysarumField active={active} reducedMotion={reducedMotion} onError={setRuntimeError} />
          : <FallbackField />}
      </div>
      <div className='morph-hero-copy'>
        <h1 className='morph-hero-title'>MORPHOGENESIS</h1>
        <div className='morph-hero-markers' role='group' aria-label='视图标识'>
          <span className='morph-marker is-current' aria-current='page'>PHYSARUM</span>
          <button type='button' className='morph-marker' onClick={onEnterSwarm}>AGENT SWARM</button>
        </div>
        {failed ? <p className='morph-hero-note'>黏菌场模块不可用，已切换为静态降级背景。</p> : null}
      </div>
    </div>
  );
};

export default React.memo(Hero);
