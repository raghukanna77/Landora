import { Link } from 'react-router-dom'
import { Shield, Map, Brain, AlertTriangle, FileText, Activity, ArrowRight, Navigation, Users, Landmark } from 'lucide-react'

export default function Landing(){
  return <div style={{background:'#f8fafc'}}>
    {/* Header */}
    <header style={{position:'sticky',top:0,zIndex:30,background:'#0a1930',borderBottom:'1px solid #1e3a5f'}}>
      <div style={{maxWidth:1200,margin:'0 auto',padding:'12px 20px',display:'flex',alignItems:'center',justifyContent:'space-between'}}>
        <div style={{display:'flex',alignItems:'center',gap:10,color:'#fff',fontWeight:900,letterSpacing:0.6}}> <span style={{width:32,height:32,background:'#ff6b35',borderRadius:8,display:'grid',placeItems:'center',fontSize:14}}>◉</span> BHOOMI-DRISHTI <span style={{fontWeight:400,fontSize:11,opacity:0.7,marginLeft:8,borderLeft:'1px solid #334155',paddingLeft:8}}>NATIONAL INFRASTRUCTURE INTELLIGENCE</span></div>
        <nav style={{display:'flex',gap:18,fontSize:13,color:'#cbd5e1'}}>
          <a href="#overview" style={{color:'#cbd5e1'}}>Overview</a><a href="#intelligence">Intelligence</a><a href="#projects">Projects</a><Link to="/grievances">Grievances</Link><a href="#about">About</a>
        </nav>
        <div style={{display:'flex',gap:8}}>
          <Link to="/complaint" className="btn" style={{background:'#fff',color:'#0a1930',borderRadius:999,padding:'8px 16px',fontWeight:800,border:'none'}}>Raise a Complaint</Link>
          <Link to="/login" style={{background:'#ff6b35',color:'#fff',padding:'8px 18px',borderRadius:999,fontWeight:800,fontSize:13}}>Officer Login</Link>
        </div>
      </div>
      <div style={{textAlign:'center',background:'#fef3c7',color:'#92400e',fontSize:11,padding:'4px',fontWeight:700}}>DEMO DATA — SYNTHETIC / CALIBRATED — Prototype • Not official government data</div>
    </header>

    {/* Hero */}
    <section id="overview" style={{background:'linear-gradient(180deg,#0a1930 0%, #0f264a 60%, #f8fafc 100%)',color:'#fff',padding:'48px 20px 40px'}}>
      <div style={{maxWidth:1200,margin:'0 auto',display:'grid',gridTemplateColumns:'1.1fr 0.9fr',gap:24}}>
        <div>
          <div style={{display:'inline-flex',gap:6,background:'rgba(255,255,255,0.08)',border:'1px solid rgba(255,255,255,0.15)',padding:'6px 10px',borderRadius:999,fontSize:11,letterSpacing:0.6}}>GOVTECH • AI DECISION SUPPORT • HUMAN-IN-THE-LOOP</div>
          <h1 style={{fontSize:46,lineHeight:1.05,fontWeight:950,marginTop:14}}>See the delay<br/>before it happens.</h1>
          <p style={{marginTop:12,color:'#cbd5e1',fontSize:15,lineHeight:1.6}}>AI-powered land acquisition intelligence for faster, transparent and proactive infrastructure delivery.</p>
          <p style={{marginTop:8,color:'#94a3b8',fontSize:12}}>Predictive intelligence layer alongside BhoomiRashi • DILRMP • PM GatiShakti • PARIVESH • PRAGATI</p>
          <div style={{marginTop:18,display:'flex',gap:10,flexWrap:'wrap'}}>
            <Link to="/login" style={{background:'#ff6b35',color:'#fff',padding:'12px 18px',borderRadius:10,fontWeight:800,display:'inline-flex',gap:8,alignItems:'center'}}>Explore Intelligence <ArrowRight size={16}/></Link>
            <Link to="/complaint" className="btn" style={{background:'#fff',color:'#0a1930',padding:'12px 18px',borderRadius:10,fontWeight:800}}>Raise a Complaint</Link>
            <a href="#intelligence" style={{border:'1px solid rgba(255,255,255,0.3)',color:'#fff',padding:'12px 18px',borderRadius:10,fontWeight:700}}>How it works</a>
          </div>
          <div style={{marginTop:18,display:'flex',gap:14,fontSize:11,color:'#94a3b8'}}>
            <span>✓ Predictive Risk</span><span>✓ Explainable AI</span><span>✓ GIS Intelligence</span><span>✓ Action Recommendations</span>
          </div>
        </div>
        <div style={{background:'#ffffff',borderRadius:16,padding:16,color:'#0f172a',border:'1px solid #e2e8f0',boxShadow:'0 20px 50px rgba(0,0,0,0.25)'}}>
          <div style={{fontSize:11,fontWeight:800,letterSpacing:0.6,color:'#64748b'}}>INTELLIGENCE PREVIEW — LIVE SIGNALS</div>
          <div style={{marginTop:10,background:'#0a1930',color:'#fff',borderRadius:12,padding:12}}>
            <div style={{fontSize:11,opacity:0.7}}>NH-48 Expansion Package A • Amritsar</div>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginTop:6}}><span style={{fontSize:28,fontWeight:900}}>82%</span><span style={{background:'#dc2626',padding:'4px 8px',borderRadius:999,fontSize:11,fontWeight:800}}>CRITICAL</span></div>
            <div style={{fontSize:11,opacity:0.8,marginTop:4}}>Primary: compensation backlog + grievance spike</div>
          </div>
          <div style={{marginTop:10,display:'grid',gridTemplateColumns:'1fr 1fr',gap:8}}>
            <div style={{background:'#f8fafc',border:'1px solid #e2e8f0',borderRadius:10,padding:10}}><div style={{fontSize:10,color:'#64748b',fontWeight:700}}>PROJECT</div><div style={{fontWeight:800}}>603 Total</div><div style={{fontSize:10,color:'#64748b'}}>Across 10 states</div></div>
            <div style={{background:'#fff7ed',border:'1px solid #fed7aa',borderRadius:10,padding:10}}><div style={{fontSize:10,color:'#9a3412',fontWeight:700}}>HIGH RISK</div><div style={{fontWeight:800,color:'#c2410c'}}>295</div><div style={{fontSize:10,color:'#9a3412'}}>Early warning</div></div>
            <div style={{background:'#fef2f2',border:'1px solid #fecaca',borderRadius:10,padding:10}}><div style={{fontSize:10,color:'#991b1b',fontWeight:700}}>GRIEVANCE HOTSPOT</div><div style={{fontWeight:800}}>Village B</div><div style={{fontSize:10,color:'#991b1b'}}>34% spike 14d</div></div>
            <div style={{background:'#f0fdf4',border:'1px solid #bbf7d0',borderRadius:10,padding:10}}><div style={{fontSize:10,color:'#166534',fontWeight:700}}>GIS</div><div style={{fontWeight:800}}>Live Map</div><div style={{fontSize:10,color:'#166534'}}>Risk + grievance</div></div>
          </div>
          <div style={{marginTop:10,display:'flex',gap:6,fontSize:10,color:'#64748b',alignItems:'center'}}><Navigation size={12}/> India corridor • State • District • Village • Parcel</div>
        </div>
      </div>
    </section>

    {/* Feature strip */}
    <section id="intelligence" style={{maxWidth:1200,margin:'0 auto',padding:'18px 20px',display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12}}>
      {[
        {icon: Brain, title:'Predictive Risk', desc:'Stage-wise LightGBM delay prediction with calibration'},
        {icon: Shield, title:'Explainable AI', desc:'SHAP TreeExplainer — why is this at risk?'},
        {icon: Map, title:'GIS Intelligence', desc:'PostGIS risk & grievance hotspots'},
        {icon: Activity, title:'Action Recommendations', desc:'Ranked preventive actions + simulator'},
      ].map(f=> <div key={f.title} className="card" style={{display:'flex',gap:10,alignItems:'flex-start'}}><f.icon size={20} color="#ff6b35"/><div><div style={{fontWeight:800,fontSize:13}}>{f.title}</div><div style={{fontSize:12,color:'#64748b',marginTop:2}}>{f.desc}</div></div></div>)}
    </section>

    {/* Loop */}
    <section style={{maxWidth:1200,margin:'0 auto',padding:'12px 20px'}}>
      <div className="card" style={{background:'#0a1930',color:'#fff',display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:10}}>
        <div style={{fontWeight:900,letterSpacing:0.4}}>PREDICT → EXPLAIN → SIMULATE → RECOMMEND → ACT → TRACK → LEARN</div>
        <div style={{fontSize:11,opacity:0.8}}>Existing systems tell us what is happening. BHOOMI-DRISHTI predicts what is likely to happen next.</div>
      </div>
    </section>

    {/* About */}
    <section id="about" style={{maxWidth:1200,margin:'0 auto',padding:'18px 20px',display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:12}}>
      <div className="card"><div style={{fontWeight:800,display:'flex',gap:8}}><Landmark size={16}/> Citizen Trust</div><p style={{fontSize:12,color:'#475569',marginTop:6}}>Raise a complaint without login. Track with Complaint ID. Your complaint is analyzed to prioritize administrative attention — not auto-decided by AI.</p></div>
      <div className="card"><div style={{fontWeight:800,display:'flex',gap:8}}><Users size={16}/> Officer Experience</div><p style={{fontSize:12,color:'#475569',marginTop:6}}>Within 10 seconds: WHAT is at risk? WHERE? WHY? WHAT should I do? DID it work?</p></div>
      <div className="card"><div style={{fontWeight:800,display:'flex',gap:8}}><FileText size={16}/> Decision Support</div><p style={{fontSize:12,color:'#475569',marginTop:6}}>AI is advisory. Human officials remain responsible. All predictions show confidence, model version, timestamp, drivers.</p></div>
    </section>

    <footer style={{textAlign:'center',padding:'18px',fontSize:11,color:'#64748b'}}>From reactive monitoring to proactive land-governance intelligence. • Built for SIH • Demo only</footer>
  </div>
}
