const S = {
  conversations: [], overrides: {}, dismissed: {}, newIds: new Set(),
  selectedId: null, actionFilter: 'all', reviewCat: 'filtered', reviewOpen: false,
  trendOpen: false, theme: 'light',
  nameSignalFirst: '', nameSignalEditing: false,
  homeSetupOpen: false,
  filter: { timelineAfter: null, timelineBefore: null },
  exportTimestamp: null, exportTimestampSource: null, lastUpdatedTimer: null,
  replyAssistById: {}, // { [threadId]: { isGenerating, suggestedReply, generationAttempted, copied, regenerateCount } }
  connectedSource: {
    supported: false, canPersist: false, supportReason: '',
    handle: null, fileName: '', lastRefreshedAt: null,
    refreshState: 'idle', runnerUrl: 'http://127.0.0.1:8765'
  }
};
const OVERRIDE_KEY='miranda2_overrides_v1', DISMISS_KEY='miranda2_dismissed_v2',
      DATA_KEY='miranda2_data_v1', META_KEY='miranda2_meta_v1', HISTORY_KEY='miranda2_history_v1',
      NAME_SIGNAL_KEY='miranda2_name_signal_v1', THEME_KEY='miranda2_theme_v1',
      CONNECTED_SOURCE_DB='miranda2_connected_source_v1', CONNECTED_SOURCE_STORE='sources', CONNECTED_SOURCE_KEY='primary';
const LEGACY_DISMISS_KEY='miranda2_dismissed_v1';
const PREVIEW_INCLUDE_ATTACHMENT=true; // set false to hide "📎 Attachment" rows in collapsed previews
const DEFAULT_AI_MODEL='';
const AI_SUGGEST_ROUTE='/api/ai-suggest-reply';
const AI_ALLOWED_DEMO_THREAD_IDS=new Set([
  'iMessage;-;+12125550101', // bird accusation
  'iMessage;-;+12125550102', // Michael Scott
  'iMessage;-;+12125550110', // minor European princess
  'iMessage;-;+12125550109', // hyperlocal media disruption engine
  'iMessage;-;+12125550105', // branding exercise
  'iMessage;-;+12125550107', // parking ticket for emotional reasons
  'iMessage;-;+12125550108', // Fleabag
  'iMessage;-;+12125550103', // society's collapsing dinner
  'iMessage;-;+12125550104'  // it's about longing
]);

async function init() {
  try { const r=localStorage.getItem(OVERRIDE_KEY); if(r) S.overrides=JSON.parse(r); } catch(_){}
  try {
    const r=localStorage.getItem(DISMISS_KEY);
    if(r)S.dismissed=JSON.parse(r);
    else{
      const legacy=localStorage.getItem(LEGACY_DISMISS_KEY);
      if(legacy)S.dismissed=JSON.parse(legacy);
    }
  } catch(_){}
  try { const r=localStorage.getItem(NAME_SIGNAL_KEY); if(r) S.nameSignalFirst=JSON.parse(r).firstName||''; } catch(_){}
  try {
    const savedTheme=localStorage.getItem(THEME_KEY);
    S.theme=savedTheme==='dark'?'dark':'light';
  } catch(_) { S.theme='light'; }
  applyTheme();
  wireStartDesignIframe();
  checkSavedData();
  const ds=document.getElementById('drop-screen');
  ds.addEventListener('dragover',e=>{e.preventDefault();ds.classList.add('drag-over');});
  ds.addEventListener('dragleave',()=>ds.classList.remove('drag-over'));
  ds.addEventListener('drop',e=>{e.preventDefault();ds.classList.remove('drag-over');if(e.dataTransfer.files[0])loadFile(e.dataTransfer.files[0]);});
  document.getElementById('file-input').addEventListener('change',e=>{if(e.target.files[0])loadFile(e.target.files[0]);});
  if(!localStorage.getItem(DATA_KEY)){
    try{
      const response=await fetch('./data/miranda_demo.json');
      if(response.ok){
        const demoData=timeShiftBundledDemoData(await response.json());
        localStorage.setItem(DATA_KEY,JSON.stringify(demoData));
        localStorage.setItem(META_KEY,JSON.stringify({
          savedAt:new Date().toISOString(),
          count:(demoData.conversations||[]).length
        }));
        checkSavedData();
      }
    }catch(_){}
  }
  await initConnectedSource();
  renderSourceUi();
  setRefreshState('idle');
}

function wireStartDesignIframe(){
  const frame=document.getElementById('start-design-frame');
  if(!frame)return;
  const wire=()=>{
    let doc=null;
    let win=null;
    try{doc=frame.contentDocument||frame.contentWindow.document;}catch(_){return;}
    if(!doc)return;
    try{win=frame.contentWindow;}catch(_){}

    // The standalone persists its last screen in iframe-local storage and
    // auto-launches a tour into Inbox on first visit. Force the start frame
    // to the About/landing screen so users see the new entrance design.
    try{
      if(win){
        try{ win.localStorage.setItem('rod_screen','landing'); }catch(_){}
        try{ win.localStorage.setItem('rod_tour_seen','1'); }catch(_){}
      }
    }catch(_){}
    const goLanding=()=>{
      try{
        if(win&&typeof win.go==='function'){ win.go('landing'); return true; }
      }catch(_){}
      const landingBtn=doc.querySelector('button[data-nav="landing"]');
      if(landingBtn){ landingBtn.click(); return true; }
      return false;
    };
    if(!goLanding()){
      let tries=0;
      const t=setInterval(()=>{
        tries+=1;
        if(goLanding()||tries>40)clearInterval(t);
      },50);
    }

    const text=(el)=>(el&&el.textContent||'').trim().toLowerCase();
    const allButtons=Array.from(doc.querySelectorAll('button'));

    const demoBtn=allButtons.find(b=>{
      const t=text(b);
      return t.includes('browse the demo inbox')||t.includes('see inbox with demo')||t.includes('demo inbox');
    });
    if(demoBtn){
      demoBtn.onclick=(e)=>{e.preventDefault();enterDemoInbox();};
    }

    const connectBtn=allButtons.find(b=>{
      const t=text(b);
      return t.includes('connect your imessage')||t.includes('connect imessage')||t.includes('upload your text inbox');
    });
    if(connectBtn){
      connectBtn.onclick=(e)=>{
        e.preventDefault();
        try{
          if(win&&typeof win.go==='function')win.go('setup');
        }catch(_){}
      };
    }

    const navInbox=doc.querySelector('button[data-nav="inbox"]');
    if(navInbox){
      navInbox.onclick=(e)=>{e.preventDefault();enterDemoInbox();};
    }

    const refreshBtn=doc.getElementById('refreshBtn');
    if(refreshBtn){
      refreshBtn.onclick=(e)=>{e.preventDefault();refresh();};
    }

    const fdaContinue=doc.getElementById('fdaContinue');
    if(fdaContinue){
      fdaContinue.disabled=false;
      fdaContinue.onclick=async (e)=>{
        e.preventDefault();
        await connectExportFile();
        try{ if(win&&typeof win.setupGo==='function')win.setupGo(3); }catch(_){}
      };
    }

    const scanContinue=doc.getElementById('scanContinue');
    if(scanContinue){
      scanContinue.disabled=false;
      scanContinue.onclick=(e)=>{
        e.preventDefault();
        try{ if(win&&typeof win.setupGo==='function')win.setupGo(4); }catch(_){}
      };
    }

    const openInboxBtn=allButtons.find(b=>{
      const t=text(b);
      return t.includes('open my inbox')||t.includes('open inbox');
    });
    if(openInboxBtn){
      openInboxBtn.onclick=(e)=>{
        e.preventDefault();
        const hasData=S.conversations.length>0||!!localStorage.getItem(DATA_KEY);
        if(hasData)loadSavedData();
        else showDropError('Connect an export first, then open inbox.');
      };
    }
  };
  frame.addEventListener('load',wire);
  if(frame.contentDocument?.readyState==='complete')wire();
}

function checkSavedData(){
  try{const m=JSON.parse(localStorage.getItem(META_KEY)),d=localStorage.getItem(DATA_KEY);
  if(m&&d){
    const metaEl=document.getElementById('saved-meta');
    const promptEl=document.getElementById('saved-prompt');
    if(metaEl)metaEl.textContent=`${m.count||'?'} conversations · saved ${timeSince(m.savedAt)}`;
    if(promptEl)promptEl.style.display='block';
  }}catch(_){}
}
function timeSince(d){const ms=Date.now()-new Date(d).getTime(),m=Math.floor(ms/60000);
  if(m<1)return'just now';if(m<60)return m+'m ago';const h=Math.floor(m/60);
  if(h<24)return h+'h ago';return Math.floor(h/24)+'d ago';}

function loadSavedData(){try{const r=localStorage.getItem(DATA_KEY);if(!r)return;
  S.newIds.clear();loadData(JSON.parse(r),false);}catch(ex){showDropError('Could not load: '+ex.message);}}

async function enterDemoInbox(){
  try{
    const existing=localStorage.getItem(DATA_KEY);
    if(existing){
      S.newIds.clear();
      loadData(JSON.parse(existing),false);
      return;
    }
    const response=await fetch('./data/miranda_demo.json');
    if(!response.ok)throw new Error('Could not load bundled demo data.');
    const demoData=timeShiftBundledDemoData(await response.json());
    localStorage.setItem(DATA_KEY,JSON.stringify(demoData));
    localStorage.setItem(META_KEY,JSON.stringify({
      savedAt:new Date().toISOString(),
      count:(demoData.conversations||[]).length
    }));
    checkSavedData();
    S.newIds.clear();
    loadData(demoData,false);
  }catch(ex){
    showDropError(ex.message||'Could not open demo inbox.');
  }
}

function openRefreshSetup(){
  S.homeSetupOpen=true;
  renderSourceUi();
  const panel=document.getElementById('source-panel-drop');
  if(panel){
    panel.scrollIntoView({ behavior:'smooth', block:'nearest' });
  }
}

function loadFile(file){
  document.getElementById('drop-error').style.display='none';
  if(!file.name.endsWith('.json')){
    const msg='Please select a .json file.';
    showDropError(msg);
    return Promise.reject(new Error(msg));
  }
  return new Promise((resolve,reject)=>{
    const reader=new FileReader();
    reader.onerror=()=>reject(reader.error||new Error('Could not read file.'));
    reader.onload=e=>{
      try{
        const data=JSON.parse(e.target.result);
        if(!data.conversations)throw new Error('Missing "conversations" key.');
        diffNew(data);
        loadData(data,true);
        resolve(data);
      }catch(ex){
        const err=new Error('Could not parse: '+ex.message);
        showDropError(err.message);
        reject(err);
      }
    };
    reader.readAsText(file);
  });
}
function diffNew(nd){S.newIds.clear();try{const o=localStorage.getItem(DATA_KEY);if(!o)return;
  const old=new Set((JSON.parse(o).conversations||[]).map(c=>c.id));
  (nd.conversations||[]).forEach(c=>{if(!old.has(c.id))S.newIds.add(c.id);});}catch(_){}}

function showDropError(msg){const el=document.getElementById('drop-error');el.textContent=msg;el.style.display='block';}
function setSourceError(msg){
  ['source-error-drop','source-error-app'].forEach(id=>{
    const el=document.getElementById(id);
    if(!el)return;
    if(!msg){el.style.display='none';el.textContent='';return;}
    el.style.display='block';el.textContent=msg;
  });
}

function setSourceStatus(msg,tone){
  ['source-status-drop','source-status-app'].forEach(id=>{
    const el=document.getElementById(id);
    if(!el)return;
    if(!msg){
      el.style.display='none';
      el.textContent='';
      el.classList.remove('is-error','is-success');
      return;
    }
    el.style.display='block';
    el.textContent=msg;
    el.classList.remove('is-error','is-success');
    if(tone==='error')el.classList.add('is-error');
    if(tone==='success')el.classList.add('is-success');
  });
}

function setRefreshState(state){
  S.connectedSource.refreshState=state;
  const labels={
    idle:'Idle',
    running_export:'Running export.command…',
    reloading_data:'Reloading data…',
    success:'Refresh complete.',
    export_failed:'Export failed. Keeping last successful data loaded.',
    runner_unavailable:'Runner unavailable. You can still reload current JSON.',
    output_unchanged:'Export finished, but output is unchanged.',
    stale_file:'No new data — double-click export.command to refresh.'
  };
  const tone=state==='export_failed'||state==='runner_unavailable'?'error':(state==='success'?'success':'');
  setSourceStatus(labels[state]||'Idle',tone);
}

function renderSourceUi(){
  const supported=S.connectedSource.supported;
  const connected=!!S.connectedSource.handle;
  const sourcePanel=document.getElementById('source-panel-drop');
  const sourceTitle=document.getElementById('source-title-drop');
  const sourceName=document.getElementById('source-name-drop');
  if(sourcePanel){
    sourcePanel.style.display=S.homeSetupOpen?'block':'none';
    if(!S.homeSetupOpen){
      setSourceStatus('', '');
      setSourceError('');
      return;
    }
    if(!supported){
      sourceTitle.textContent='Connected export file';
      sourceName.textContent=S.connectedSource.supportReason||'One-click refresh is unavailable in this browser or page context.';
    }else if(!connected){
      sourceTitle.textContent='Connected export file';
      sourceName.textContent=S.connectedSource.canPersist
        ? 'Connect once, then use Refresh.'
        : 'Connect file for this session, then use Refresh.';
    }else{
      const nameText=`Connected file: ${S.connectedSource.fileName||'miranda2_messages.json'}`;
      sourceTitle.textContent='Connected export file';
      sourceName.textContent=nameText;
    }
  }
  const connectIds=['connect-export-btn-drop'];
  const refreshIds=['refresh-btn-drop','refresh-btn-app'];
  const changeIds=['change-source-btn-drop'];
  connectIds.forEach(id=>{const el=document.getElementById(id);if(el)el.style.display=(supported&&!connected)?'inline-block':'none';});
  refreshIds.forEach(id=>{const el=document.getElementById(id);if(el)el.style.display=(supported&&connected)?'inline-block':'none';});
  changeIds.forEach(id=>{const el=document.getElementById(id);if(el)el.style.display=(supported&&connected)?'inline-block':'none';});
}

function openConnectedSourceDb(){
  return new Promise((resolve,reject)=>{
    const req=indexedDB.open(CONNECTED_SOURCE_DB,1);
    req.onupgradeneeded=()=>{const db=req.result;if(!db.objectStoreNames.contains(CONNECTED_SOURCE_STORE))db.createObjectStore(CONNECTED_SOURCE_STORE);};
    req.onsuccess=()=>resolve(req.result);
    req.onerror=()=>reject(req.error||new Error('Failed to open IndexedDB'));
  });
}

async function saveConnectedSourceRecord(record){
  const db=await openConnectedSourceDb();
  await new Promise((resolve,reject)=>{
    const tx=db.transaction(CONNECTED_SOURCE_STORE,'readwrite');
    tx.objectStore(CONNECTED_SOURCE_STORE).put(record,CONNECTED_SOURCE_KEY);
    tx.oncomplete=()=>resolve();
    tx.onerror=()=>reject(tx.error||new Error('Could not save source'));
  });
  db.close();
}

async function loadConnectedSourceRecord(){
  const db=await openConnectedSourceDb();
  const result=await new Promise((resolve,reject)=>{
    const tx=db.transaction(CONNECTED_SOURCE_STORE,'readonly');
    const req=tx.objectStore(CONNECTED_SOURCE_STORE).get(CONNECTED_SOURCE_KEY);
    req.onsuccess=()=>resolve(req.result||null);
    req.onerror=()=>reject(req.error||new Error('Could not read source'));
  });
  db.close();
  return result;
}

async function clearConnectedSourceRecord(){
  const db=await openConnectedSourceDb();
  await new Promise((resolve,reject)=>{
    const tx=db.transaction(CONNECTED_SOURCE_STORE,'readwrite');
    tx.objectStore(CONNECTED_SOURCE_STORE).delete(CONNECTED_SOURCE_KEY);
    tx.oncomplete=()=>resolve();
    tx.onerror=()=>reject(tx.error||new Error('Could not clear source'));
  });
  db.close();
}

async function initConnectedSource(){
  const hasPicker=typeof window.showOpenFilePicker==='function';
  const hasIndexedDb=typeof window.indexedDB!=='undefined';
  const secureContext=window.isSecureContext===true;
  S.connectedSource.supported=hasPicker;
  S.connectedSource.canPersist=hasIndexedDb;
  if(!hasPicker){
    S.connectedSource.supportReason=secureContext
      ? 'One-click refresh is unavailable in this browser.'
      : 'One-click refresh is unavailable in this page context. Use localhost/HTTPS.';
    return;
  }
  if(!hasIndexedDb){
    S.connectedSource.supportReason='One-click refresh is available, but connected file won’t persist after reload.';
    return;
  }
  try{
    const saved=await loadConnectedSourceRecord();
    if(!saved||!saved.handle)return;
    S.connectedSource.handle=saved.handle;
    S.connectedSource.fileName=saved.fileName||'miranda2_messages.json';
    S.connectedSource.lastRefreshedAt=saved.lastRefreshedAt||null;
  }catch(_){
    S.connectedSource.canPersist=false;
    setSourceError('Connected source could not be restored. Re-connect export file for this session.');
  }
}

async function ensureReadPermission(handle){
  if(!handle)return false;
  try{
    if((await handle.queryPermission({mode:'read'}))==='granted')return true;
    if((await handle.requestPermission({mode:'read'}))==='granted')return true;
  }catch(_){}
  return false;
}

async function connectExportFile(){
  setSourceError('');
  if(!S.connectedSource.supported){setSourceError('Connect not supported. Import file manually.');renderSourceUi();return;}
  try{
    const [handle]=await window.showOpenFilePicker({multiple:false,types:[{description:'JSON export',accept:{'application/json':['.json']}}]});
    if(!handle)return;
    const file=await handle.getFile();
    const refreshedAt=new Date().toISOString();
    if(S.connectedSource.canPersist){
      await saveConnectedSourceRecord({handle,fileName:file.name,lastRefreshedAt:refreshedAt});
    }
    S.connectedSource.handle=handle;
    S.connectedSource.fileName=file.name;
    S.connectedSource.lastRefreshedAt=refreshedAt;
    await loadFile(file);
    setRefreshState('idle');
    renderSourceUi();
  }catch(ex){
    if(ex&&ex.name==='AbortError')return;
    setSourceError('Connect failed. Import file manually.');
  }
}

async function refreshMessages(){
  setSourceError('');
  setSourceStatus('',null);
  if(!S.connectedSource.supported){setSourceError('Refresh failed. Import file manually.');return false;}
  if(!S.connectedSource.handle){setSourceError('Refresh failed. Import file manually.');renderSourceUi();return false;}
  try{
    setRefreshState('reloading_data');
    const allowed=await ensureReadPermission(S.connectedSource.handle);
    if(!allowed){
      setRefreshState('export_failed');
      setSourceError('Reload failed (permission denied). Import file manually.');
      return false;
    }
    const file=await S.connectedSource.handle.getFile();
    const refreshedAt=new Date().toISOString();
    S.connectedSource.lastRefreshedAt=refreshedAt;
    if(S.connectedSource.canPersist){
      await saveConnectedSourceRecord({handle:S.connectedSource.handle,fileName:file.name,lastRefreshedAt:refreshedAt});
    }
    await loadFile(file);
    setRefreshState('success');
    renderSourceUi();
    return true;
  }catch(_){
    setRefreshState('export_failed');
    setSourceError('Reload failed. Import file manually.');
    return false;
  }
}

async function refresh(){
  setSourceError('');
  setSourceStatus('',null);
  if(!S.connectedSource.supported||!S.connectedSource.handle){
    setSourceError('No connected file. Use Home to reconnect.');
    renderSourceUi();
    return;
  }
  const beforeTs=S.exportTimestamp||null;
  let runResult=null;
  // Try local runner; silently fall through to file reload if unavailable
  try{
    setRefreshState('running_export');
    const resp=await fetch(`${S.connectedSource.runnerUrl}/run-export`,{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({})
    });
    if(!resp.ok){
      setRefreshState('export_failed');
      const payload=await resp.json().catch(()=>({}));
      setSourceError(payload.error||'Export failed. Keeping last successful data loaded.');
      return;
    }
    runResult=await resp.json();
    if(!runResult||runResult.ok!==true){
      setRefreshState('export_failed');
      setSourceError((runResult&&runResult.error)||'Export failed. Keeping last successful data loaded.');
      return;
    }
  }catch(_){/* runner not running — fall through to file reload */}
  const reloaded=await refreshMessages();
  if(!reloaded)return;
  if(runResult){
    if(runResult.changed===false){setRefreshState('output_unchanged');}
  }else if(beforeTs&&S.exportTimestamp===beforeTs){
    setRefreshState('stale_file');
  }
}

async function changeSource(){
  setSourceError('');
  try{if(S.connectedSource.supported&&S.connectedSource.canPersist)await clearConnectedSourceRecord();}catch(_){}
  S.connectedSource.handle=null;
  S.connectedSource.fileName='';
  S.connectedSource.lastRefreshedAt=null;
  setRefreshState('idle');
  renderSourceUi();
}

function loadData(data,save){
  S.conversations=data.conversations||[];S.selectedId=null;
  recategorize();
  reconcileDismissedState();
  document.getElementById('drop-screen').style.display='none';
  document.getElementById('app').classList.add('loaded');
  document.getElementById('app').classList.add('design-inbox-mode');
  wireInboxDesignIframe();
  try{ localStorage.setItem('rod_screen','inbox'); }catch(_){}
  if(save){try{localStorage.setItem(DATA_KEY,JSON.stringify(data));
    localStorage.setItem(META_KEY,JSON.stringify({savedAt:new Date().toISOString(),count:S.conversations.length}));}catch(_){}}
  setLastUpdatedTimestamp(data);
  handleTimeline(document.getElementById('timeline-filter').value);
}

function timeShiftBundledDemoData(data){
  const cloned=(typeof structuredClone==='function')
    ? structuredClone(data)
    : JSON.parse(JSON.stringify(data));
  const exportedMs=new Date(cloned.exported_at).getTime();
  if(Number.isNaN(exportedMs))return cloned;
  const deltaMs=Date.now()-exportedMs;
  const shiftIso=(iso)=>{
    const ms=new Date(iso).getTime();
    if(Number.isNaN(ms))return iso;
    return new Date(ms+deltaMs).toISOString();
  };
  cloned.exported_at=shiftIso(cloned.exported_at);
  (cloned.conversations||[]).forEach(c=>{
    c.last_message_at=shiftIso(c.last_message_at);
    c.latest_inbound_at=shiftIso(c.latest_inbound_at);
    (c.messages||[]).forEach(m=>{m.date=shiftIso(m.date);});
  });
  return cloned;
}

function resetData(){
  S.conversations=[];S.selectedId=null;S.newIds.clear();
  clearLastUpdatedTimestamp();
  document.getElementById('app').classList.remove('design-inbox-mode');
  document.getElementById('app').classList.remove('loaded');
  document.getElementById('drop-screen').style.display='flex';
  document.getElementById('drop-error').style.display='none';
  document.getElementById('file-input').value='';checkSavedData();renderSourceUi();
  setRefreshState('idle');
}


function wireInboxDesignIframe(){
  const frame=document.getElementById('inbox-design-frame');
  if(!frame)return;
  const wire=()=>{
    let doc=null;
    let win=null;
    try{
      win=frame.contentWindow;
      doc=frame.contentDocument||win.document;
    }catch(_){return;}
    if(!doc)return;

    try{ if(win)win.localStorage.setItem('rod_screen','inbox'); }catch(_){}
    let tries=0;
    const timer=setInterval(()=>{
      tries+=1;
      try{
        if(win&&typeof win.go==='function'){
          win.go('inbox');
          clearInterval(timer);
          return;
        }
        const inboxBtn=doc.querySelector('button[data-nav="inbox"]');
        if(inboxBtn){
          inboxBtn.click();
          clearInterval(timer);
          return;
        }
      }catch(_){}
      if(tries>40)clearInterval(timer);
    },50);
    try{
      if(win&&typeof win.go==='function')win.go('inbox');
      else{
        const inboxBtn=doc.querySelector('button[data-nav="inbox"]');
        if(inboxBtn)inboxBtn.click();
      }
    }catch(_){ }

    const landingBtn=doc.querySelector('button[data-nav="landing"],button[data-nav="about"]');
    if(landingBtn){
      landingBtn.onclick=(e)=>{e.preventDefault();resetData();};
    }

    const setupBtn=doc.querySelector('button[data-nav="setup"]');
    if(setupBtn){
      setupBtn.onclick=async (e)=>{
        e.preventDefault();
        await connectExportFile();
      };
    }

    const refreshBtn=doc.getElementById('refreshBtn');
    if(refreshBtn){
      refreshBtn.onclick=(e)=>{e.preventDefault();refresh();};
    }
    // Note: iframe Regenerate is wired by the patched standalone calling
    // window.parent.miranda2RegenAi() directly, not by overrides here.
  };
  frame.addEventListener('load',wire);
  if(frame.contentDocument?.readyState==='complete')wire();
}

function setLastUpdatedTimestamp(data){
  let iso=(data&&data.exported_at)||null,source='exported_at';
  if(!iso){
    try{
      const m=JSON.parse(localStorage.getItem(META_KEY));
      if(m&&m.savedAt){iso=m.savedAt;source='savedAt';}
    }catch(_){}
  }
  if(!iso){clearLastUpdatedTimestamp();return;}
  const ts=new Date(iso);
  if(Number.isNaN(ts.getTime())){clearLastUpdatedTimestamp();return;}
  S.exportTimestamp=ts.toISOString();
  S.exportTimestampSource=source;
  renderLastUpdated();
  if(S.lastUpdatedTimer)clearInterval(S.lastUpdatedTimer);
  S.lastUpdatedTimer=setInterval(renderLastUpdated,60000);
}

function clearLastUpdatedTimestamp(){
  if(S.lastUpdatedTimer){clearInterval(S.lastUpdatedTimer);S.lastUpdatedTimer=null;}
  S.exportTimestamp=null;S.exportTimestampSource=null;
  const el=document.getElementById('last-updated');
  if(!el)return;
  el.style.display='none';
  el.textContent='';
  el.title='';
  el.classList.remove('stale');
}

function relativeLastUpdated(d){
  const ms=Date.now()-new Date(d).getTime();
  const m=Math.floor(ms/60000);
  if(m<1)return'just now';
  if(m<60)return`${m}m ago`;
  const h=Math.floor(m/60);
  if(h<24)return`${h}h ago`;
  return`${Math.floor(h/24)}d ago`;
}

function renderLastUpdated(){
  if(!S.exportTimestamp)return;
  const el=document.getElementById('last-updated');
  if(!el)return;
  const ts=new Date(S.exportTimestamp);
  if(Number.isNaN(ts.getTime())){clearLastUpdatedTimestamp();return;}
  const rel=relativeLastUpdated(S.exportTimestamp);
  el.textContent=`Last updated: ${rel}`;
  el.title=ts.toLocaleString('en-US',{month:'short',day:'numeric',year:'numeric',hour:'numeric',minute:'2-digit'});
  const ageHrs=(Date.now()-ts.getTime())/3600000;
  if(ageHrs>24)el.classList.add('stale');else el.classList.remove('stale');
  el.style.display='inline';
}

// ── Recategorize ─────────────────────────────────────────────────────────────
function hasManualOverride(c){
  return !!((c.phone&&S.overrides[c.phone])||S.overrides[c.id]);
}

function isEligiblePersonalRecheck(c){
  return c.category==='personal'&&!c.contact_name&&!c.is_group&&!hasManualOverride(c);
}

function isHighConfidenceRideshare(t){
  const BRAND=['lyft','uber'];
  const TXN=['your driver','trip with','arriving in','arriving now','look for','license plate','pickup spot'];
  return BRAND.some(k=>t.includes(k))&&TXN.some(k=>t.includes(k));
}

function recategorize(){
  const SPAM=['trump','democrat','republican','midterm','gop ','dems ','vote yes','vote no','vote for',
    'polling','campaign','petition','volunteer','election day','ballot',
    'kelly services','randstad','recruiter at','recruitment','found a role','job opportunity',
    'job details','career goals','career options','open for work','open to work','hiring manager',
    'may i share','can i share','share the job','your resume','from indeed',
    'exclusive offer','limited time','act now',"don't miss",'sale ends','promo code','discount code','% off',
    'we made room','we cleared a spot','best deal','membership expires','free trial','expires tomorrow',
    '% return','percent return','locking in a stock','vip investors','paid opportunity','paid survey',
    'match.com','singles in','home solo','first introduction','dating profile',
    'dental check-up','check-up & cleaning','teeth whitening','we have openings',
    'open house','price reduced','home for sale','just listed','mls#','mls #','sq ft','sqft',
    'bd/','ba ','purchasing 1031','real estate',
    'reply stop','reply y to','text stop','opt out','opt-out','unsubscribe','msg & data rates',
    'free msg:','free msg ','we need your','we noticed','we selected','we found',
    'selected for','chosen for','quick conversation','are you free for a quick',
    'are you busy now','are you interested in','are you open to','would you be open',
    'reaching out','touching base','follow up','appreciation program','support team',
    'current issues in california','share your opinion'];
  const DELIV=['receipt from','view your receipt','your receipt','order confirmed','order is ready',
    'your order','payment received','payment confirmed','your appt','your appointment','appointment is',
    'scheduled for','confirm:','cancel:','reschedule:','is tomorrow','rsvp',
    'your ride','your driver','trip with','arriving now','license plate','car details','your lugg',
    'reservation at','booking confirmed','book a reservation',
    'your bill','bill is due','payment due','autopay','account ending in',
    'verification code','login code','security code','one-time code','one-time password',
    'use code:','your code is','your code:','authorize a login','clover.com','square.com','toast tab'];
  S.conversations.forEach(c=>{
    const uncategorizedEligible=c.category==='uncategorized'&&!c.contact_name&&!hasManualOverride(c);
    const personalRecheck=isEligiblePersonalRecheck(c);
    if(!uncategorizedEligible&&!personalRecheck)return;
    const t=(c.messages||[]).map(m=>(m.text||'').toLowerCase()).join(' ');
    if(personalRecheck){
      if(isHighConfidenceRideshare(t))c.category='delivery';
      return;
    }
    const ph=(c.phone||'').replace(/[\+\-\s]/g,'');
    if((ph.length<=6&&ph.length>0)||(c.phone||'').includes('@')){
      c.category=DELIV.some(k=>t.includes(k))?'delivery':'spam';return;}
    if(SPAM.some(k=>t.includes(k))){c.category='spam';return;}
    if(DELIV.some(k=>t.includes(k))){c.category='delivery';return;}
  });
}

function getCategory(c){
  // Phone-keyed override persists across re-exports
  if(c.phone&&S.overrides[c.phone])return S.overrides[c.phone];
  if(S.overrides[c.id])return S.overrides[c.id];
  const raw=c.category||'uncategorized';
  if(c.contact_name&&(raw==='delivery'||raw==='spam'))return'personal';
  return raw;
}

function normalizeIdentityToken(value){
  return String(value||'').trim().toLowerCase();
}

function normalizeHandleValue(value){
  const raw=String(value||'').trim().toLowerCase();
  if(!raw)return'';
  if(raw.includes('@'))return raw;
  return raw.replace(/[^0-9]/g,'');
}

function participantDismissKey(c){
  if(!c)return'';
  if(c.is_group){
    const groupName=normalizeIdentityToken(c.group_name);
    const handle=normalizeHandleValue(c.phone);
    if(groupName||handle)return`g:${groupName}|${handle}`;
    return`g:id:${normalizeIdentityToken(c.id)}`;
  }
  const handle=normalizeHandleValue(c.phone);
  if(handle)return`p:${handle}`;
  const contact=normalizeIdentityToken(c.contact_name);
  if(contact)return`p:name:${contact}`;
  return`p:id:${normalizeIdentityToken(c.id)}`;
}

function isRealTextMessageContent(text){
  const t=String(text||'').trim();
  if(!t)return false;
  if(t==='📎 Attachment')return false;
  return true;
}

function latestInboundTextAt(c){
  // Prefer the export-computed field, which covers the full message history
  // rather than just the 5-message preview stored in c.messages.
  if(c?.latest_inbound_at){
    const d=new Date(c.latest_inbound_at);
    if(!Number.isNaN(d.getTime()))return d.toISOString();
  }
  // Fallback: scan the 5-message preview (older exports without latest_inbound_at).
  const inbound=(c?.messages||[])
    .filter(m=>!m?.from_me&&isRealTextMessageContent(m?.text))
    .map(m=>m?.date)
    .map(d=>new Date(d))
    .filter(d=>!Number.isNaN(d.getTime()));
  if(!inbound.length)return null;
  return new Date(Math.max(...inbound.map(d=>d.getTime()))).toISOString();
}

function makeDismissRecord(c){
  return {
    key:participantDismissKey(c),
    dismissedAt:new Date().toISOString(),
    inboundCheckpointAt:latestInboundTextAt(c)||null,
    threadId:c?.id||''
  };
}

function saveDismissed(){
  try{localStorage.setItem(DISMISS_KEY,JSON.stringify(S.dismissed));}catch(_){}
}

function hasNewInboundSinceCheckpoint(c,rec){
  const nowInbound=latestInboundTextAt(c);
  if(!nowInbound)return false;
  if(!rec?.inboundCheckpointAt){
    // Legacy dismiss records may not have inboundCheckpointAt.
    // Fall back to dismissedAt so ignored threads don't auto-reappear on every load.
    const dismissedTs=new Date(rec?.dismissedAt||'').getTime();
    const nowTs=new Date(nowInbound).getTime();
    if(Number.isNaN(nowTs)||Number.isNaN(dismissedTs))return false;
    return nowTs>dismissedTs;
  }
  const nowTs=new Date(nowInbound).getTime();
  const checkpointTs=new Date(rec.inboundCheckpointAt).getTime();
  if(Number.isNaN(nowTs)||Number.isNaN(checkpointTs))return false;
  return nowTs>checkpointTs;
}

function getDismissRecord(c){
  if(!c)return null;
  const key=participantDismissKey(c);
  if(key&&S.dismissed[key]&&typeof S.dismissed[key]==='object')return S.dismissed[key];
  if(S.dismissed[c.id]===true||typeof S.dismissed[c.id]==='object'){
    const rec=makeDismissRecord(c);
    if(S.dismissed[c.id]&&typeof S.dismissed[c.id]==='object'){
      const old=S.dismissed[c.id];
      rec.dismissedAt=old.dismissedAt||rec.dismissedAt;
      rec.inboundCheckpointAt=old.inboundCheckpointAt||rec.inboundCheckpointAt;
    }
    if(key)S.dismissed[key]=rec;
    delete S.dismissed[c.id];
    saveDismissed();
    return rec;
  }
  return null;
}

function isDismissed(c){
  const rec=getDismissRecord(c);
  if(!rec)return false;
  if(hasNewInboundSinceCheckpoint(c,rec)){
    const key=participantDismissKey(c);
    if(key)delete S.dismissed[key];
    saveDismissed();
    return false;
  }
  return true;
}

function reconcileDismissedState(){
  let changed=false;
  S.conversations.forEach(c=>{
    const rec=getDismissRecord(c);
    if(!rec)return;
    if(hasNewInboundSinceCheckpoint(c,rec)){
      const key=participantDismissKey(c);
      if(key&&S.dismissed[key]){
        delete S.dismissed[key];
        changed=true;
      }
    }
  });
  if(changed)saveDismissed();
}

// ── Core filters ─────────────────────────────────────────────────────────────
function needsResponse(c){
  const cat=getCategory(c);
  if(cat==='spam'||cat==='delivery')return false;
  if(c.is_group)return false;
  if(c.i_replied_last)return false;
  if(isDismissed(c))return false;
  return true;
}
function inTimeline(c){
  const{timelineAfter,timelineBefore}=S.filter;
  if(!c.last_message_at)return false;
  const d=new Date(c.last_message_at);
  if(timelineAfter&&d<timelineAfter)return false;
  if(timelineBefore&&d>timelineBefore)return false;
  return true;
}
function actionable(){return S.conversations.filter(c=>needsResponse(c)&&inTimeline(c)&&c.contact_name);}
function allPersonalInTimeline(){return S.conversations.filter(c=>{
  const cat=getCategory(c);if(cat==='spam'||cat==='delivery')return false;
  if(c.is_group)return false;return inTimeline(c);});}
function allPersonalInTrailingDays(days){
  const cutoff=new Date();
  cutoff.setDate(cutoff.getDate()-days);
  cutoff.setHours(0,0,0,0);
  return S.conversations.filter(c=>{
    const cat=getCategory(c);if(cat==='spam'||cat==='delivery')return false;
    if(c.is_group)return false;
    if(!c.last_message_at)return false;
    return new Date(c.last_message_at)>=cutoff;
  });
}

// ── Score ─────────────────────────────────────────────────────────────────────
function computeScoreFromPersonal(personal){
  if(!personal.length)return{score:100,rate:100,speed:0,speedScore:100,hanging:0,hangingScore:100,replied:0,total:0};
  const replied=personal.filter(c=>c.i_replied_last||isDismissed(c));
  const unreplied=personal.filter(c=>!c.i_replied_last&&!isDismissed(c));
  const total=personal.length;
  const rate=Math.round((replied.length/total)*100);
  let avgWait=0;
  if(unreplied.length){avgWait=unreplied.reduce((s,c)=>{
    if(!c.last_message_at)return s;return s+(Date.now()-new Date(c.last_message_at).getTime())/3600000;},0)/unreplied.length;}
  let speedScore=100;if(avgWait>1)speedScore=Math.max(0,Math.round(100-(avgWait/72)*100));
  let hp=0;unreplied.forEach(c=>{if(!c.last_message_at)return;
    const h=(Date.now()-new Date(c.last_message_at).getTime())/3600000;
    if(h<1)hp+=1;else if(h<24)hp+=3;else if(h<72)hp+=6;else hp+=10;});
  const hangingScore=Math.max(0,100-hp);
  const score=Math.round(rate*0.45+speedScore*0.25+hangingScore*0.30);
  return{score:Math.max(0,Math.min(100,score)),rate,speed:avgWait,speedScore,hanging:unreplied.length,hangingScore,replied:replied.length,total};
}
function computeScore(){return computeScoreFromPersonal(allPersonalInTimeline());}
function computeFixedHistoryScore(){return computeScoreFromPersonal(allPersonalInTrailingDays(7));}
function scoreColor(s){if(s>=85)return'var(--green)';if(s>=65)return'var(--yellow)';if(s>=40)return'var(--orange)';return'var(--red)';}
function fmtSpeed(h){if(h<1)return'<1h';return Math.round(h)+'h';}
function scoreLabel(score){
  if(score<=15)return'actively ghosting 👻';
  if(score<=35)return'bad texter 😬';
  if(score<=55)return'hit or miss 🎲';
  if(score<=75)return'solid 👍';
  if(score<=90)return'on it ⚡️';
  return'ELITE responder 🏆';
}
function cleanScoreLabel(label){
  return String(label||'').replace(/\s*\(\d+\)\s*$/,'').trim();
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function waitHours(c){if(!c.last_message_at)return 0;return(Date.now()-new Date(c.last_message_at).getTime())/3600000;}
function urgency(c){const h=waitHours(c);if(h<1)return'green';if(h<24)return'yellow';if(h<72)return'orange';return'red';}
function relTime(d){if(!d)return'';const ms=Date.now()-new Date(d).getTime(),m=Math.floor(ms/60000),h=Math.floor(ms/3600000),dy=Math.floor(ms/86400000);
  if(m<1)return'now';if(m<60)return m+'m';if(h<24)return h+'h';if(dy<7)return dy+'d';
  return new Date(d).toLocaleDateString('en-US',{month:'short',day:'numeric'});}
function fullTime(d){if(!d)return'';return new Date(d).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});}
function displayName(c){if(c.is_group&&c.group_name&&c.group_name.trim())return c.group_name.trim();return c.contact_name||c.phone||'Unknown';}
function initial(c){return displayName(c).trim()[0].toUpperCase();}
function latestEventAt(c){return c.last_message_at||null;}
function latestEventText(c){return c.last_message_text||'';}
function literalRecentEvents(c){return(c.messages||[]).slice(-5);}
function previewTextIncluded(txt){
  if(!txt)return false;
  if(!PREVIEW_INCLUDE_ATTACHMENT&&txt==='📎 Attachment')return false;
  return true;
}
function previewRows(c){
  return (c.messages||[])
    .filter(m=>previewTextIncluded(String(m?.text??'').trim()))
    .slice(-2)
    .map(m=>({
      from_me:!!m.from_me,
      text:String(m.text).trim()
    }));
}


function getReplyAssistState(threadId){
  if(!S.replyAssistById[threadId]){
    S.replyAssistById[threadId]={
      isGenerating:false,
      suggestedReply:'',
      generationAttempted:false,
      blockedReason:'',
      copied:false,
      regenerateCount:0
    };
  }
  return S.replyAssistById[threadId];
}

function isPlainTextMessage(msg){
  const text=String(msg?.text??'').trim();
  if(!text)return false;
  return text!=='📎 Attachment';
}

function latestVisibleTextMessage(thread){
  const msgs=Array.isArray(thread?.messages)?thread.messages:[];
  for(let i=msgs.length-1;i>=0;i--){
    if(isPlainTextMessage(msgs[i])) return msgs[i];
  }
  return null;
}

function isAiThreadAllowlisted(thread){
  return !!thread&&AI_ALLOWED_DEMO_THREAD_IDS.has(String(thread.id||''));
}

function aiReplyBlockReason(thread){
  if(!isAiThreadAllowlisted(thread))return 'Not on demo allowlist';
  const lastVisible=latestVisibleTextMessage(thread);
  if(!lastVisible)return 'Need an incoming text to reply to';
  if(lastVisible.from_me)return 'Need an incoming text to reply to';
  return '';
}

function isAiReplyAllowed(thread){
  return aiReplyBlockReason(thread)==='';
}

function buildReplyContext(thread){
  const msgs=(thread?.messages||[])
    .filter(m=>isPlainTextMessage(m))
    .map(m=>({
      speaker:m?.from_me?'Me':'Them',
      text:String(m?.text??'').trim()
    }))
    .filter(m=>m.text.length>0);

  return msgs.slice(-6);
}

function getAiEndpoint(){
  return AI_SUGGEST_ROUTE;
}

function buildAiPrompt(context, latestInbound){
  const conversation=context.map(m=>`${m.speaker}: ${m.text}`).join('\n');
  return `Write exactly one short text reply to the latest inbound message.

Examples of good replies:

Input: “I saw you across the street and you did not acknowledge me. Don’t act like you were looking at a bird.”
Reply: “no fake bird, just poor situational awareness on my end”

Input: “Need yes/no. Is this outfit saying ‘charity lunch’ or ‘minor European princess’?”
Reply: “minor european princess, but like approachable”

Input: “I have an idea. It’s about longing.”
Reply: “no idea what that means, which is probably the problem”

Input: “I couldn’t help but wonder: is replying late a red flag or a branding exercise?”
Reply: “branding exercise, obviously”

Input: “Hypothetically, how bad is it to ignore a parking ticket for emotional reasons?”
Reply: “emotionally valid, financially inadvisable”

Input: “We gotta discuss dinner. Nobody knows where to eat anymore. Society’s collapsing.”
Reply: “agreed, we’ve lost the plot. where are we going?”

Input: “Here’s the phrase: ‘Hyperlocal media disruption engine.’ Too small?”
Reply: “that’s either a poem or a problem”

Constraints:
- write it like a normal text message
- respond directly to the latest messages
- avoid overly polished or formal phrasing
- do not use em dashes
- be witty and funny

Latest inbound message:
${latestInbound}

Recent text context:
${conversation}`;
}

function stripWrappingQuotes(text){
  let t=String(text||'').trim();
  const pairs=[['"','"'],['“','”'],['‘','’'],["'","'"]];
  for(let i=0;i<2;i++){
    for(const [open,close] of pairs){
      if(t.length>=2&&t.startsWith(open)&&t.endsWith(close)){
        t=t.slice(open.length,t.length-close.length).trim();
        break;
      }
    }
  }
  return t;
}

async function requestSuggestedReplyFromModel(thread, context){
  const latest=context[context.length-1];
  if(!latest||latest.speaker!=='Them') throw new Error('Latest message is not inbound text');
  const response=await fetch(getAiEndpoint(),{
    method:'POST',
    headers:{ 'Content-Type':'application/json' },
    body:JSON.stringify({
      ...(DEFAULT_AI_MODEL?{ model:DEFAULT_AI_MODEL }:{}),
      prompt:buildAiPrompt(context,latest.text),
      latestInbound:latest.text,
      context
    })
  });

  if(!response.ok){
    let serverError='';
    try{
      const errJson=await response.clone().json();
      serverError=String(errJson?.error||'').trim();
    }catch(_){
      const raw=await response.text().catch(()=> '');
      serverError=raw.slice(0,200);
    }
    const err=new Error(`AI request failed (${response.status})${serverError?': '+serverError:''}`);
    err.status=response.status;
    err.serverError=serverError;
    throw err;
  }

  const data=await response.json();
  const reply=stripWrappingQuotes(data?.reply||'');
  if(!reply)throw new Error('AI returned empty reply');
  return reply;
}

function containsBannedPreamble(text){
  return /(here'?s\s+(a\s+)?reply|you\s+could\s+say|response\s+you\s+could\s+send|i\s+hope\s+you'?re\s+doing\s+well|thank\s+you\s+for\s+reaching\s+out|i\s+apologize\s+for\s+the\s+delay)/i.test(text);
}

function hasGreetingOrSignoff(text){
  return /(^|\s)(hi|hello|hey|dear)\b|\b(best|sincerely|regards|thanks[,!]?|thank you[,!]?|cheers)\s*$|\bthanks for\b/i.test(text);
}

function looksAssistantLike(text){
  return /(absolutely|certainly|let me know|happy to help|as an ai|please feel free|that sounds great!?$)/i.test(text);
}

function validateAiReply(output, thread){
  const text=String(output||'').trim();
  if(!text)return { valid:false, reason:'empty' };
  const words=text.split(/\s+/).filter(Boolean);
  if(words.length<2)return { valid:false, reason:'near-empty' };
  if(words.length>20)return { valid:false, reason:'too-long' };
  if(text.includes('—'))return { valid:false, reason:'em-dash' };
  if(/["“”]/.test(text))return { valid:false, reason:'quotes' };
  if(containsBannedPreamble(text))return { valid:false, reason:'preamble' };
  if(hasGreetingOrSignoff(text))return { valid:false, reason:'greeting-signoff' };
  if(looksAssistantLike(text))return { valid:false, reason:'assistant-tone' };
  if(/[\n•]|\boption\s*1\b|\bor\s+\w+\s*\?/i.test(text))return { valid:false, reason:'multiple-options' };
  const inbound=buildReplyContext(thread).slice(-1)[0]?.text?.toLowerCase()||'';
  if(inbound){
    const inboundTerms=inbound.split(/[^a-z0-9']+/i).filter(w=>w.length>=4).slice(0,8);
    const out=text.toLowerCase();
    const overlap=inboundTerms.some(t=>out.includes(t));
    if(!overlap&&words.length>=10)return { valid:false, reason:'may-not-respond' };
  }
  return { valid:true, reason:'ok' };
}

async function generateAiReply(thread){
  const context=buildReplyContext(thread);
  if(!context.length)return { ok:false, reason:'no-context' };
  const latest=context[context.length-1];
  if(latest.speaker!=='Them')return { ok:false, reason:'latest-not-inbound' };
  const candidate=await requestSuggestedReplyFromModel(thread,context);
  const check=validateAiReply(candidate,thread);
  if(!check.valid)return { ok:false, reason:check.reason };
  return { ok:true, reply:candidate };
}

// Used by the embedded standalone design iframe (Inbox view). The patched
// standalone calls window.parent.miranda2RegenAi(selectedContact, aiBodyEl)
// instead of its design-tool default of picking from a hardcoded alts array.
async function generateAiReplyForIframeContact(contact){
  const msgs=Array.isArray(contact?.msgs)?contact.msgs:[];
  const context=msgs
    .filter(m=>m&&typeof m.t==='string'&&m.t.trim())
    .slice(-6)
    .map(m=>({ speaker:m.me?'Me':'Them', text:String(m.t).trim() }));
  if(!context.length)throw new Error('no-context');
  const latest=context[context.length-1];
  if(latest.speaker!=='Them')throw new Error('latest-not-inbound');
  const synthThread={
    id:contact?.phone||contact?.id||'',
    messages:context.map(c=>({ from_me:c.speaker==='Me', text:c.text }))
  };
  // Skip the strict legacy validator — the AI body is contenteditable so the
  // user can edit before sending, and over-aggressive validation was silently
  // dropping every model response and falling through to the curated baseline.
  const candidate=await requestSuggestedReplyFromModel(synthThread,context);
  const text=String(candidate||'').trim();
  if(!text)throw new Error('empty-reply');
  return text;
}

// Bridge function called directly by the patched standalone iframe.
// docs/standalone.html has its regenAi() rewritten to call
// window.parent.miranda2RegenAi(selectedContact, aiBodyEl). One well-known
// entry point means we don't depend on patching DOM listeners after the
// bundler swap.
window.miranda2RegenAi=async function(contact, bodyEl){
  if(!bodyEl)return;
  try{
    const reply=await generateAiReplyForIframeContact(contact||{});
    bodyEl.textContent=reply;
  }catch(err){
    console.warn('miranda2RegenAi failed',err);
    const detail=String(err&&(err.serverError||err.message)||'').trim();
    bodyEl.textContent=detail?`AI error: ${detail}`:'AI service unavailable';
  }
};

function renderSuggestedReplyUI(thread){
  if(!isAiThreadAllowlisted(thread))return '';

  const st=getReplyAssistState(thread.id);
  const triggerHtml=`<div class="ai-trigger-row"><button class="btn-dismiss" onclick="generateReplyForThread(${esc(JSON.stringify(thread.id))},false);event.stopPropagation()">AI Suggested Reply</button></div>`;

  if(st.isGenerating){
    return `${triggerHtml}<div class="ai-use-note">Generating...</div>`;
  }

  if(st.suggestedReply){
    return `
      ${triggerHtml}
      <div class="ai-suggest-card">
        <div class="ai-suggest-label">AI Suggested Reply</div>
        <div class="ai-suggest-text">${esc(st.suggestedReply)}</div>
        <div class="ai-suggest-actions">
          <button class="btn-dismiss" onclick="useSuggestedReply(${esc(JSON.stringify(thread.id))});event.stopPropagation()">Use</button>
          <button class="btn-dismiss" onclick="generateReplyForThread(${esc(JSON.stringify(thread.id))},true);event.stopPropagation()">Regenerate</button>
          <span class="ai-use-note">${st.copied?'Added to draft':''}</span>
        </div>
      </div>
    `;
  }

  if(st.generationAttempted&&st.blockedReason){
    return `
      ${triggerHtml}
      <div class="ai-suggest-card">
        <div class="ai-suggest-label">AI Suggested Reply</div>
        <div class="ai-suggest-text">Can't generate a reply for this message</div>
        <div class="ai-use-note">${esc(st.blockedReason)}</div>
      </div>
    `;
  }

  return triggerHtml;
}

// ── Render ───────────────────────────────────────────────────────────────────
function renderAll(){renderScore();saveScoreHistory();renderTrend();renderActions();renderOtherTexts();renderReview();}

// ── Score history ────────────────────────────────────────────────────────────
function getHistory(){
  try{const r=localStorage.getItem(HISTORY_KEY);return r?JSON.parse(r):[];}catch(_){return[];}
}
function localDateKey(d=new Date()){
  const y=d.getFullYear();
  const m=String(d.getMonth()+1).padStart(2,'0');
  const day=String(d.getDate()).padStart(2,'0');
  return `${y}-${m}-${day}`;
}

function saveScoreHistory(){
  const s=computeFixedHistoryScore();
  const today=localDateKey();
  let history=getHistory();
  // Update today's entry (last export of the day wins)
  const idx=history.findIndex(h=>h.date===today);
  const entry={date:today,score:s.score,rate:s.rate,hanging:s.hanging,total:s.total,replied:s.replied,window_days:7};
  if(idx>=0)history[idx]=entry;else history.push(entry);
  // Keep last 90 days max
  if(history.length>90)history=history.slice(-90);
  history.sort((a,b)=>a.date.localeCompare(b.date));
  try{localStorage.setItem(HISTORY_KEY,JSON.stringify(history));}catch(_){}
}

function computeStreaks(){
  const history=getHistory();
  if(!history.length)return{current:0,longest:0};
  // Build set of dates with entries
  const dates=new Set(history.map(h=>h.date));
  // Current streak: count backwards from today
  let current=0;
  let d=new Date();
  while(true){
    const ds=localDateKey(d);
    if(dates.has(ds)){current++;d.setDate(d.getDate()-1);}
    else break;
  }
  // Longest streak
  let longest=0,run=0;
  const sorted=[...dates].sort();
  for(let i=0;i<sorted.length;i++){
    if(i===0){run=1;}
    else{
      const prev=new Date(sorted[i-1]);prev.setDate(prev.getDate()+1);
      if(prev.toISOString().slice(0,10)===sorted[i])run++;
      else run=1;
    }
    if(run>longest)longest=run;
  }
  return{current,longest};
}

function renderTrend(){
  const history=getHistory();
  const chart=document.getElementById('trend-chart');
  const dates=document.getElementById('trend-dates');
  const latest=history.length?history[history.length-1].score:'--';
  document.getElementById('trend-preview').textContent=`Last 7d score: ${latest}`;

  if(history.length<2){
    chart.innerHTML='<div class="trend-empty">Run the export on different days to build your 7-day score trend</div>';
    dates.innerHTML='';
    document.getElementById('trend-best').textContent='--';
    document.getElementById('trend-avg').textContent='--';
    document.getElementById('trend-sessions').textContent=history.length;
    document.getElementById('trend-delta').textContent='--';
    const streaks=computeStreaks();
    document.getElementById('streak-current').textContent=streaks.current;
    document.getElementById('streak-longest').textContent=streaks.longest;
    return;
  }

  // Stats
  const scores=history.map(h=>h.score);
  const best=Math.max(...scores);
  const avg=Math.round(scores.reduce((a,b)=>a+b,0)/scores.length);
  document.getElementById('trend-best').textContent=best;
  document.getElementById('trend-best').style.color=scoreColor(best);
  document.getElementById('trend-avg').textContent=avg;
  document.getElementById('trend-avg').style.color=scoreColor(avg);
  document.getElementById('trend-sessions').textContent=history.length;

  // Delta vs last session
  if(history.length>=2){
    const curr=history[history.length-1].score;
    const prev=history[history.length-2].score;
    const delta=curr-prev;
    const deltaEl=document.getElementById('trend-delta');
    deltaEl.textContent=(delta>0?'+':'')+delta;
    deltaEl.style.color=delta>0?'var(--green)':delta<0?'var(--red)':'var(--text3)';
  }

  // Streaks
  const streaks=computeStreaks();
  document.getElementById('streak-current').textContent=streaks.current;
  document.getElementById('streak-longest').textContent=streaks.longest;

  // Draw SVG chart
  const w=580,h=90,pad=4;
  const n=scores.length;
  const min=Math.max(0,Math.min(...scores)-10);
  const max=Math.min(100,Math.max(...scores)+10);
  const range=max-min||1;

  const points=scores.map((s,i)=>{
    const x=pad+(i/(n-1))*(w-pad*2);
    const y=h-pad-((s-min)/range)*(h-pad*2);
    return{x,y,s};
  });

  // Gradient fill
  const linePath=points.map((p,i)=>(i===0?'M':'L')+p.x.toFixed(1)+','+p.y.toFixed(1)).join(' ');
  const areaPath=linePath+` L${points[n-1].x.toFixed(1)},${h} L${points[0].x.toFixed(1)},${h} Z`;

  const lastColor=scoreColor(scores[scores.length-1]);
  const lastColorHex=scores[scores.length-1]>=85?'#2dd4a0':scores[scores.length-1]>=65?'#f5c842':scores[scores.length-1]>=40?'#f59e42':'#ef4444';

  let dotsHtml=points.map((p,i)=>{
    const col=scoreColor(p.s);
    const r=i===n-1?5:3;
    const op=i===n-1?1:0.6;
    return`<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${r}" fill="${col}" opacity="${op}"/>`;
  }).join('');

  // Score labels on dots
  let labelsHtml='';
  // Show label on first, last, and best
  const showLabels=new Set([0,n-1]);
  const bestIdx=scores.indexOf(best);
  if(bestIdx!==0&&bestIdx!==n-1)showLabels.add(bestIdx);
  showLabels.forEach(i=>{
    const p=points[i];
    labelsHtml+=`<text x="${p.x.toFixed(1)}" y="${(p.y-10).toFixed(1)}" text-anchor="middle" fill="${scoreColor(p.s)}" font-size="11" font-weight="700" font-family="DM Mono,monospace">${p.s}</text>`;
  });

  chart.innerHTML=`<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
    <defs>
      <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="${lastColorHex}" stop-opacity="0.15"/>
        <stop offset="100%" stop-color="${lastColorHex}" stop-opacity="0"/>
      </linearGradient>
    </defs>
    <path d="${areaPath}" fill="url(#areaGrad)"/>
    <path d="${linePath}" fill="none" stroke="${lastColorHex}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    ${dotsHtml}${labelsHtml}
  </svg>`;

  // Date labels
  const first=history[0].date,last=history[history.length-1].date;
  const fmtDate=d=>new Date(d+'T12:00:00').toLocaleDateString('en-US',{month:'short',day:'numeric'});
  dates.innerHTML=`<span>${fmtDate(first)}</span><span>${fmtDate(last)}</span>`;
}

function renderScore(){
  const s=computeScore(),color=scoreColor(s.score);
  const circ=2*Math.PI*78,offset=circ*(1-s.score/100);
  const ring=document.getElementById('ring-fill');
  ring.style.stroke='url(#ring-gradient)';
  ring.style.filter=`drop-shadow(0 0 14px ${color})`;
  ring.setAttribute('stroke-dasharray',circ);ring.setAttribute('stroke-dashoffset',offset);
  document.getElementById('score-number').textContent=s.score;
  document.getElementById('score-number').style.color=color;
  const sum=document.getElementById('score-summary');
  sum.textContent=cleanScoreLabel(scoreLabel(s.score));
  document.getElementById('contrib-rate').textContent=s.rate+'%';
  document.getElementById('contrib-rate').style.color=scoreColor(s.rate);
  document.getElementById('contrib-rate-bar').style.width=s.rate+'%';
  document.getElementById('contrib-rate-bar').style.background=scoreColor(s.rate);
  const sl=s.hanging>0?fmtSpeed(s.speed):'—';
  document.getElementById('contrib-speed').textContent=sl;
  document.getElementById('contrib-speed').style.color=scoreColor(s.speedScore);
  document.getElementById('contrib-speed-bar').style.width=s.speedScore+'%';
  document.getElementById('contrib-speed-bar').style.background=scoreColor(s.speedScore);
  document.getElementById('contrib-hanging').textContent=s.hanging;
  const hc=s.hanging===0?'var(--green)':scoreColor(s.hangingScore);
  document.getElementById('contrib-hanging').style.color=hc;
  document.getElementById('contrib-hanging-bar').style.width=s.hangingScore+'%';
  document.getElementById('contrib-hanging-bar').style.background=hc;
}

function applyTheme(){
  document.body.setAttribute('data-theme',S.theme);
  const toggle=document.getElementById('theme-toggle');
  if(toggle)toggle.textContent=S.theme==='dark'?'light mode':'dark mode';
}

function toggleTheme(){
  S.theme=S.theme==='dark'?'light':'dark';
  applyTheme();
  try{localStorage.setItem(THEME_KEY,S.theme);}catch(_){}
}

function renderActions(){
  let list=actionable();
  list.sort((a,b)=>(a.last_message_at?new Date(a.last_message_at).getTime():0)-(b.last_message_at?new Date(b.last_message_at).getTime():0));
  if(S.actionFilter==='urgent')list=list.filter(c=>waitHours(c)>=24);
  else if(S.actionFilter==='today')list=list.filter(c=>{if(!c.last_message_at)return false;
    return new Date(c.last_message_at).toDateString()===new Date().toDateString();});
  document.getElementById('action-count').textContent =
    list.length === 1
      ? '1 person waiting for your response'
      : `${list.length} people waiting for your response`;
  const el=document.getElementById('action-list');
  if(!list.length){el.innerHTML='<div class="action-empty"><div class="action-empty-icon">✨</div><div>You\'re all caught up!</div></div>';return;}
  el.innerHTML=list.map(c=>{
    const name=displayName(c),rows=previewRows(c),phone=c.phone||'',smsHref=phone?'sms:'+phone.replace(/\s/g,''):'#';
    const msgs=literalRecentEvents(c),exp=c.id===S.selectedId;
    let previewHtml=rows.map(r=>`<div class="${r.from_me?'action-preview-mine':'action-preview'}"><span class="preview-label">${r.from_me?'You':'Them'}:</span> ${esc(r.text)}</div>`).join('');
    if(!previewHtml)previewHtml=`<div class="action-preview">${esc(latestEventText(c))}</div>`;
    const textRows=msgs
      .filter(m=>String(m?.text??'').trim())
      .map(m=>`<div><div>${esc(String(m.text).trim())}</div><div class="msg-time">${esc(fullTime(m.date))}</div></div>`).join('');
    return`<div class="action-item${exp?' expanded':''}" onclick="toggleExpand('${esc(c.id)}')">
      <div class="action-item-top">
        <div class="action-avatar">${esc(initial(c))}</div>
        <div class="action-body">
          <div class="action-name">${esc(name)}</div>
          ${previewHtml}
        </div>
        <div class="action-right">
          <span class="action-time">${esc(relTime(latestEventAt(c)))}</span>
          <div class="urgency-dot ${urgency(c)}"></div>
        </div>
      </div>
      <div class="action-detail" onclick="event.stopPropagation()">
        <div class="detail-messages">${textRows?textRows:'<div style="color:var(--text3);font-size:12px;text-align:center;padding:12px 0">No messages in export window</div>'}</div>
        <div class="detail-actions">
          ${phone?`<a class="btn-reply" href="${smsHref}">Reply in Messages ↗</a>`:''}
          <button class="btn-dismiss" onclick="dismissConvo('${esc(c.id)}')">No reply needed</button>
          ${renderFilterOutMenu(c.id)}
          ${renderSuggestedReplyUI(c)}
        </div>
      </div>
    </div>`;
  }).join('');
}

function otherTexts(){
  return S.conversations.filter(c=>needsResponse(c)&&inTimeline(c)&&!c.contact_name);
}

function renderOtherTexts(){
  const list=otherTexts().sort((a,b)=>{
    const at=a.last_message_at?new Date(a.last_message_at).getTime():0;
    const bt=b.last_message_at?new Date(b.last_message_at).getTime():0;
    return bt-at;
  });
  document.getElementById('other-count').textContent=list.length===1?'1 text':list.length+' texts';
  const el=document.getElementById('other-list');
  if(!list.length){el.innerHTML='<div class="review-empty">Nothing here</div>';return;}
  el.innerHTML=list.map(c=>{
    const name=displayName(c),rows=previewRows(c),phone=c.phone||'',smsHref=phone?'sms:'+phone.replace(/\s/g,''):'#';
    const msgs=literalRecentEvents(c),exp=c.id===S.selectedId;
    let previewHtml=rows.map(r=>`<div class="${r.from_me?'action-preview-mine':'action-preview'}"><span class="preview-label">${r.from_me?'You':'Them'}:</span> ${esc(r.text)}</div>`).join('');
    if(!previewHtml)previewHtml=`<div class="action-preview">${esc(latestEventText(c))}</div>`;
    const textRows=msgs
      .filter(m=>String(m?.text??'').trim())
      .map(m=>`<div><div>${esc(String(m.text).trim())}</div><div class="msg-time">${esc(fullTime(m.date))}</div></div>`).join('');
    return `<div class="action-item${exp?' expanded':''}" onclick="toggleExpand('${esc(c.id)}')">
      <div class="action-item-top">
        <div class="action-avatar">${esc(initial(c))}</div>
        <div class="action-body">
          <div class="action-name">${esc(name)}</div>
          ${previewHtml}
        </div>
        <div class="action-right">
          <span class="action-time">${esc(relTime(latestEventAt(c)))}</span>
        </div>
      </div>
      <div class="action-detail" onclick="event.stopPropagation()">
        <div class="detail-messages">${textRows?textRows:'<div style="color:var(--text3);font-size:12px;text-align:center;padding:12px 0">No messages in export window</div>'}</div>
        <div class="detail-actions">
          ${phone?`<a class="btn-reply" href="${smsHref}">Reply in Messages ↗</a>`:''}
          <button class="btn-dismiss" onclick="dismissConvo('${esc(c.id)}')">No reply needed</button>
          ${renderFilterOutMenu(c.id)}
          ${renderSuggestedReplyUI(c)}
        </div>
      </div>
    </div>`;
  }).join('');
}

function renderFilterOutMenu(id){
  const safeId=esc(id);
  return `<details class="filter-out-menu" onclick="event.stopPropagation()">
    <summary>Filter out ▾</summary>
    <div class="filter-out-popover">
      <button onclick="reclassify('${safeId}','delivery');closeFilterOutMenu(this,event)">Logistics</button>
      <button onclick="reclassify('${safeId}','spam');closeFilterOutMenu(this,event)">Spam</button>
    </div>
  </details>`;
}

function closeFilterOutMenu(btn,event){
  if(event)event.stopPropagation();
  const root=btn?.closest('.filter-out-menu');
  if(root)root.open=false;
}

// ── Actions ──────────────────────────────────────────────────────────────────
function handleTimeline(val){
  if(!val){S.filter.timelineAfter=null;S.filter.timelineBefore=null;}
  else{const cutoff=new Date();cutoff.setDate(cutoff.getDate()-parseInt(val));cutoff.setHours(0,0,0,0);
    S.filter.timelineAfter=cutoff;S.filter.timelineBefore=null;}
  renderAll();
}
function setActionFilter(f){S.actionFilter=f;
  document.querySelectorAll('.filter-chip').forEach(b=>b.classList.toggle('active',b.dataset.filter===f));renderActions();}
function toggleExpand(id){S.selectedId=S.selectedId===id?null:id;renderActions();renderOtherTexts();}
function dismissConvo(id){
  const thread=S.conversations.find(c=>c.id===id);
  if(!thread)return;
  const key=participantDismissKey(thread);
  if(!key)return;
  S.dismissed[key]=makeDismissRecord(thread);
  delete S.dismissed[id];
  saveDismissed();
  renderAll();
}


async function generateReplyForThread(id,isRegenerate){
  const thread=S.conversations.find(c=>c.id===id);
  if(!thread)return;
  if(!isAiThreadAllowlisted(thread))return;

  const st=getReplyAssistState(id);
  if(st.isGenerating)return;
  const blockedReason=aiReplyBlockReason(thread);
  if(blockedReason){
    st.generationAttempted=true;
    st.suggestedReply='';
    st.blockedReason=blockedReason;
    st.isGenerating=false;
    renderActions();
    return;
  }

  st.isGenerating=true;
  st.copied=false;
  st.blockedReason='';
  renderActions();

  try{
    await new Promise(r=>setTimeout(r,250));
    const result=await generateAiReply(thread);
    if(result.ok){
      st.suggestedReply=String(result.reply||'').trim();
      st.generationAttempted=true;
      st.blockedReason='';
      if(isRegenerate)st.regenerateCount=(st.regenerateCount||0)+1;
    }else{
      st.suggestedReply='';
      st.generationAttempted=true;
      st.blockedReason='';
      console.warn('AI suggestion suppressed after validation',{threadId:id,reason:result.reason});
    }
  }catch(err){
    st.suggestedReply='';
    st.generationAttempted=true;
    const detail=String(err?.serverError||err?.message||'').trim();
    st.blockedReason=detail?`AI service error: ${detail}`:'AI service unavailable';
    console.warn('AI suggestion failed',err);
  }finally{
    st.isGenerating=false;
    renderActions();
  }
}

function buildSmsHref(phone,body){
  const clean=String(phone||'').replace(/\s/g,'');
  if(!clean)return '#';
  const txt=String(body||'').trim();
  if(!txt)return `sms:${clean}`;
  return `sms:${clean}&body=${encodeURIComponent(txt)}`;
}

function useSuggestedReply(id){
  const thread=S.conversations.find(c=>c.id===id);
  if(!thread)return;
  const st=getReplyAssistState(id);
  const txt=String(st.suggestedReply||'').trim();
  if(!txt)return;

  const href=buildSmsHref(thread.phone||'',txt);
  if(href!=='#'){
    window.location.href=href;
    st.copied=true;
    renderActions();
    setTimeout(()=>{ st.copied=false; renderActions(); },1200);
    return;
  }

  navigator.clipboard.writeText(txt).then(()=>{
    st.copied=true;
    renderActions();
    setTimeout(()=>{ st.copied=false; renderActions(); },1200);
  }).catch(()=>{});
}

function toggleTrend(){
  S.trendOpen=!S.trendOpen;
  document.getElementById('trend-body').style.display=S.trendOpen?'block':'none';
  document.getElementById('trend-toggle-label').textContent=S.trendOpen?'Score history ▴':'Score history ▾';
}

// ── Review categories ────────────────────────────────────────────────────────
function toggleReview(){
  S.reviewOpen=!S.reviewOpen;
  document.getElementById('review-body').style.display=S.reviewOpen?'block':'none';
  document.getElementById('review-arrow').classList.toggle('open',S.reviewOpen);
  if(S.reviewOpen)renderReview();
}

function setReviewCat(cat){
  S.reviewCat=cat;
  document.querySelectorAll('.review-tab').forEach(t=>t.classList.toggle('active',t.dataset.cat===cat));
  renderReview();
}

function reviewConvos(cat){
  if(cat==='filtered'){
    return S.conversations.filter(c=>{
      const actual=getCategory(c);
      return actual==='spam'||actual==='delivery';
    });
  }
  return S.conversations.filter(c=>{
    const actual=getCategory(c);
    if(actual!==cat)return false;
    return true;
  });
}

function normFirstName(s){
  const raw=String(s||'').trim();
  if(!raw)return'';
  return raw.split(/\s+/)[0].replace(/[^a-zA-Z'-]/g,'').slice(0,30);
}

function saveNameSignal(){
  try{localStorage.setItem(NAME_SIGNAL_KEY,JSON.stringify({firstName:S.nameSignalFirst||''}));}catch(_){}
}

function setNameSignalEdit(on){
  S.nameSignalEditing=!!on;
  renderReview();
}

function saveNameSignalFromInput(){
  const input=document.getElementById('other-name-input');
  if(!input)return;
  S.nameSignalFirst=normFirstName(input.value);
  S.nameSignalEditing=false;
  saveNameSignal();
  renderReview();
}

function clearNameSignal(){
  S.nameSignalFirst='';
  S.nameSignalEditing=false;
  saveNameSignal();
  renderReview();
}

function recentInboundText(c){
  const msgs=(c.messages||[]).filter(m=>!m.from_me).slice(-3);
  return msgs.map(m=>String(m.text||'')).join(' ').toLowerCase();
}

function looksConversational(c){
  const msgs=(c.messages||[]).slice(-5);
  const inbound=msgs.filter(m=>!m.from_me).length;
  const outbound=msgs.filter(m=>m.from_me).length;
  const text=msgs.map(m=>String(m.text||'')).join(' ').toLowerCase();
  let s=0;
  if(inbound>0&&outbound>0)s+=2;
  if((text.match(/\?/g)||[]).length>0)s+=1;
  if(/\b(i|you|we|me|my|your)\b/.test(text))s+=1;
  return s;
}

function otherRankScore(c){
  let score=0;
  const now=Date.now();
  const lastAt=c.last_message_at?new Date(c.last_message_at).getTime():0;
  const ageH=lastAt?((now-lastAt)/3600000):9999;
  if(!c.i_replied_last){
    if(ageH<=24)score+=3;
    else if(ageH<=24*7)score+=2;
    else if(ageH<=24*14)score+=1;
  }
  const txt=recentInboundText(c);
  const introHint=/\b(this is|i'?m|my name is|who is this|nice to meet|met you|intro)\b/.test(txt);
  if(introHint)score+=2;
  const conv=looksConversational(c);
  if(conv>=3)score+=2;
  else if(conv>=2)score+=1;

  const first=normFirstName(S.nameSignalFirst).toLowerCase();
  if(first&&new RegExp(`\\b${first.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}\\b`,'i').test(txt)){
    score+=2;
    if(!introHint&&conv<2)score-=1; // keep name signal weak without conversational context
  }

  const txn=/\b(code|verification|appointment|receipt|order|delivery|unsubscribe|stop|promo|offer|payment due|bill)\b/.test(txt);
  if(txn)score-=3;
  return score;
}

function renderOtherSignalControl(){
  const status=S.nameSignalFirst?'Using name signal':'Name signal off';
  const safe=esc(S.nameSignalFirst||'');
  if(S.nameSignalEditing){
    return `<div class="other-signal-bar">
      <div class="other-signal-meta">
        <div class="other-signal-status">${status}</div>
        <div class="other-signal-help">Only affects ordering in Other.</div>
      </div>
      <div class="other-signal-actions">
        <input id="other-name-input" class="other-signal-input" type="text" maxlength="30" placeholder="First name" value="${safe}">
        <button class="review-btn secondary" onclick="saveNameSignalFromInput()">Save</button>
        <button class="review-btn secondary" onclick="setNameSignalEdit(false)">Cancel</button>
      </div>
    </div>`;
  }
  if(S.nameSignalFirst){
    return `<div class="other-signal-bar">
      <div class="other-signal-meta">
        <div class="other-signal-status">Using name signal</div>
        <div class="other-signal-help">Only affects ordering in Other.</div>
      </div>
      <div class="other-signal-actions">
        <button class="review-btn secondary" onclick="setNameSignalEdit(true)">Edit</button>
        <button class="review-btn secondary" onclick="clearNameSignal()">Clear</button>
      </div>
    </div>`;
  }
  return `<div class="other-signal-bar">
    <div class="other-signal-meta">
      <div class="other-signal-status">Name signal off</div>
      <div class="other-signal-help">Only affects ordering in Other.</div>
    </div>
    <div class="other-signal-actions">
      <button class="review-btn secondary" onclick="setNameSignalEdit(true)">Add</button>
    </div>
  </div>`;
}

function renderReview(){
  // Update counts
  const spamCount=reviewConvos('spam').length;
  const delivCount=reviewConvos('delivery').length;
  document.getElementById('review-count-filtered').textContent=spamCount+delivCount;
  document.getElementById('review-toggle-label').textContent=
    `Auto-filtered texts (${spamCount+delivCount})`;

  if(!S.reviewOpen)return;

  const list=reviewConvos(S.reviewCat);
  const el=document.getElementById('review-list');

  if(!list.length){
    el.innerHTML='<div class="review-empty">Nothing here</div>';
    return;
  }

  // Sort most recent first
  if(S.reviewCat==='uncategorized'){
    list.sort((a,b)=>{
      const as=otherRankScore(a),bs=otherRankScore(b);
      if(bs!==as)return bs-as;
      const at=a.last_message_at?new Date(a.last_message_at).getTime():0;
      const bt=b.last_message_at?new Date(b.last_message_at).getTime():0;
      return bt-at;
    });
  }else{
    list.sort((a,b)=>{
      const at=a.last_message_at?new Date(a.last_message_at).getTime():0;
      const bt=b.last_message_at?new Date(b.last_message_at).getTime():0;
      return bt-at;
    });
  }

  const control=S.reviewCat==='uncategorized'?renderOtherSignalControl():'';
  el.innerHTML=control+list.slice(0,50).map(c=>{
    const name=c.contact_name||c.phone||'Unknown';
    const preview=(latestEventText(c)||'').slice(0,60);
    const actual=getCategory(c);
    const cat=actual==='delivery'?'delivery':actual==='spam'?'spam':S.reviewCat;
    const reason=cat==='delivery'?'Logistics':'Spam';
    const CAT_LABELS={personal:'Personal',delivery:'Logistics',spam:'Spam',uncategorized:'Other'};
    const hasOverride=(c.phone&&S.overrides[c.phone])||S.overrides[c.id];
    const buttons=['personal','delivery','spam','uncategorized'].filter(cc=>cc!==cat).map(cc=>
      `<button class="review-btn" onclick="reclassify('${esc(c.id)}','${cc}');event.stopPropagation()">→ ${CAT_LABELS[cc]}</button>`
    ).join('')+(hasOverride?` <button class="review-btn" onclick="reclassify('${esc(c.id)}','auto');event.stopPropagation()" style="opacity:.5">↺ Reset</button>`:'');
    return`<div class="review-item">
      <span class="review-name">${esc(name)}</span>
      <span class="review-preview">${esc(preview)}</span>
      <span class="review-reason ${cat}">${reason}</span>
      ${buttons}
    </div>`;
  }).join('');
}

function reclassify(id,newCat){
  const conv=S.conversations.find(c=>c.id===id);
  const key=conv?.phone||id;
  if(newCat==='auto'){delete S.overrides[key];delete S.overrides[id];}
  else S.overrides[key]=newCat;
  try{localStorage.setItem(OVERRIDE_KEY,JSON.stringify(S.overrides));}catch(_){}
  renderAll();
}

function esc(s){return String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
init();
