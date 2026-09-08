import { BrowserRouter, Routes, Route, Link, useLocation, useNavigate, Outlet, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import RiskIntelligence from './pages/RiskIntelligence'
import GIS from './pages/GIS'
import Grievances from './pages/Grievances'
import Simulator from './pages/Simulator'
import Recommendations from './pages/Recommendations'
import Outcomes from './pages/Outcomes'
import Alerts from './pages/Alerts'
import ModelHealth from './pages/ModelHealth'
import Administration from './pages/Administration'
import Profile from './pages/Profile'
import Login from './pages/Login'
import Landing from './pages/Landing'
import Complaint from './pages/Complaint'
import TrackComplaint from './pages/TrackComplaint'
import VoiceAssistant from './components/VoiceAssistant'
import { LayoutDashboard, FolderKanban, AlertTriangle, Map, MessageSquare, FlaskConical, Lightbulb, ClipboardCheck, Bell, Shield, Activity, User as UserIcon, LogOut } from 'lucide-react'

function OfficerLayout(){
  const loc=useLocation(); const nav=useNavigate()
  const user=JSON.parse(localStorage.getItem('user')||'null')
  const isActive=(p:string)=>{
    if(p==='/dashboard') return loc.pathname==='/' || loc.pathname==='/dashboard'
    if(p==='/projects') return loc.pathname.startsWith('/projects')
    return loc.pathname===p
  }
  const NavItem=({to,icon,label}:{to:string,icon:any,label:string})=>(
    <Link to={to} className={isActive(to)?'active':''}>{icon} {label}</Link>
  )
  return <div>
    <div className="topbar">
      <Link to="/dashboard" className="brand" style={{color:'#fff'}}><span style={{width:30,height:30,background:'#ff6b35',display:'grid',placeItems:'center',borderRadius:8,fontSize:13}}>◉</span><div>BHOOMI-DRISHTI <small>AI Decision Intelligence — DEMO DATA — SYNTHETIC / CALIBRATED</small></div></Link>
      <div style={{display:'flex',gap:10,alignItems:'center'}}>
        <Link to="/alerts" style={{position:'relative',background:'#1e3a5f',padding:'6px 10px',borderRadius:8,color:'#fff',fontSize:12,display:'flex',gap:6,alignItems:'center'}}><Bell size={14}/> Alerts</Link>
        <span className="demo-badge">DEMO DATA</span>
        <Link to="/profile" style={{fontSize:11,opacity:0.9,background:'#1e3a5f',padding:'6px 10px',borderRadius:8,color:'#fff'}}>{user?.username} · {user?.role}</Link>
        <button className="btn" style={{background:'#fff',color:'#0a1930',padding:'6px 10px'}} onClick={()=>{localStorage.clear(); nav('/login')}}><LogOut size={14}/> Logout</button>
      </div>
    </div>
    <div className="layout">
      <nav className="sidenav">
        <div style={{fontSize:10,letterSpacing:0.6,opacity:0.6,marginBottom:6}}>INTELLIGENCE</div>
        <NavItem to="/dashboard" icon={<LayoutDashboard size={16}/>} label="Dashboard"/>
        <NavItem to="/projects" icon={<FolderKanban size={16}/>} label="Projects"/>
        <NavItem to="/risk-intelligence" icon={<AlertTriangle size={16}/>} label="Risk Intelligence"/>
        <NavItem to="/gis" icon={<Map size={16}/>} label="GIS Intelligence"/>
        <NavItem to="/grievances" icon={<MessageSquare size={16}/>} label="Grievances"/>
        <NavItem to="/simulator" icon={<FlaskConical size={16}/>} label="What-If Simulator"/>
        <NavItem to="/recommendations" icon={<Lightbulb size={16}/>} label="Recommendations"/>
        <NavItem to="/outcomes" icon={<ClipboardCheck size={16}/>} label="Outcomes"/>
        <NavItem to="/alerts" icon={<Bell size={16}/>} label="Alerts"/>
        <NavItem to="/model-health" icon={<Activity size={16}/>} label="Model Health"/>
        <NavItem to="/administration" icon={<Shield size={16}/>} label="Administration"/>
        <div style={{marginTop:10,fontSize:10,letterSpacing:0.6,opacity:0.6}}>VOICE & ACCOUNT</div>
        <NavItem to="/profile" icon={<UserIcon size={16}/>} label="Profile"/>
        <div style={{marginTop:8,background:'#ff6b35',borderRadius:9,padding:'8px 10px'}}>
          <div style={{fontSize:11,fontWeight:900,color:'#fff',display:'flex',gap:6,alignItems:'center'}}>🎙️ Voice Intelligence</div>
          <div style={{fontSize:10,color:'#fff',opacity:0.9,marginTop:2}}>Ask: “Show critical projects”</div>
        </div>
        <div style={{marginTop:10,fontSize:10,letterSpacing:0.6,opacity:0.6}}>PUBLIC</div>
        <Link to="/complaint" style={{display:'flex',gap:9,padding:'9px 11px',fontSize:11,background:'#ff6b35',color:'#fff',borderRadius:9,fontWeight:800,marginTop:4,justifyContent:'center'}}>Raise Complaint</Link>
        <Link to="/track-complaint" style={{display:'flex',gap:9,padding:'9px 11px',fontSize:11,background:'#1e3a5f',color:'#fff',borderRadius:9,marginTop:4,justifyContent:'center'}}>Track Complaint</Link>
      </nav>
      <div className="content">
        <Outlet/>
        <VoiceAssistant/>
        <div style={{marginTop:20,fontSize:10,color:'#64748b',textAlign:'center',borderTop:'1px solid #e2e8f0',paddingTop:10}}>From reactive monitoring to proactive land-governance intelligence. — AI-assisted decision support · predicted risk · human-in-the-loop · prototype</div>
      </div>
    </div>
  </div>
}

function RequireAuth({children}:{children?:any}){
  const token=localStorage.getItem('token')
  if(!token) return <Navigate to="/login" replace/>
  return children ? children : <Outlet/>
}

export default function App(){
  return <BrowserRouter>
    <Routes>
      {/* Public */}
      <Route path="/" element={<Landing/>}/>
      <Route path="/landing" element={<Landing/>}/>
      <Route path="/complaint" element={<Complaint/>}/>
      <Route path="/track-complaint" element={<TrackComplaint/>}/>
      <Route path="/login" element={<Login/>}/>

      {/* Protected officer shell */}
      <Route element={<RequireAuth><OfficerLayout/></RequireAuth>}>
        <Route path="/dashboard" element={<Dashboard/>}/>
        <Route path="/projects" element={<Projects/>}/>
        <Route path="/projects/:id" element={<ProjectDetail/>}/>
        <Route path="/risk-intelligence" element={<RiskIntelligence/>}/>
        <Route path="/gis" element={<GIS/>}/>
        <Route path="/grievances" element={<Grievances/>}/>
        <Route path="/simulator" element={<Simulator/>}/>
        <Route path="/recommendations" element={<Recommendations/>}/>
        <Route path="/outcomes" element={<Outcomes/>}/>
        <Route path="/alerts" element={<Alerts/>}/>
        <Route path="/model-health" element={<ModelHealth/>}/>
        <Route path="/administration" element={<Administration/>}/>
        <Route path="/profile" element={<Profile/>}/>
        {/* Legacy aliases */}
        <Route path="/model" element={<Navigate to="/model-health" replace/>}/>
        <Route path="/admin" element={<Navigate to="/administration" replace/>}/>
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace/>}/>
    </Routes>
  </BrowserRouter>
}
