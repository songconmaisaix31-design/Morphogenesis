import React, { useState } from 'react';
import { useTrackComponent } from './hooks';

const FallbackField = () => (
  <div className='physarum-fallback' aria-hidden='true'>
    <i /><i /><i /><i /><i />
  </div>
);

// The native yellow simulation remains ambient, with no pointer or touch input.
const Hero = ({ active, reducedMotion, showLabel }) => {
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
      <div className={`story-physarum-label${showLabel ? ' is-visible' : ''}`}>
        <span lang='zh-CN'>黏菌</span><span lang='en'>PHYSARUM</span>
        {failed ? <p className='morph-hero-note'>黏菌场模块不可用，已切换为静态降级背景。</p> : null}
      </div>
    </div>
  );
};

export default React.memo(Hero);
