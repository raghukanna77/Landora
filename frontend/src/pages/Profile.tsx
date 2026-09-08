export default function Profile(){
  const user = JSON.parse(localStorage.getItem('user')||'{}')
  return <div className="grid" style={{gap:16,maxWidth:700}}>
    <h2 style={{fontWeight:900}}>Profile — RBAC & Jurisdiction</h2>
    <div className="card">
      <div style={{fontWeight:800}}>{user.username || '—'} <span style={{fontSize:11,background:'#0a1930',color:'#fff',padding:'3px 8px',borderRadius:999}}>{user.role}</span></div>
      <div style={{fontSize:12,color:'#64748b',marginTop:6}}>State: {user.state || 'All (National)'} • District: {user.district || 'All'}</div>
      <div style={{fontSize:11,color:'#64748b',marginTop:6}}>Jurisdiction filtering enforced on backend. Voice queries respect same RBAC.</div>
      <div style={{marginTop:10,display:'flex',gap:8}}>
        <button className="btn" onClick={()=>{localStorage.clear(); window.location.href='/login'}}>Logout</button>
        <span style={{fontSize:11,alignSelf:'center',color:'#64748b'}}>JWT expiration 1440m • Audit logged</span>
      </div>
    </div>
    <div className="card"><div style={{fontWeight:700}}>Roles</div><div style={{fontSize:12,color:'#475569',marginTop:4}}>District Collector • LAO/CALA • Revenue Officer • Legal Officer • Project Manager • Admin • Citizen (complaint without login). Backend authorization mandatory — frontend hiding alone not sufficient.</div></div>
  </div>
}
