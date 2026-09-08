import { useState } from 'react'
import { Link } from 'react-router-dom'

const categories = ["Compensation","Land Record","Ownership","Survey","Legal Issue","Rehabilitation & Resettlement","Possession","Notification","Other"]
const states = ["Punjab","Tamil Nadu","Gujarat","Bihar","Karnataka","Maharashtra","Rajasthan","Uttar Pradesh","Madhya Pradesh","West Bengal"]

export default function Complaint(){
  const [step,setStep]=useState(1)
  const [form,setForm]=useState<any>({project_name:"Punjab Infrastructure Corridor — Demo Package 14",state:"Punjab",district:"Amritsar",village:"Demo Village",category:"Compensation",details:"Compensation for my acquired land has not been received despite the award being issued.",latitude:31.63,longitude:74.87,contact_preference:"anonymous",name:"",mobile:"",email:""})
  const [cid,setCid]=useState<string>("")
  const [loading,setLoading]=useState(false)
  const [analysis,setAnalysis]=useState<any>(null)
  const set = (k:string,v:any)=> setForm((s:any)=>({...s,[k]:v}))
  const submit=async()=>{
    setLoading(true)
    try{
      const res = await fetch("/api/complaints/public", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(form)})
      const j = await res.json()
      if(!j.success) throw new Error(j.error?.message || "Failed")
      setCid(j.data.complaint_id)
      setAnalysis(j.data.analysis)
      setStep(8)
    }catch(e:any){ alert(e.message)} finally{ setLoading(false)}
  }
  const useLocation=()=>{
    if(navigator.geolocation){
      navigator.geolocation.getCurrentPosition(p=>{ set("latitude", +p.coords.latitude.toFixed(4)); set("longitude", +p.coords.longitude.toFixed(4))})
    }
  }
  return <div style={{maxWidth:900,margin:'0 auto',padding:'20px'}}>
    <Link to="/" style={{fontSize:12,color:'#0a1930',fontWeight:700}}>← Back to Home</Link>
    <h1 style={{fontSize:22,fontWeight:900,marginTop:8}}>Raise a Complaint — No Login Required</h1>
    <p style={{fontSize:12,color:'#64748b'}}>Secure submission • Track using Complaint ID • Your complaint helps identify emerging issues</p>
    <div style={{display:'flex',gap:6,marginTop:10,flexWrap:'wrap'}}>
      {[1,2,3,4,5,6,7].map(n=> <div key={n} style={{width:32,height:32,borderRadius:999,display:'grid',placeItems:'center',fontSize:12,fontWeight:800,background: step>=n ? '#0a1930':'#e2e8f0',color: step>=n?'#fff':'#475569'}}>{n}</div>)}
      <span style={{fontSize:11,color:'#64748b',alignSelf:'center',marginLeft:8}}>Project → Category → Details → Location → Documents → Contact → Submit</span>
    </div>

    {step===1 && <div className="card" style={{marginTop:12}}>
      <h3 style={{fontWeight:800}}>1. Project Identification</h3>
      <div style={{display:'grid',gap:10,marginTop:10}}>
        <input className="input" placeholder="Project / Highway / Infrastructure Name" value={form.project_name} onChange={e=>set("project_name",e.target.value)}/>
        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10}}>
          <select className="select" value={form.state} onChange={e=>set("state",e.target.value)}>{states.map(s=> <option key={s}>{s}</option>)}</select>
          <input className="input" placeholder="District" value={form.district} onChange={e=>set("district",e.target.value)}/>
        </div>
        <input className="input" placeholder="Village" value={form.village} onChange={e=>set("village",e.target.value)}/>
        <div style={{display:'flex',justifyContent:'space-between'}}>
          <span style={{fontSize:11,color:'#64748b'}}>Allow search/autocomplete — demo uses text match</span>
          <button className="btn primary" onClick={()=>setStep(2)}>Next</button>
        </div>
      </div>
    </div>}

    {step===2 && <div className="card" style={{marginTop:12}}>
      <h3 style={{fontWeight:800}}>2. Complaint Category</h3>
      <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:10,marginTop:10}}>
        {categories.map(c=> <button key={c} onClick={()=>set("category",c)} style={{padding:12,borderRadius:10,border: form.category===c? '2px solid #0a1930':'1px solid #e2e8f0',background: form.category===c? '#f1f5f9':'#fff',fontSize:12,fontWeight:700}}>{c}</button>)}
      </div>
      <div style={{display:'flex',justifyContent:'space-between',marginTop:10}}>
        <button className="btn" onClick={()=>setStep(1)}>Back</button>
        <button className="btn primary" onClick={()=>setStep(3)}>Next</button>
      </div>
    </div>}

    {step===3 && <div className="card" style={{marginTop:12}}>
      <h3 style={{fontWeight:800}}>3. Complaint Details</h3>
      <textarea className="textarea" rows={5} value={form.details} onChange={e=>set("details",e.target.value)} placeholder="Describe your issue — e.g., Compensation for my acquired land has not been received despite the award being issued."/>
      <div style={{display:'flex',justifyContent:'space-between',marginTop:10}}>
        <button className="btn" onClick={()=>setStep(2)}>Back</button>
        <button className="btn primary" onClick={()=>setStep(4)}>Next</button>
      </div>
    </div>}

    {step===4 && <div className="card" style={{marginTop:12}}>
      <h3 style={{fontWeight:800}}>4. Location — PostGIS</h3>
      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10}}>
        <input className="input" type="number" step="0.0001" value={form.latitude} onChange={e=>set("latitude",parseFloat(e.target.value))} placeholder="Latitude"/>
        <input className="input" type="number" step="0.0001" value={form.longitude} onChange={e=>set("longitude",parseFloat(e.target.value))} placeholder="Longitude"/>
      </div>
      <div style={{display:'flex',gap:8,marginTop:8}}>
        <button className="btn" onClick={useLocation}>Use current location</button>
        <span style={{fontSize:11,color:'#64748b',alignSelf:'center'}}>Also: search village/district or select on map (map integration ready)</span>
      </div>
      <div style={{display:'flex',justifyContent:'space-between',marginTop:10}}>
        <button className="btn" onClick={()=>setStep(3)}>Back</button>
        <button className="btn primary" onClick={()=>setStep(5)}>Next</button>
      </div>
    </div>}

    {step===5 && <div className="card" style={{marginTop:12}}>
      <h3 style={{fontWeight:800}}>5. Supporting Documents (Optional)</h3>
      <div style={{border:'1px dashed #cbd5e1',borderRadius:10,padding:20,textAlign:'center',color:'#64748b',fontSize:12}}>
        Drag & drop or <span style={{color:'#0a1930',fontWeight:700}}>choose files</span><br/>Notice • Compensation document • Land record • Court document • Photograph • Other<br/>
        <input type="file" style={{marginTop:8}} onChange={()=>{}}/>
        <div style={{fontSize:10,marginTop:6}}>Validated file type and size (demo: no upload required)</div>
      </div>
      <div style={{display:'flex',justifyContent:'space-between',marginTop:10}}>
        <button className="btn" onClick={()=>setStep(4)}>Back</button>
        <button className="btn primary" onClick={()=>setStep(6)}>Next</button>
      </div>
    </div>}

    {step===6 && <div className="card" style={{marginTop:12}}>
      <h3 style={{fontWeight:800}}>6. Contact Preference</h3>
      <div style={{display:'flex',gap:10}}>
        <button className="btn" style={{flex:1,background: form.contact_preference==='anonymous'?'#0a1930':'#fff',color: form.contact_preference==='anonymous'?'#fff':'#0f172a'}} onClick={()=>set("contact_preference","anonymous")}>Submit anonymously</button>
        <button className="btn" style={{flex:1,background: form.contact_preference==='with_contact'?'#0a1930':'#fff',color: form.contact_preference==='with_contact'?'#fff':'#0f172a'}} onClick={()=>set("contact_preference","with_contact")}>Submit with contact details</button>
      </div>
      {form.contact_preference==='with_contact' && <div style={{display:'grid',gap:8,marginTop:10}}>
        <input className="input" placeholder="Name" value={form.name} onChange={e=>set("name",e.target.value)}/>
        <input className="input" placeholder="Mobile number" value={form.mobile} onChange={e=>set("mobile",e.target.value)}/>
        <input className="input" placeholder="Email" value={form.email} onChange={e=>set("email",e.target.value)}/>
        <div style={{fontSize:10,color:'#64748b'}}>Do not request Aadhaar for ordinary complaints — minimal data</div>
      </div>}
      <div style={{display:'flex',justifyContent:'space-between',marginTop:10}}>
        <button className="btn" onClick={()=>setStep(5)}>Back</button>
        <button className="btn primary" onClick={()=>setStep(7)}>Next</button>
      </div>
    </div>}

    {step===7 && <div className="card" style={{marginTop:12}}>
      <h3 style={{fontWeight:800}}>7. Submit</h3>
      <div style={{background:'#f8fafc',padding:10,borderRadius:8,fontSize:12}}>
        <div><b>Project:</b> {form.project_name} • {form.state}/{form.district}/{form.village}</div>
        <div><b>Category:</b> {form.category} • <b>Stage mapped:</b> {form.category}</div>
        <div><b>Details:</b> {form.details.slice(0,120)}...</div>
        <div><b>Location:</b> {form.latitude}, {form.longitude}</div>
        <div><b>Contact:</b> {form.contact_preference}</div>
      </div>
      <button className="btn primary" style={{marginTop:10,width:'100%',padding:12}} onClick={submit} disabled={loading}>{loading? 'Submitting...':'Submit Complaint → Generate Complaint ID'}</button>
      <div style={{display:'flex',justifyContent:'space-between',marginTop:8}}>
        <button className="btn" onClick={()=>setStep(6)}>Back</button>
        <Link to="/track-complaint" style={{fontSize:12,color:'#0a1930',fontWeight:700,alignSelf:'center'}}>Already have ID? Track →</Link>
      </div>
    </div>}

    {step===8 && <div className="card" style={{marginTop:12,border:'2px solid #16a34a'}}>
      <h3 style={{fontWeight:900,color:'#16a34a'}}>✓ Complaint Submitted</h3>
      <div style={{marginTop:8,background:'#f0fdf4',padding:12,borderRadius:10,textAlign:'center'}}>
        <div style={{fontSize:11,color:'#166534',fontWeight:700}}>Complaint ID</div>
        <div style={{fontSize:22,fontWeight:900,letterSpacing:1}}>{cid}</div>
        <div style={{fontSize:11,color:'#166534'}}>Save this ID to track your complaint</div>
      </div>
      {analysis && <div style={{marginTop:10,display:'flex',gap:6,flexWrap:'wrap'}}>
        <span className="badge HIGH">{analysis.sentiment}</span>
        <span className="badge MEDIUM">{analysis.intent}</span>
        <span style={{fontSize:11,background:'#e0f2fe',padding:'4px 8px',borderRadius:999}}>{analysis.urgency} urgency</span>
        <span style={{fontSize:11,background:'#fef3c7',padding:'4px 8px',borderRadius:999}}>Stage: {analysis.stage_mapped || '—'}</span>
      </div>}
      <div style={{marginTop:10,fontSize:11,color:'#475569',background:'#fffbeb',padding:8,borderRadius:8}}>Your complaint is analyzed to help identify patterns and prioritize administrative attention. It feeds: NLP → Project Mapping → Risk Signal → Officer Dashboard.</div>
      <div style={{display:'flex',gap:8,marginTop:10}}>
        <Link to="/track-complaint" className="btn primary">Track Complaint</Link>
        <Link to="/" className="btn">Back to Home</Link>
      </div>
    </div>}
  </div>
}
