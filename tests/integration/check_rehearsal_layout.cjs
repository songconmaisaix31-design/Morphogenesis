// Read-only geometry and screenshot acceptance against an explicitly replay-marked viewer.
// Usage: node tests/integration/check_rehearsal_layout.cjs URL OUTPUT_DIR
// Uses MORPH_PLAYWRIGHT and MORPH_CHROMIUM, as observe_rehearsal.cjs does.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require(process.env.MORPH_PLAYWRIGHT);
const [url, output] = process.argv.slice(2);
assert(url && output);
fs.mkdirSync(output, {recursive:true});

(async () => {
  const browser = await chromium.launch({headless:true, executablePath:process.env.MORPH_CHROMIUM});
  const rows=[];
  try {
    for(const [width,height] of [[1366,768],[1920,1080]]) {
      const page=await browser.newPage({viewport:{width,height}});
      await page.goto(url);
      await page.waitForFunction(()=>document.querySelector('#provenance').textContent.includes('replay'));
      await page.waitForTimeout(1400); // Includes another polling interval and fully drawn nodes.
      rows.push(await page.evaluate(()=>{
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
      }));
      await page.screenshot({path:path.join(output,`replay-${width}.png`)});
      await page.close();
    }
  } finally { await browser.close(); }
  fs.writeFileSync(path.join(output,'geometry.json'),JSON.stringify(rows,null,2));
  for(const row of rows) {
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
  console.log(JSON.stringify({viewports:rows.map(r=>r.viewport),labels:3,nodes:3,clipping:false,overlap:false}));
})().catch(error=>{console.error(error);process.exitCode=1;});
