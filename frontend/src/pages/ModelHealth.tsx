import { useEffect, useState } from 'react'
import { api } from '../services/api'

export default function ModelHealth(){
  const [s,setS]=useState<any>(null); const [m,setM]=useState<any>(null); const [q,setQ]=useState<any>(null)
  useEffect(()=>{ api.modelStatus().then(r=>setS(r.data)); api.modelMetrics().then(r=>setM(r.data)); api.retrainingQueue().then(r=>setQ(r.data))},[])
  const train=async()=>{ const r=await api.train(); alert('Candidate '+r.data.model_version)}
  const approve=async()=>{ await api.approve(); alert('Approved')}
  if(!s) return <div>Loading...</div>
  return <div className="grid" style={{gap:16}}>
    <div className="card" style={{background:'#fef3c7',border:'1px solid #fde68a'}}>DEMO MODEL — SYNTHETIC DATA — Not production performance</div>
    <div className="grid" style={{gridTemplateColumns:'repeat(4,1fr)',gap:12}}>
      <div className="card metric"><div className="label">ROC-AUC</div><div className="value">{(m?.roc_auc||0).toFixed(2)}</div></div>
      <div className="card metric"><div className="label">PR-AUC</div><div className="value">{(m?.pr_auc||0).toFixed(2)}</div></div>
      <div className="card metric"><div className="label">F1</div><div className="value">{(m?.f1||0).toFixed(2)}</div></div>
      <div className="card metric"><div className="label">Calibration (Brier)</div><div className="value">{(m?.brier||0).toFixed(3)}</div></div>
    </div>
    <div className="card"><b>Model Status</b><pre style={{fontSize:12,marginTop:8,background:'#f8fafc',padding:10,borderRadius:8}}>{JSON.stringify(s,null,2)}</pre>
      <div style={{marginTop:8}}><b>Confusion Matrix</b> {m?.confusion && <span>{JSON.stringify(m.confusion)}</span>}</div>
      <div style={{marginTop:8}}><b>By Stage AUC</b> <pre style={{fontSize:12}}>{JSON.stringify(m?.by_stage_auc,null,2)}</pre></div>
    </div>
    <div className="card">
      <div style={{fontWeight:700}}>Retraining Queue — {q?.queued_samples} samples</div>
      <div style={{fontSize:12,color:'#64748b'}}>PIPELINE: Recommendation → Action → Outcome → Validated Label → Queue → Training → Evaluation → Approval → Deployment</div>
      <div style={{display:'flex',gap:8,marginTop:10}}><button className="btn primary" onClick={train}>Train candidate model</button><button className="btn" onClick={approve}>Approve</button></div>
      <div style={{fontSize:11,marginTop:8}}>Model status: TRAINING → VALIDATION → PENDING_APPROVAL → APPROVED → DEPLOYED</div>
    </div>
  </div>
}
