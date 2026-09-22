// Adapted from tdesign-react-starter src/components/Board/index.tsx (MIT,
// commit fce97863edd5d5556f766dd4e342aace31a99487): same Card + title/count/
// desc structure; trend icons and demo micro-charts removed, and the count is a
// plain data-owned span (giant mono number) instead of hardcoded statistics.
import React from 'react';
import { Card } from 'tdesign-react';
import classnames from 'classnames';

const Board = ({ title, countId, count, desc, descId, className }) => (
  <Card
    className={classnames('morph-board', className)}
    title={<span className='morph-board-title'>{title}</span>}
    bordered={false}
    footer={<div className='morph-board-desc' id={descId}>{desc}</div>}
  >
    <span className='morph-board-count' id={countId}>{count}</span>
  </Card>
);

export default React.memo(Board);
