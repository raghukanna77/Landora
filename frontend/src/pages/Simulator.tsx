import { useEffect, useState } from 'react'
import { api } from '../services/api'

export default function Simulator(){
  const [pid,setPid]=useState(1)
  const [p,setP]=useState<any>(null)
  const [changes,setChanges]=useState<any>({consultation_progress_pct:75, document_completeness_pct:90, compensation_pending_pct:30, legal_disputes:2})
  const [res,setRes]=useState<any>(null)
  useEffect(()=>{ api.project(pid).then(r=>{setP(r.data); setChanges({consultation_progress_pct:75, document_completeness_pct:r.data.document_completeness_pct, compensation_pending_pct:r.data.compensation_pending_pct, legal_disputes:r.data.legal_disputes})})},[pid])
  const run=async()=>{ const r=await api.simulate(pid,changes); setRes(r.data)}
  if(!p) return <div>Loading...</div>
  return <div className="grid" style={{gap:16}}>
    <div className="card"><b>Counterfactual Simulator</b> — <span style={{background:'#fef3c7',padding:'2px 6px',borderRadius:999,fontSize:11}}>SIMULATION — NOT AN ACTUAL RECORD CHANGE</span>
      <div style={{marginTop:8,display:'flex',gap:8}}><input className="input" style={{maxWidth:120}} value={pid} onChange={e=>setPid(Number(e.target.value))}/> <button className="btn primary" onClick={run}>Run Simulation</button></div>
    </div>
    <div className="grid" style={{gridTemplateColumns:'1fr 1fr 1fr',gap:16}}>
      <div className="card"><div style={{fontWeight:700}}>Current — ACTUAL</div>
        <div style={{fontSize:28,fontWeight:800}}>{(p.risk?.probability*100).toFixed(0)}%</div>
        <div className={`badge ${p.risk?.risk_level}`}>{p.risk?.risk_level}</div>
        <div style={{fontSize:12,marginTop:8}}>Consultation {p.consultation_progress_pct}%<br/>Documents {p.document_completeness_pct}%<br/>Compensation pending {p.compensation_pending_pct}%<br/>Legal {p.legal_disputes}</div>
      </div>
      <div className="card"><div style={{fontWeight:700}}>Controls</div>
        <label style={{fontSize:12}}>Consultation Progress {changes.consultation_progress_pct}%<input type="range" min={0} max={100} value={changes.consultation_progress_pct} onChange={e=>setChanges({...changes, consultation_progress_pct:Number(e.target.value)})} className="slider"/></label>
        <label style={{fontSize:12}}>Document Completeness {changes.document_completeness_pct}%<input type="range" min={0} max={100} value={changes.document_completeness_pct} onChange={e=>setChanges({...changes, document_completeness_pct:Number(e.target.value)})} className="slider"/></label>
        <label style={{fontSize:12}}>Compensation Pending {changes.compensation_pending_pct}%<input type="range" min={0} max={100} value={changes.compensation_pending_pct} onChange={e=>setChanges({...changes, compensation_pending_pct:Number(e.target.value)})} className="slider"/></label>
        <label style={{fontSize:12}}>Legal Disputes {changes.legal_disputes}<input type="number" value={changes.legal_disputes} onChange={e=>setChanges({...changes, legal_disputes:Number(e.target.value)})} className="input"/></label>
      </div>
      <div className="card" style={{background: res? '#f0fdf4':'#fff', border: res?'2px solid #16a34a':'1px solid #e2e8f0'}}><div style={{fontWeight:700}}>After — SIMULATION</div>
        {res ? <><div style={{fontSize:28,fontWeight:800}}>{(res.after_probability*100).toFixed(0)}%</div><div className={`badge ${res.after_level}`}>{res.after_level}</div><div style={{marginTop:8,fontWeight:700, color: res.risk_change<0?'#16a34a':'#dc2626'}}>{res.risk_change>0?'+':''}{(res.risk_change*100).toFixed(0)} pp · {res.interpretation}</div><div style={{fontSize:11,marginTop:4}}>Before { (res.before_probability*100).toFixed(0)}% → After {(res.after_probability*100).toFixed(0)}%</div></> : <div style={{fontSize:12,color:'#64748b',marginTop:20}}>Run simulation to see delta.</div>}
      </div>
    </div>
  </div>
}
