// Shared read-only browser checks; no model or credential lookup.
const assert = require('node:assert/strict');

function withoutGatewayKey(environment) {
  return Object.fromEntries(Object.entries(environment).filter(([key]) => key.toUpperCase() !== 'MORPH_EVOMAP_API_KEY'));
}

// This function runs in the page, against the actual ZRender display list.
function readGeometry() {
  const chart=echarts.getInstanceByDom(document.getElementById('story-pipe-chart'));
  const display=chart.getZr().storage.getDisplayList();
  const bounds=element=>{
    const r=element.getBoundingRect().clone();
    r.applyTransform(element.getComputedTransform());
    return {type:element.type,text:element.style.text,x:r.x,y:r.y,width:r.width,height:r.height};
  };
  return {viewport:innerWidth,viewportHeight:innerHeight,width:chart.getWidth(),height:chart.getHeight(),
    overflow:document.documentElement.scrollWidth>innerWidth,
    geneBottom:document.querySelector('.gene-ledger').getBoundingClientRect().bottom,
    labels:display.filter(e=>e.type==='tspan').map(bounds),nodes:display.filter(e=>e.type==='path').map(bounds)};
}

function assertGeometry(row) {
  assert(!row.overflow);
  assert(row.geneBottom<row.viewportHeight,'Gene ledger outside first viewport');
  assert.equal(row.labels.length,3);
  assert.equal(row.nodes.length,3);
  for(const item of [...row.labels,...row.nodes]) {
    assert(item.x>=0&&item.y>=0&&item.x+item.width<=row.width&&item.y+item.height<=row.height,`clipped ${item.text??'node'}`);
  }
  for(let i=0;i<row.labels.length;i++) for(let j=i+1;j<row.labels.length;j++) {
    const a=row.labels[i],b=row.labels[j];
    assert(a.x+a.width<=b.x||b.x+b.width<=a.x||a.y+a.height<=b.y||b.y+b.height<=a.y,'overlapping labels');
  }
  for(const node of row.nodes) for(const label of row.labels) {
    assert.equal(node.width,node.height,'expected circle symbol');
    const cx=node.x+node.width/2,cy=node.y+node.height/2;
    const dx=cx-Math.max(label.x,Math.min(cx,label.x+label.width));
    const dy=cy-Math.max(label.y,Math.min(cy,label.y+label.height));
    assert(dx*dx+dy*dy>=(node.width/2)**2,`label over circle: ${label.text}`);
  }
}

module.exports={withoutGatewayKey,readGeometry,assertGeometry};
