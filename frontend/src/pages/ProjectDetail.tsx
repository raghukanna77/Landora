import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../services/api'

export default function ProjectDetail(){
  const {id}=useParams()
  const pid=Number(id)
  const [p,setP]=useState<any>(null); const [risk,setRisk]=useState<any>(null); const [prec,setPrec]=useState<any[]>([]); const [gSum,setGSum]=useState<any>(null)
  const [voice,setVoice]=useState<any>(null)
  useEffect(()=>{
    api.project(pid).then(r=>setP(r.data))
    api.risk(pid).then(r=>setRisk(r.data)).catch(()=>{})
    api.precedents(pid).then(r=>setPrec(r.data))
    api.grievanceSummary(pid).then(r=>setGSum(r.data))
  },[pid])
  const doVoice=async(lang:string)=>{
    const r=await api.voice(pid,lang); setVoice(r.data)
  }
  const predict=async()=>{ const r=await api.predict(pid); setRisk(r.data); window.location.reload()}
  if(!p) return <div>Loading...</div>
  const prob = p.risk?.probability ?? risk?.probability ?? 0
  const level = p.risk?.risk_level ?? risk?.risk_level ?? 'LOW'
  return <div className="grid" style={{gap:16}}>
    <div className="card" style={{display:'flex',justifyContent:'space-between',flexWrap:'wrap',gap:12}}>
      <div><h2 style={{fontWeight:800}}>{p.name} <span style={{fontWeight:400,fontSize:12,color:'#64748b'}}> {p.project_code}</span></h2><div style={{fontSize:12,color:'#64748b'}}>{p.state} · {p.district} · {p.department} · {p.current_stage} · {p.project_size}</div>
        <div style={{marginTop:6,display:'flex',gap:6,flexWrap:'wrap'}}>
          <span className={`badge ${level}`}>{level} {(prob*100).toFixed(0)}% — Predicted Delay Risk</span>
          <span style={{fontSize:11,background:'#f1f5f9',padding:'4px 8px',borderRadius:999}}>Model {p.risk?.model_version}</span>
        </div>
        <div style={{fontSize:11,color:'#64748b',marginTop:4}}>AI-assisted decision support · predicted risk · human-in-the-loop · DEMO DATA</div>
      </div>
      <div style={{textAlign:'right'}}>
        <div style={{fontSize:28,fontWeight:800}}>{(prob*100).toFixed(0)}%</div>
        <div className={`badge ${level}`} style={{justifyContent:'center'}}>{level} RISK</div>
        <div><button className="btn primary" style={{marginTop:8}} onClick={predict}>Re-predict</button></div>
      </div>
    </div>
    <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>{["Notification","SIA","Consent","Award","Compensation","Possession"].map(s=><div key={s} className="card" style={{flex:1,minWidth:120,textAlign:'center',background: s===p.current_stage?'#0f1e3a':'#fff', color: s===p.current_stage?'#fff':'#0f172a'}}><div style={{fontSize:11,fontWeight:700}}>{s}</div><div style={{fontSize:11,opacity:0.7}}>{s===p.current_stage?'● Current':''}</div></div>)}</div>
    <div className="grid" style={{gridTemplateColumns:'1.2fr 0.8fr', gap:16}}>
      <div className="grid" style={{gap:16}}>
        <div className="card">
          <div style={{fontWeight:800,marginBottom:8}}>WHY IS THIS PROJECT AT RISK?</div>
          <div style={{fontSize:11,color:'#64748b',marginBottom:8}}>SHAP TreeExplainer · Top 5 drivers</div>
          {(risk?.explanations||[]).slice(0,5).map((e:any)=><div key={e.feature} style={{marginBottom:10}}>
            <div style={{display:'flex',justifyContent:'space-between'}}><span style={{fontWeight:600,fontSize:12}}>{e.feature.toUpperCase()} <span style={{color: e.direction==='increases risk'?'#dc2626':'#16a34a',fontSize:11}}>{e.direction==='increases risk'?'↑':'↓'} {e.contribution.toFixed(2)}</span></span><span style={{fontSize:11, color:'#64748b'}}>{e.direction.toUpperCase()}</span></div>
            <div style={{fontSize:12,color:'#334155'}}>{e.human_explanation}</div>
            <div className="why-bar"><div className="why-fill" style={{width:`${Math.min(100,Math.abs(e.contribution)*200)}%`, background: e.direction==='increases risk'?'#dc2626':'#16a34a'}}/></div>
          </div>)}
          {(!risk?.explanations || risk.explanations.length===0) && <div style={{fontSize:12,color:'#64748b'}}>No explanation — run prediction.</div>}
        </div>
        <div className="card">
          <div style={{fontWeight:800}}>SIMILAR ACQUISITION PRECEDENTS</div>
          <div style={{fontSize:11,color:'#64748b'}}>Geography + stage + grievance + legal + compensation similarity</div>
          {prec.map((pr:any)=><div key={pr.reference_project_id} style={{border:'1px solid #e2e8f0',borderRadius:8,padding:10,marginTop:8}}>
            <div style={{display:'flex',justifyContent:'space-between'}}><b style={{fontSize:13}}>{pr.reference_project}</b><span style={{fontWeight:800,color:'#0f1e3a'}}>{(pr.similarity*100).toFixed(0)}% similarity</span></div>
            <div style={{fontSize:11,color:'#64748b'}}>{pr.district}, {pr.state} · {pr.stage} {pr.distance_km?`· ${pr.distance_km} km`:''}</div>
            <div style={{fontSize:12,marginTop:4}}>Pattern: <i>{pr.pattern}</i> {pr.historical_delay? '· historically delayed': '· on-time'}</div>
            <span style={{fontSize:10,background:'#fef3c7',padding:'2px 6px',borderRadius:999}}>DEMO SYNTHETIC</span>
          </div>)}
        </div>
      </div>
      <div className="grid" style={{gap:16}}>
        <div className="card">
          <div style={{fontWeight:800}}>Risk Drivers — Project Features</div>
          <div style={{fontSize:12,marginTop:6,display:'grid',gap:4}}>
            <div>Affected landowners: <b>{p.affected_landowners}</b></div>
            <div>Grievances: <b>{p.grievances}</b></div>
            <div>Compensation pending: <b>{p.compensation_pending_pct}%</b></div>
            <div>Consultation progress: <b>{p.consultation_progress_pct}%</b></div>
            <div>Legal disputes: <b>{p.legal_disputes}</b></div>
            <div>Document completeness: <b>{p.document_completeness_pct}%</b></div>
            <div>Land records match: <b>{p.land_records_match_pct}%</b></div>
            <div>Utility conflicts: <b>{p.utility_conflicts}</b></div>
          </div>
          <Link to="/simulator" className="btn primary" style={{marginTop:10,display:'inline-block'}}>Open Simulator →</Link>
        </div>
        <div className="card">
          <div style={{fontWeight:800}}>Grievance Intelligence</div>
          {gSum && <div style={{fontSize:12,marginTop:6}}>
            <div>Total: <b>{gSum.total}</b> · Negative: <b>{gSum.negative_pct}%</b> · High urgency: <b>{gSum.high_urgency}</b></div>
            <div>Top intent: <b>{gSum.top_intent||'—'}</b></div>
            <div style={{marginTop:6}}>{Object.entries(gSum.intent_distribution||{}).map(([k,v]:any)=><span key={k} style={{background:'#f1f5f9',padding:'2px 6px',borderRadius:999,marginRight:6,fontSize:11}}>{k}: {v as number}</span>)}</div>
          </div>}
          <Link to="/grievances" className="btn" style={{marginTop:10,display:'inline-block'}}>View grievances</Link>
        </div>
        <div className="card">
          <div style={{fontWeight:800}}>Voice Briefing — BHASHINI Adapter</div>
          <div style={{display:'flex',gap:6,marginTop:8}}>
            <button className="btn primary" onClick={()=>doVoice('en')}>English</button>
            <button className="btn" onClick={()=>doVoice('hi')}>Hindi</button>
            <button className="btn" onClick={()=>doVoice('ta')}>Tamil</button>
          </div>
          {voice && <div style={{marginTop:8,background:'#f8fafc',padding:10,borderRadius:8,fontSize:12}}>
            <div><b>Provider:</b> {voice.provider} {voice.note?`— ${voice.note}`:''}</div>
            <div style={{marginTop:4}}>{voice.text}</div>
          </div>}
        </div>
        <div className="card">
          <div style={{fontWeight:800}}>Recommended Next</div>
          <Link to="/recommendations" className="btn primary">View Recommendations</Link>
        </div>
      </div>
    </div>
  </div>
}
