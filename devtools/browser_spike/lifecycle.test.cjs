const assert=require('node:assert/strict');const {classify}=require('./lifecycle.js');
const done={busy:'false',actions:true,text:'Answer'};
assert.equal(classify(undefined,done),'unknown');
assert.equal(classify(undefined,{...done,busy:'true'}),'generating');
assert.equal(classify('generating',done),'complete');
assert.equal(classify('complete',done),'complete');
assert.equal(classify('generating',{...done,aborted:true}),'aborted');
assert.equal(classify('generating',{...done,actions:false}),'generating');
assert.equal(classify(classify('generating',{...done,actions:false}),done),'complete');
console.log('7 conservative lifecycle assertions passed; not host validation.');

