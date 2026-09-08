import { useState } from 'react'
import { api } from '../services/api'

export default function Recommendations(){
  const [pid,setPid]=useState(1)
  const [list,setList]=useState<any[]>([])
  const load=()=> api.advisory(pid).then(r=>setList(r.data))
  const act=async(id:number, type:string)=>{
    if(type==='accept') await api.accept(id)
    if(type==='reject') await api.reject(id)
    load()
  }
  return <div className="grid" style={{gap:12}}>
    <div className="card" style={{display:'flex',gap:8}}><input className="input" style={{maxWidth:120}} value={pid} onChange={e=>setPid(Number(e.target.value))}/><button className="btn primary" onClick={load}>Load Advisory — AI-assisted recommendation · decision support</button></div>
    {list.map((r:any,idx:number)=><div key={r.id} className="card" style={{borderLeft:`4px solid ${r.priority==='HIGH'?'#dc2626':r.priority==='MEDIUM'?'#d97706':'#16a34a'}`}}>
      <div style={{display:'flex',justifyContent:'space-between'}}><b>#{idx+1} {r.action}</b><span className={`badge ${r.priority==='HIGH'?'HIGH':'MEDIUM'}`}>{r.priority}</span></div>
      <div style={{fontSize:12,marginTop:4}}>Why: {r.reason} · Owner: <b>{r.owner_role}</b> · Predicted reduction {(r.predicted_risk_reduction*100).toFixed(0)} pp</div>
      <div style={{fontSize:11,color:'#64748b'}}>Status: {r.status} · Stage: {r.stage}</div>
      <div style={{display:'flex',gap:6,marginTop:8}}>
        <button className="btn primary" onClick={()=>act(r.id,'accept')}>Accept</button>
        <button className="btn" onClick={()=>act(r.id,'reject')}>Reject</button>
      </div>
    </div>)}
    {list.length===0 && <div className="card" style={{color:'#64748b'}}>No recommendations — click Load.</div>}
  </div>
}
