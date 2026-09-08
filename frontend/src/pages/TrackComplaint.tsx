import { useState } from 'react'
import { Link } from 'react-router-dom'

export default function TrackComplaint(){
  const [cid,setCid]=useState("")
  const [data,setData]=useState<any>(null)
  const [err,setErr]=useState("")
  const doTrack=async()=>{
    setErr("")
    try{
      const r = await window.fetch(`/api/complaints/track/${cid}`)
      const j = await r.json()
      if(!j.success) throw new Error(j.error?.message || "Not found")
      setData(j.data)
    }catch(e:any){ setErr(e.message); setData(null)}
  }
  return <div style={{maxWidth:700,margin:'0 auto',padding:'20px'}}>
    <Link to="/" style={{fontSize:12,fontWeight:700,color:'#0a1930'}}>← Home</Link>
    <h1 style={{fontWeight:900,marginTop:8}}>Track Complaint — No Login Required</h1>
    <div style={{display:'flex',gap:8,marginTop:10}}>
      <input className="input" placeholder="Enter Complaint ID e.g., BD-2026-PB-004821" value={cid} onChange={e=>setCid(e.target.value.toUpperCase())} style={{flex:1}}/>
      <button className="btn primary" onClick={doTrack}>Track</button>
    </div>
    {err && <div style={{marginTop:10,color:'#dc2626',fontSize:12}}>{err}</div>}
    {data && <div className="card" style={{marginTop:12}}>
      <div style={{display:'flex',justifyContent:'space-between'}}>
        <div><div style={{fontWeight:800}}>{data.complaint_id}</div><div style={{fontSize:12,color:'#64748b'}}>{data.project_name} • {data.category} • {data.status}</div></div>
        <span className="badge HIGH">{data.status}</span>
      </div>
      <div style={{fontSize:11,color:'#64748b',marginTop:6}}>Assigned: {data.assigned_department || '—'} • Stage mapped: {data.analysis?.stage_mapped}</div>
      <div style={{marginTop:12,borderLeft:'2px solid #e2e8f0',paddingLeft:12,display:'grid',gap:8}}>
        {data.timeline.map((t:any)=> <div key={t.stage} style={{display:'flex',gap:8,alignItems:'center'}}>
          <span style={{width:18,height:18,borderRadius:999,display:'grid',placeItems:'center',fontSize:10,background: t.state==='completed' ? '#16a34a' : t.state==='current' ? '#0a1930':'#e2e8f0',color: t.state==='pending' ? '#475569':'#fff'}}>✓</span>
          <span style={{fontSize:13,fontWeight: t.state==='current'?800:400, color: t.state==='pending'?'#64748b':'#0f172a'}}>{t.stage}</span>
          <span style={{fontSize:10,background: t.state==='completed'?'#dcfce7': t.state==='current'?'#0a1930':'#f1f5f9',color: t.state==='completed'?'#166534': t.state==='current'?'#fff':'#64748b',padding:'2px 6px',borderRadius:999}}>{t.state}</span>
        </div>)}
      </div>
      <div style={{marginTop:10,fontSize:11,color:'#475569'}}>Expected next: {data.timeline.find((t:any)=>t.state==='current')?.stage || 'Resolved'} • Last update {new Date(data.updated_at).toLocaleString()}</div>
      {data.resolution_notes && <div style={{marginTop:8,background:'#f0fdf4',padding:8,borderRadius:8,fontSize:12}}>{data.resolution_notes}</div>}
      <div style={{marginTop:8,fontSize:10,color:'#64748b'}}>Never expose internal officer information — department view only</div>
    </div>}
    <div style={{marginTop:12,display:'flex',gap:8}}>
      <Link to="/complaint" className="btn">Raise New Complaint</Link>
      <Link to="/login" className="btn">Officer Login</Link>
    </div>
  </div>
}
