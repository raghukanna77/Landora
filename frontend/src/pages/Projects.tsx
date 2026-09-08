import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { Link } from 'react-router-dom'

export default function Projects(){
  const [list,setList]=useState<any[]>([])
  const [q,setQ]=useState(''); const [risk,setRisk]=useState('ALL'); const [stage,setStage]=useState('ALL'); const [sort,setSort]=useState('highest_risk')
  const fetch=()=>{
    const qs=new URLSearchParams()
    if(q) qs.set('search',q)
    if(risk) qs.set('risk',risk)
    if(stage) qs.set('stage',stage)
    if(sort) qs.set('sort',sort)
    api.projects('?'+qs.toString()).then(r=>setList(r.data))
  }
  useEffect(()=>{fetch()},[])
  return <div className="grid" style={{gap:12}}>
    <div className="card">
      <div style={{fontWeight:800,marginBottom:8}}>Projects — DEMO DATA — SYNTHETIC / CALIBRATED</div>
      <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
        <input className="input" placeholder="Search name or code" value={q} onChange={e=>setQ(e.target.value)} style={{maxWidth:240}}/>
        <select className="select" value={risk} onChange={e=>setRisk(e.target.value)} style={{maxWidth:140}}><option>ALL</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select>
        <select className="select" value={stage} onChange={e=>setStage(e.target.value)} style={{maxWidth:160}}><option>ALL</option><option>Notification</option><option>SIA</option><option>Consent</option><option>Award</option><option>Compensation</option><option>Possession</option></select>
        <select className="select" value={sort} onChange={e=>setSort(e.target.value)} style={{maxWidth:160}}><option value="highest_risk">Highest risk</option><option value="lowest_risk">Lowest risk</option><option value="newest">Newest</option></select>
        <button className="btn primary" onClick={fetch}>Filter</button>
      </div>
    </div>
    <div className="card" style={{overflowX:'auto'}}>
      <table className="table"><thead><tr><th>Project</th><th>State/District</th><th>Stage</th><th>Risk</th><th></th></tr></thead>
      <tbody>{list.map((p:any)=><tr key={p.id}><td><b>{p.name}</b><br/><span style={{fontSize:11,color:'#64748b'}}>{p.project_code}</span></td><td>{p.state} / {p.district}</td><td>{p.current_stage}</td><td><span className={`badge ${p.risk_level}`}>{p.risk_level} {(p.probability*100).toFixed(0)}%</span></td><td><Link className="btn" to={`/projects/${p.id}`}>Open</Link></td></tr>)}</tbody></table>
      {list.length===0 && <div style={{padding:20,textAlign:'center',color:'#64748b'}}>No projects found.</div>}
    </div>
  </div>
}
