import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { Link } from 'react-router-dom'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'

function MapFix(){
  const map=useMap()
  useEffect(()=>{
    // Fix Leaflet stuck tiles when map was hidden (voice overlay, tab switch)
    const id=setTimeout(()=> map.invalidateSize(), 220)
    const onResize=()=> map.invalidateSize()
    window.addEventListener('resize', onResize)
    // Also re-invalidate after data loads / voice navigation
    const t2=setTimeout(()=> map.invalidateSize(), 800)
    return ()=>{ clearTimeout(id); clearTimeout(t2); window.removeEventListener('resize', onResize)}
  },[map])
  return null
}

export default function GIS(){
  const [heat,setHeat]=useState<any[]>([])
  const [filterRisk,setFilterRisk]=useState('ALL')
  const [filterStage,setFilterStage]=useState('ALL')
  useEffect(()=>{ api.heatmap().then(r=>setHeat(r.data))},[])
  const filtered=heat.filter(h=>{
    if(filterRisk!=='ALL' && h.risk_level!==filterRisk) return false
    if(filterStage!=='ALL' && h.stage!==filterStage) return false
    return true
  })
  return <div className="grid" style={{gap:16}}>
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
      <h2 style={{fontWeight:900}}>GIS Intelligence — Risk & Grievance Hotspots</h2>
      <span style={{fontSize:11,background:'#fef3c7',padding:'4px 8px',borderRadius:999}}>PostGIS • Demo synthetic corridors</span>
    </div>
    <div className="card" style={{display:'flex',gap:8,flexWrap:'wrap'}}>
      <select className="select" value={filterRisk} onChange={e=>setFilterRisk(e.target.value)} style={{maxWidth:160}}><option>ALL</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option><option>CRITICAL</option></select>
      <select className="select" value={filterStage} onChange={e=>setFilterStage(e.target.value)} style={{maxWidth:160}}><option>ALL</option><option>Notification</option><option>SIA</option><option>Consent</option><option>Award</option><option>Compensation</option><option>Possession</option></select>
      <span style={{fontSize:11,color:'#64748b',alignSelf:'center'}}>{filtered.length} projects • Click marker → details</span>
    </div>
    <div className="card" style={{padding:0,overflow:'hidden'}}>
      <MapContainer center={[22,78]} zoom={5} style={{height:520,width:'100%'}}>
        <MapFix/>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
        {filtered.slice(0,400).map((h:any)=><CircleMarker key={h.project_id} center={[h.lat,h.lon]} radius={h.risk_level==='HIGH'||h.risk_level==='CRITICAL'?8:6} pathOptions={{color: h.risk_level.includes('HIGH')||h.risk_level==='CRITICAL'?'#dc2626':h.risk_level==='MEDIUM'?'#d97706':'#16a34a', fillOpacity:0.85}}>
          <Popup>
            <b>{h.name}</b><br/>{h.district}, {h.state}<br/>Risk {h.risk_level} {(h.probability*100).toFixed(0)}% • {h.stage}<br/>
            <Link to={`/projects/${h.project_id}`}>Open Intelligence</Link>
          </Popup>
        </CircleMarker>)}
      </MapContainer>
    </div>
    <div className="grid" style={{gridTemplateColumns:'repeat(3,1fr)',gap:12}}>
      <div className="card"><div style={{fontWeight:800,fontSize:12}}>Layers</div><div style={{fontSize:11,color:'#64748b',marginTop:4}}>Project Corridors • District Boundaries • Risk Hotspots • Grievance Hotspots • Critical Areas</div></div>
      <div className="card"><div style={{fontWeight:800,fontSize:12}}>Risk Legend</div><div style={{display:'flex',gap:6,marginTop:6}}><span className="badge LOW">LOW</span><span className="badge MEDIUM">MEDIUM</span><span className="badge HIGH">HIGH</span><span className="badge CRITICAL" style={{background:'#7f1d1d',color:'#fff'}}>CRITICAL</span></div></div>
      <div className="card"><div style={{fontWeight:800,fontSize:12}}>Interaction</div><div style={{fontSize:11,color:'#64748b',marginTop:4}}>Click district → overview • Click project → detail • Click hotspot → grievance count & primary issue</div></div>
    </div>
  </div>
}
