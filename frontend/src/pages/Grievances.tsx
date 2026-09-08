import { useEffect, useState } from 'react'
import { api } from '../services/api'

export default function Grievances(){
  const [text,setText]=useState('We have not received our compensation and nobody explained the SIA process.')
  const [res,setRes]=useState<any>(null)
  const [pid,setPid]=useState(1)
  const [list,setList]=useState<any[]>([])
  const [summary,setSummary]=useState<any>(null)
  const load=()=>{
    api.grievances(pid).then(r=>setList(r.data))
    api.grievanceSummary(pid).then(r=>setSummary(r.data))
  }
  useEffect(()=>{load()},[pid])
  const analyze=async()=>{ const r=await api.analyzeGrievance(text); setRes(r.data) }
  const submit=async()=>{ const r=await api.createGrievance(pid,text); setRes(r.data); load()}
  return <div className="grid" style={{gap:16}}>
    <div className="card">
      <div style={{fontWeight:800}}>Grievance NLP Engine — spaCy baseline · transformer-ready</div>
      <div style={{display:'flex',gap:8,marginTop:10,flexWrap:'wrap'}}>
        <input className="input" style={{maxWidth:120}} value={pid} onChange={e=>setPid(Number(e.target.value))} placeholder="Project ID"/>
        <input className="input" value={text} onChange={e=>setText(e.target.value)} style={{flex:1}}/>
        <button className="btn" onClick={analyze}>Analyze</button>
        <button className="btn primary" onClick={submit}>Submit & Update Risk</button>
      </div>
      {res && <div style={{marginTop:10,display:'flex',gap:8,flexWrap:'wrap'}}>
        <span className="badge HIGH">{res.sentiment}</span>
        <span className="badge MEDIUM">{res.intent}</span>
        <span className="badge LOW">{res.urgency}</span>
        <span style={{fontSize:12}}>Confidence {(res.confidence*100).toFixed(0)}%</span>
        <span style={{fontSize:12}}>Entities: {res.entities?.join(', ')}</span>
        {res.risk_updated && <span style={{fontSize:12,background:'#dcfce7',padding:'2px 6px',borderRadius:999}}>Risk updated: {(res.risk_updated.probability*100).toFixed(0)}% {res.risk_updated.risk_level}</span>}
      </div>}
      {summary && <div style={{marginTop:10,fontSize:12}}>Total {summary.total} · Negative {summary.negative_pct}% · High urgency {summary.high_urgency} · Top intent {summary.top_intent}</div>}
    </div>
    <div className="card">
      <div style={{fontWeight:700}}>Grievances for Project {pid}</div>
      {list.map((g:any)=><div key={g.id} style={{borderBottom:'1px solid #e2e8f0',padding:'8px 0'}}>
        <div style={{fontSize:13}}>{g.text}</div>
        <div style={{fontSize:11,color:'#64748b'}}>{g.sentiment} · {g.intent} · {g.urgency} · {(g.confidence*100).toFixed(0)}% · {g.cluster_id}</div>
      </div>)}
      {list.length===0 && <div style={{color:'#64748b',fontSize:12,marginTop:8}}>No grievances.</div>}
    </div>
  </div>
}
