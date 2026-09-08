import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import { Shield, Brain, Map, Activity } from 'lucide-react'

export default function Login(){
  const [u,setU]=useState('admin'); const [p,setP]=useState('demo123'); const [err,setErr]=useState('')
  const submit=async()=>{
    try{ const r=await api.login(u,p); localStorage.setItem('token',r.data.access_token); localStorage.setItem('user', JSON.stringify(r.data.user)); window.location.href='/dashboard'; }catch(e:any){ setErr(e.message) }
  }
  return <div className="login-wrap">
    <div className="login-left">
      <div style={{display:'flex',alignItems:'center',gap:10,fontWeight:900,letterSpacing:0.6}}><span style={{width:36,height:36,background:'#ff6b35',display:'grid',placeItems:'center',borderRadius:10}}>◉</span> BHOOMI-DRISHTI</div>
      <div style={{fontSize:11,letterSpacing:1,opacity:0.7,marginTop:4}}>NATIONAL INFRASTRUCTURE INTELLIGENCE</div>
      <h1 style={{fontSize:34,fontWeight:950,marginTop:18,lineHeight:1.1}}>Predict.<br/>Explain.<br/>Prevent.</h1>
      <p style={{marginTop:12,color:'#cbd5e1',fontSize:13,lineHeight:1.6}}>AI-powered early warning for India's infrastructure projects.</p>
      <div style={{marginTop:16,display:'grid',gap:8,fontSize:12,opacity:0.9}}>
        <span style={{display:'flex',gap:8}}><Brain size={14}/> Predictive Risk</span>
        <span style={{display:'flex',gap:8}}><Shield size={14}/> Explainable AI</span>
        <span style={{display:'flex',gap:8}}><Map size={14}/> GIS Intelligence</span>
        <span style={{display:'flex',gap:8}}><Activity size={14}/> Action Recommendations</span>
      </div>
      <div style={{marginTop:18,padding:12,background:'rgba(255,255,255,0.06)',border:'1px solid rgba(255,255,255,0.12)',borderRadius:12,fontSize:11}}>
        Existing systems tell us what is happening.<br/><b>BHOOMI-DRISHTI predicts what is likely to happen next.</b>
      </div>
    </div>
    <div className="login-right">
      <div className="login-card">
        <h2 style={{fontWeight:900}}>Officer Login</h2><p style={{fontSize:12,color:'#64748b',marginTop:4}}>Secure access for District Collector, LAO, Revenue, Legal, PM</p>
        <div style={{marginTop:14,display:'grid',gap:10}}>
          <input className="input" placeholder="Official Email / Username" value={u} onChange={e=>setU(e.target.value)}/>
          <input className="input" type="password" placeholder="Password" value={p} onChange={e=>setP(e.target.value)}/>
          {err && <div style={{color:'#dc2626',fontSize:12}}>{err}</div>}
          <button className="btn primary" onClick={submit} style={{padding:11}}>Sign In</button>
          <a style={{fontSize:11,color:'#64748b',textAlign:'center'}}>Forgot Password?</a>
        </div>
        <div style={{marginTop:14,borderTop:'1px solid #e2e8f0',paddingTop:12}}>
          <div style={{background:'#ff6b35',color:'#fff',textAlign:'center',padding:'7px',borderRadius:8,fontSize:10,fontWeight:900,letterSpacing:0.6}}>🚨 RAISE A COMPLAINT WITHOUT LOGIN</div>
          <p style={{fontSize:12,fontWeight:700,marginTop:8,textAlign:'center'}}>Having an issue with land acquisition?</p>
          <Link to="/complaint" className="btn saffron" style={{display:'block',textAlign:'center',marginTop:8,padding:11}}>Raise a Complaint</Link>
          <div style={{fontSize:10,color:'#64748b',textAlign:'center',marginTop:6}}>No login required • Secure submission • Track using Complaint ID</div>
          <div style={{fontSize:10,color:'#92400e',background:'#fef3c7',padding:6,borderRadius:8,marginTop:10,textAlign:'center'}}>Demo: admin/demo123 · officer/demo123 · reviewer/demo123</div>
        </div>
      </div>
    </div>
  </div>
}
