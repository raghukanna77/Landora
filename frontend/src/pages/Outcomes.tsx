import { useState } from 'react'
import { api } from '../services/api'

export default function Outcomes(){
  const [pid,setPid]=useState(1)
  const [list,setList]=useState<any[]>([])
  const [form,setForm]=useState({accepted:'YES', action_taken:'Consultation completed; grievance volume reduced', result:'Grievance volume reduced', outcome_label:'POSITIVE'})
  const load=()=> api.outcomes(pid).then(r=>setList(r.data))
  const submit=async()=>{
    await api.createOutcome({project_id:pid, recommendation_id:null, ...form})
    load()
  }
  return <div className="grid" style={{gap:16}}>
    <div className="card" style={{display:'flex',gap:8}}><input className="input" style={{maxWidth:120}} value={pid} onChange={e=>setPid(Number(e.target.value))}/><button className="btn primary" onClick={load}>Load Outcomes</button></div>
    <div className="card">
      <div style={{fontWeight:700}}>Record Outcome — Learning Queue</div>
      <div style={{display:'grid',gap:8,marginTop:8}}>
        <select className="select" value={form.accepted} onChange={e=>setForm({...form, accepted:e.target.value})}><option>YES</option><option>NO</option></select>
        <input className="input" value={form.action_taken} onChange={e=>setForm({...form, action_taken:e.target.value})} placeholder="Action taken"/>
        <input className="input" value={form.result} onChange={e=>setForm({...form, result:e.target.value})} placeholder="Result"/>
        <select className="select" value={form.outcome_label} onChange={e=>setForm({...form, outcome_label:e.target.value})}><option>POSITIVE</option><option>NEGATIVE</option><option>NEUTRAL</option></select>
        <button className="btn primary" onClick={submit}>Submit Outcome → Queued for retraining</button>
      </div>
    </div>
    <div className="card">
      <div style={{fontWeight:700}}>Outcomes — Project {pid}</div>
      {list.map((o:any)=><div key={o.id} style={{padding:'8px 0',borderBottom:'1px solid #e2e8f0',fontSize:12}}>
        <b>{o.outcome_label}</b> · {o.action_taken} · {o.result} · <span style={{color:'#64748b'}}>{o.created_at}</span> · Learning: Queued for model retraining
      </div>)}
      {list.length===0 && <div style={{color:'#64748b',fontSize:12}}>No outcomes.</div>}
    </div>
  </div>
}
