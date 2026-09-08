const BASE = ''
function authHeader(){ const t=localStorage.getItem('token'); return t? {Authorization:`Bearer ${t}`}: {} as any }
async function req(path:string, opts:any={}){
  const res=await fetch(`${BASE}${path}`, { ...opts, headers:{'Content-Type':'application/json', ...authHeader(), ...(opts.headers||{})}})
  const j=await res.json().catch(()=>({}))
  if(!res.ok) throw new Error(j.detail || j.error?.message || 'Request failed')
  return j
}
export const api={
  login:(u:string,p:string)=> req('/api/auth/login',{method:'POST', body:JSON.stringify({username:u,password:p})}),
  me:()=> req('/api/auth/me'),
  dashboardSummary:()=> req('/api/dashboard/summary'),
  stageRisk:()=> req('/api/dashboard/stage-risk'),
  heatmap:()=> req('/api/dashboard/heatmap'),
  alerts:()=> req('/api/dashboard/alerts'),
  projects:(q:string)=> req(`/api/projects${q}`),
  project:(id:number)=> req(`/api/projects/${id}`),
  risk:(id:number)=> req(`/api/projects/${id}/risk`),
  predict:(id:number)=> req(`/api/projects/${id}/predict`,{method:'POST'}),
  explanation:(id:number)=> req(`/api/projects/${id}/explanation`),
  precedents:(id:number)=> req(`/api/projects/${id}/precedents`),
  grievances:(id:number)=> req(`/api/projects/${id}/grievances`),
  grievanceSummary:(id:number)=> req(`/api/projects/${id}/grievance-summary`),
  analyzeGrievance:(text:string)=> req('/api/grievances/analyze',{method:'POST', body:JSON.stringify({text})}),
  createGrievance:(project_id:number,text:string)=> req('/api/grievances',{method:'POST', body:JSON.stringify({project_id,text})}),
  simulate:(project_id:number,changes:any)=> req('/api/simulation/counterfactual',{method:'POST', body:JSON.stringify({project_id,changes})}),
  advisory:(id:number)=> req(`/api/projects/${id}/advisory`),
  accept:(id:number)=> req(`/api/recommendations/${id}/accept`,{method:'POST'}),
  reject:(id:number)=> req(`/api/recommendations/${id}/reject`,{method:'POST'}),
  outcomes:(id:number)=> req(`/api/projects/${id}/outcomes`),
  createOutcome:(data:any)=> req('/api/outcomes',{method:'POST', body:JSON.stringify(data)}),
  modelStatus:()=> req('/api/model/status'),
  modelMetrics:()=> req('/api/model/metrics'),
  retrainingQueue:()=> req('/api/retraining/queue'),
  train:()=> req('/api/model/train',{method:'POST'}),
  approve:()=> req('/api/model/approve',{method:'POST'}),
  voice:(project_id:number,language:string)=> req('/api/voice/briefing',{method:'POST', body:JSON.stringify({project_id,language})}),
  notifications:()=> req('/api/notifications'),
  submitComplaint:(data:any)=> fetch('/api/complaints/public',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).then(r=>r.json()),
  trackComplaint:(id:string)=> fetch(`/api/complaints/track/${id}`).then(r=>r.json()),
  listComplaints:()=> req('/api/complaints'),
}
