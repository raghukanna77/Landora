import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { Link } from 'react-router-dom'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'

function MapFix(){ const map=useMap(); useEffect(()=>{ const id=setTimeout(()=> map.invalidateSize(), 250); const onR=()=> map.invalidateSize(); window.addEventListener('resize', onR); const t2=setTimeout(()=> map.invalidateSize(), 900); return ()=>{ clearTimeout(id); clearTimeout(t2); window.removeEventListener('resize', onR)}},[map]); return null }

export default function Dashboard(){
  const [summary,setSummary]=useState<any>(null)
  const [stage,setStage]=useState<any[]>([])
  const [heat,setHeat]=useState<any[]>([])
  const [alerts,setAlerts]=useState<any[]>([])
  const [projects,setProjects]=useState<any[]>([])
  useEffect(()=>{
    api.dashboardSummary().then(r=>setSummary(r.data))
    api.stageRisk().then(r=>setStage(r.data))
    api.heatmap().then(r=>setHeat(r.data))
    api.alerts().then(r=>setAlerts(r.data))
    api.projects('?sort=highest_risk').then(r=>setProjects(r.data.slice(0,8)))
  },[])
  if(!summary) return <div>Loading risk intelligence...</div>
  return <div className="grid" style={{gap:16}}>
    <div className="grid kpis">
      <div className="card metric"><div className="label">Total Projects</div><div className="value">{summary.total_projects}</div><div className="sub">DEMO DATA</div></div>
      <div className="card metric"><div className="label">High Risk</div><div className="value" style={{color:'#dc2626'}}>{summary.high_risk}</div></div>
      <div className="card metric"><div className="label">Medium Risk</div><div className="value" style={{color:'#d97706'}}>{summary.medium_risk}</div></div>
      <div className="card metric"><div className="label">Low Risk</div><div className="value" style={{color:'#16a34a'}}>{summary.low_risk}</div></div>
      <div className="card metric"><div className="label">Average Risk</div><div className="value">{(summary.average_risk*100).toFixed(0)}%</div></div>
      <div className="card metric"><div className="label">Early Alerts</div><div className="value">{summary.early_alerts}</div></div>
      <div className="card metric"><div className="label">Model</div><div className="value" style={{fontSize:14}}>{summary.model_health.version}</div><div className="sub">ROC-AUC {(summary.model_health.roc_auc||0).toFixed(2)}</div></div>
    </div>
    <div className="grid" style={{gridTemplateColumns:'1.5fr 1fr 1fr', gap:16}}>
      <div className="card" style={{height:360}}>
        <div style={{fontWeight:700,marginBottom:8}}>Risk Map — HIGH / MEDIUM / LOW</div>
        <MapContainer center={[22,78]} zoom={4.3} style={{height:310,width:'100%'}}>
          <MapFix/>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
          {heat.slice(0,250).map((h:any)=><CircleMarker key={h.project_id} center={[h.lat,h.lon]} radius={6} pathOptions={{color: h.risk_level==='HIGH'?'#dc2626':h.risk_level==='MEDIUM'?'#d97706':'#16a34a', fillColor: h.risk_level==='HIGH'?'#dc2626':h.risk_level==='MEDIUM'?'#d97706':'#16a34a', fillOpacity:0.8}}>
            <Popup><b>{h.name}</b><br/>{h.risk_level} {(h.probability*100).toFixed(0)}% — {h.stage} <br/><Link to={`/projects/${h.project_id}`}>Open Intelligence</Link></Popup>
          </CircleMarker>)}
        </MapContainer>
      </div>
      <div className="card">
        <div style={{fontWeight:700,marginBottom:8}}>Prioritized Project List</div>
        {projects.map((p:any)=><Link key={p.id} to={`/projects/${p.id}`} style={{display:'flex',justifyContent:'space-between',padding:'8px 0',borderBottom:'1px solid #e2e8f0'}}>
          <div><div style={{fontWeight:600,fontSize:12}}>{p.name}</div><div style={{fontSize:11,color:'#64748b'}}>{p.district}, {p.state} · {p.current_stage}</div></div>
          <span className={`badge ${p.risk_level}`}>{p.risk_level} {(p.probability*100).toFixed(0)}%</span>
        </Link>)}
        <Link to="/projects" className="btn" style={{marginTop:10,display:'inline-block'}}>View all projects</Link>
      </div>
      <div className="card">
        <div style={{fontWeight:700,marginBottom:8}}>Stage Risk</div>
        {stage.map((s:any)=><div key={s.stage} style={{display:'flex',justifyContent:'space-between',padding:'6px 0',borderBottom:'1px solid #f1f5f9'}}>
          <div><div style={{fontWeight:600,fontSize:12}}>{s.stage}</div><div style={{fontSize:11,color:'#64748b'}}>{s.project_count} projects</div></div>
          <div style={{textAlign:'right'}}><div style={{fontWeight:700}}>{(s.average_risk*100).toFixed(0)}%</div><div style={{fontSize:11,color:'#dc2626'}}>{s.high_risk_count} high</div></div>
        </div>)}
        <div style={{marginTop:12}}>
          <div style={{fontWeight:700,marginBottom:6}}>Recent Alerts</div>
          {alerts.slice(0,5).map((a:any)=><div key={a.id} className="alert">⚠ {a.message}</div>)}
          {alerts.length===0 && <div style={{fontSize:12,color:'#64748b'}}>No alerts</div>}
        </div>
      </div>
    </div>
  </div>
}
