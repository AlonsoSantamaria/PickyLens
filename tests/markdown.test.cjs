const assert=require('node:assert/strict');
const fs=require('node:fs');
const test=require('node:test');
global.markdownit=require('../app/static/vendor/markdown-it-15.0.3.min.js');
require('../app/static/markdown.js');
const source=fs.readFileSync('tests/fixtures/answer-markdown.md','utf8');
test('common Markdown and aligned semantic tables',()=>{
 const html=PickyLensMarkdown.html(source);
 for(const tag of ['h3','h4','p','strong','em','ul','ol','blockquote','code','pre','a','table','thead','tbody','th','td'])assert.match(html,new RegExp('<'+tag+'(?:>| )'));
 assert.match(html,/<th scope="col">Planning variable<\/th>/);
 assert.match(html,/<td style="text-align:right">1,500<\/td>/);
 assert.match(html,/class="table-scroll"/);
 assert.ok(!html.includes('| Planning variable'));
});
test('untrusted HTML, URL schemes, images and attribute injection stay inert',()=>{
 const hostile=source+'\n[data](data:text/html;base64,AAAA)\n[x](vbscript:evil)\n[x](https://example.com "\" onmouseover=evil")';
 const html=PickyLensMarkdown.html(hostile);
 assert.doesNotMatch(html,/<(?:script|img|iframe|svg|object|embed|style)(?:>| )/i);
 assert.doesNotMatch(html,/href="(?:javascript|vbscript|data):/i);
 assert.doesNotMatch(html,/<[^>]+\son(?:error|mouseover|load)=/i);
 assert.match(html,/&lt;script&gt;/);
});
test('source is unchanged and repeat rendering does not reset a reading panel',()=>{
 const target={dataset:{},writes:0,set innerHTML(value){this.writes++;this.html=value;}};
 const original=source;
 PickyLensMarkdown.render(target,source);PickyLensMarkdown.render(target,source);
 assert.equal(source,original);assert.equal(target.writes,1);
});
