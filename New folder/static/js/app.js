// Theme toggle
(function(){
  const root = document.documentElement;
  const key = 'catrack-theme';
  const saved = localStorage.getItem(key);
  if(saved){ root.setAttribute('data-theme', saved); }
  const btn = document.getElementById('themeToggle');
  if(btn){
    btn.addEventListener('click', ()=>{
      const next = (root.getAttribute('data-theme') === 'dark') ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      localStorage.setItem(key, next);
    });
  }
})();

// Dashboard charts
(function(){
  const el = document.getElementById('byProjectChart');
  const dataEl = document.getElementById('byProjectData');
  if(!el || !dataEl) return;
  try{
    const rows = JSON.parse(dataEl.textContent || '[]');
    const labels = rows.map(r => `${r.project__number}`);
    const values = rows.map(r => r.open_count || 0);
    const ctx = el.getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Open Submittals',
          data: values,
          borderRadius: 8,
          backgroundColor: 'rgba(124, 92, 255, 0.6)'
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { x: { grid: { display:false } }, y: { grid: { color:'rgba(255,255,255,0.06)' }, ticks: { precision:0 } } }
      }
    });
  }catch(e){ console.warn('Chart init failed', e); }
})();

// Due next 7 days chart
(function(){
  const el = document.getElementById('due7Chart');
  const dataEl = document.getElementById('due7Data');
  if(!el || !dataEl) return;
  try{
    const rows = JSON.parse(dataEl.textContent || '[]');
    const labels = rows.map(r => r.date);
    const subs = rows.map(r => r.submittals||0);
    const rfis = rows.map(r => r.rfis||0);
    const ctx = el.getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label:'Submittals', data: subs, backgroundColor:'rgba(124,92,255,0.7)', borderRadius:8 },
          { label:'RFIs', data: rfis, backgroundColor:'rgba(14,165,233,0.7)', borderRadius:8 }
        ]
      },
      options: {
        responsive:true,
        plugins:{ legend:{ position:'bottom' } },
        scales:{ x:{ grid:{ display:false } }, y:{ grid:{ color:'rgba(255,255,255,0.06)' }, ticks:{ precision:0 } } }
      }
    });
  }catch(e){ console.warn('Due7 chart init failed', e); }
})();

// HTMX toasts
(function(){
  const toasts = document.getElementById('toasts');
  if(!toasts) return;
  function show(msg, kind='good', timeout=2000){
    const div=document.createElement('div');
    div.className='toast '+kind; div.textContent=msg; toasts.appendChild(div);
    setTimeout(()=>{div.style.opacity='0'; setTimeout(()=>div.remove(), 400)}, timeout);
  }
  document.body.addEventListener('htmx:afterRequest', function(evt){
    try{
      const method = (evt.detail && evt.detail.requestConfig && evt.detail.requestConfig.verb)||'';
      const status = evt.detail.xhr.status;
      if(['post','put','patch','delete'].includes(method.toLowerCase())){
        if(status>=200 && status<400){ show('Saved'); }
      }
    }catch(e){}
  });
  document.body.addEventListener('htmx:responseError', function(evt){ show('Error: '+evt.detail.xhr.status, 'bad', 3500); });
})();

// Inline edit toggling
(function(){
  function bind(root){
    root.querySelectorAll('.inline-edit').forEach(w=>{
      const disp = w.querySelector('.display');
      const input = w.querySelector('.editor input, .editor textarea, .editor select');
      if(disp){ disp.addEventListener('click', ()=>{ w.classList.add('active'); if(input){ setTimeout(()=>input.focus(), 10);} }); }
      if(input){
        input.addEventListener('keydown', (e)=>{ if(e.key==='Escape'){ w.classList.remove('active'); }});
        input.addEventListener('blur', ()=>{ const form=w.querySelector('.editor'); if(form && form.tagName==='FORM'){ if(input.value!=input.getAttribute('value')){ form.requestSubmit(); } else { w.classList.remove('active'); } } });
      }
    });
  }
  document.addEventListener('DOMContentLoaded', ()=>bind(document));
  document.body.addEventListener('htmx:afterSwap', (e)=>{ bind(e.target||document); });
})();
