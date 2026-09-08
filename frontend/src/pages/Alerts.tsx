import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { Link } from 'react-router-dom'

export default function Alerts(){
  const [alerts,setAlerts]=useState<any[]>([])
  const [filter,setFilter]=useState('ALL')
  useEffect(()=>{ api.alerts().then(r=>setAlerts(r.data)); },[])
  // enrich with stage risk alerts from dashboard? For demo, use notifications as alerts
  const filtered = alerts.filter(a=> filter==='ALL' ? true : a.type===filter)
  const severity = (t:string)=> t==='HIGH_RISK' ? 'CRITICAL' : t==='GRIEVANCE_SPIKE' ? 'HIGH' : 'MEDIUM'
  return <div className="grid" style={{gap:16}}>
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
      <h2 style={{fontWeight:900}}>Alerts — Intelligent Early Warning</h2>
      <select className="select" value={filter} onChange={e=>setFilter(e.target.value)} style={{maxWidth:180}}><option>ALL</option><option>HIGH_RISK</option><option>GRIEVANCE_SPIKE</option></select>
    </div>
    <div className="grid" style={{gridTemplateColumns:'repeat(3,1fr)',gap:12}}>
      <div className="card"><div style={{fontSize:10,fontWeight:800,color:'#64748b'}}>NEW</div><div style={{fontSize:22,fontWeight:900}}>{alerts.filter(a=>a.status==='UNREAD').length}</div></div>
      <div className="card"><div style={{fontSize:10,fontWeight:800,color:'#64748b'}}>ACKNOWLEDGED</div><div style={{fontSize:22,fontWeight:900}}>{alerts.filter(a=>a.status==='READ').length}</div></div>
      <div className="card"><div style={{fontSize:10,fontWeight:800,color:'#64748b'}}>TOTAL</div><div style={{fontSize:22,fontWeight:900}}>{alerts.length}</div></div>
    </div>
    {filtered.slice(0,30).map((a:any)=> <div key={a.id} className="card" style={{borderLeft:`4px solid ${severity(a.type)==='CRITICAL'?'#7f1d1d':severity(a.type)==='HIGH'?'#dc2626':'#d97706'}`,display:'flex',justifyContent:'space-between',alignItems:'center'}}>
      <div>
        <div style={{display:'flex',gap:6,alignItems:'center'}}><span className={`badge ${severity(a.type)==='CRITICAL'?'CRITICAL':(severity(a.type)==='HIGH'?'HIGH':'MEDIUM')}`} style={severity(a.type)==='CRITICAL'?{background:'#7f1d1d',color:'#fff'}:{}}>{severity(a.type)}</span><span style={{fontSize:11,color:'#64748b'}}>{new Date(a.created_at).toLocaleString()}</span></div>
        <div style={{fontWeight:700,fontSize:13,marginTop:4}}>{a.message}</div>
        <div style={{fontSize:11,color:'#64748b'}}>Project {a.project_id || '—'} • Reason: {a.type.replace('_',' ')} • Status: {a.status}</div>
      </div>
      <div style={{display:'flex',gap:6}}>
        {a.project_id && <Link to={`/projects/${a.project_id}`} className="btn" style={{fontSize:12}}>Open</Link>}
        <span style={{fontSize:11,background:'#f1f5f9',padding:'6px 8px',borderRadius:8}}>{a.status}</span>
      </div>
    </div>)}
    {filtered.length===0 && <div className="card" style={{textAlign:'center',color:'#64748b'}}>No alerts for selected filter.</div>}
  </div>
}
