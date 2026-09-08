import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { Link } from 'react-router-dom'

export default function RiskIntelligence(){
  const [summary,setSummary]=useState<any>(null)
  const [stage,setStage]=useState<any[]>([])
  const [projects,setProjects]=useState<any[]>([])
  const [drivers,setDrivers]=useState<any[]>([])
  useEffect(()=>{
    api.dashboardSummary().then(r=>setSummary(r.data))
    api.stageRisk().then(r=>setStage(r.data))
    api.projects('?sort=highest_risk').then(r=>{
      const top=r.data.slice(0,5)
      setProjects(top)
      if(top[0]) api.explanation(top[0].id).then(e=>setDrivers(e.data.slice(0,6)))
    })
  },[])
  if(!summary) return <div>Loading Risk Intelligence...</div>
  const total=summary.total_projects
  const dist=[
    {label:'CRITICAL',value: summary.high_risk, color:'#7f1d1d', pct: Math.round(summary.high_risk/total*100)},
    {label:'HIGH',value: Math.round(summary.high_risk*0.6), color:'#dc2626', pct: Math.round(summary.high_risk*0.6/total*100)},
    {label:'MEDIUM',value: summary.medium_risk, color:'#d97706', pct: Math.round(summary.medium_risk/total*100)},
    {label:'LOW',value: summary.low_risk, color:'#16a34a', pct: Math.round(summary.low_risk/total*100)},
  ]
  return <div className="grid" style={{gap:16}}>
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
      <h2 style={{fontWeight:900}}>Risk Intelligence — Explainable AI</h2>
      <span style={{fontSize:10,background:'#fef3c7',padding:'4px 8px',borderRadius:999,fontWeight:700}}>DEMO DATA — SYNTHETIC / CALIBRATED</span>
    </div>
    <div className="grid" style={{gridTemplateColumns:'repeat(4,1fr)',gap:12}}>
      {dist.map(d=> <div key={d.label} className="card" style={{borderLeft:`4px solid ${d.color}`}}><div style={{fontSize:10,fontWeight:800,letterSpacing:0.6,color:'#64748b'}}>{d.label}</div><div style={{fontSize:22,fontWeight:900}}>{d.value}</div><div style={{fontSize:11,color:'#64748b'}}>{d.pct}% of portfolio</div></div>)}
    </div>
    <div className="grid" style={{gridTemplateColumns:'1.2fr 0.8fr',gap:16}}>
      <div className="card">
        <div style={{fontWeight:800}}>Overall Risk Distribution</div>
        <div style={{marginTop:10,display:'grid',gap:8}}>
          {dist.map(d=> <div key={d.label} style={{display:'flex',alignItems:'center',gap:10}}><span style={{width:70,fontSize:11,fontWeight:700}}>{d.label}</span><div style={{flex:1,height:10,background:'#e2e8f0',borderRadius:999,overflow:'hidden'}}><div style={{width:`${d.pct}%`,height:'100%',background:d.color}}/></div><span style={{fontSize:11,fontWeight:700}}>{d.pct}%</span></div>)}
        </div>
        <div style={{marginTop:12,background:'#f8fafc',padding:10,borderRadius:8,fontSize:12}}>
          <b>Stage-Wise Risk</b>
          {stage.map(s=> <div key={s.stage} style={{display:'flex',justifyContent:'space-between',padding:'4px 0',fontSize:12}}><span>{s.stage}</span><span style={{fontWeight:700}}>{(s.average_risk*100).toFixed(0)}% avg • {s.high_risk_count} high</span></div>)}
        </div>
      </div>
      <div className="card">
        <div style={{fontWeight:800}}>WHY IS THIS PROJECT AT RISK? — SHAP</div>
        <div style={{fontSize:11,color:'#64748b'}}>Top drivers for highest-risk project: {projects[0]?.name}</div>
        {drivers.map((d:any)=> <div key={d.feature} style={{marginTop:10}}>
          <div style={{display:'flex',justifyContent:'space-between',fontSize:12}}><span style={{fontWeight:700}}>{d.feature}</span><span style={{color: d.direction==='increases risk' ? '#dc2626':'#16a34a'}}>{d.direction==='increases risk'?'+':''}{d.contribution.toFixed(2)}</span></div>
          <div className="why-bar"><div className="why-fill" style={{width:`${Math.min(100,Math.abs(d.contribution)*180)}%`, background: d.direction==='increases risk'?'#dc2626':'#16a34a'}}/></div>
          <div style={{fontSize:11,color:'#475569',marginTop:2}}>{d.human_explanation}</div>
        </div>)}
        <div style={{marginTop:10,background:'#fffbeb',padding:8,borderRadius:8,fontSize:11}}>AI-generated decision-support signal. Human review required. Model v1 • {new Date().toLocaleString()}</div>
      </div>
    </div>
    <div className="card">
      <div style={{fontWeight:800}}>Critical Projects — Immediate Attention</div>
      {projects.map((p:any)=> <Link key={p.id} to={`/projects/${p.id}`} style={{display:'flex',justifyContent:'space-between',padding:'8px 0',borderBottom:'1px solid #f1f5f9'}}>
        <div><div style={{fontWeight:700,fontSize:12}}>{p.name}</div><div style={{fontSize:11,color:'#64748b'}}>{p.state} {p.district} • {p.current_stage}</div></div>
        <span className={`badge ${p.risk_level}`}>{p.risk_level} {(p.probability*100).toFixed(0)}%</span>
      </Link>)}
    </div>
  </div>
}
