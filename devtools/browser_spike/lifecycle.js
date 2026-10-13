// Pure conservative lifecycle classifier; unknown/aborted outputs are never complete.
(function(root){
 function classify(previous,signal){
  if(signal.aborted)return 'aborted';
  if(signal.busy==='true')return 'generating';
  if(signal.busy==='false'&&signal.actions&&signal.text.trim()&&previous==='generating')return 'complete';
  if(previous==='complete'&&signal.busy==='false'&&signal.actions)return 'complete';
  if(previous==='generating')return 'generating';
  return 'unknown';
 }
 if(typeof module!=='undefined')module.exports={classify};else root.PickyLensLifecycle={classify};
})(typeof window==='undefined'?{}:window);

