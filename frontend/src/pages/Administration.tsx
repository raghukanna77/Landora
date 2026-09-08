export default function Administration(){
  return <div className="grid" style={{gap:12}}>
    <div className="card"><b>Administration</b><div style={{fontSize:12,color:'#64748b',marginTop:4}}>Users · Roles · Jurisdictions · Model versions · Integrations · Notification config</div>
      <div style={{marginTop:10,display:'grid',gap:6,fontSize:13}}>
        <div>Demo Users: admin/demo123 (ADMIN), officer/demo123 (STATE_OFFICER Punjab), reviewer/demo123 (NATIONAL_REVIEWER), district/demo123 (DISTRICT_OFFICER Amritsar)</div>
        <div>Integrations: Bhoomi Rashi (requires credentials), PM GatiShakti (requires credentials), DILRMP, NHAI — demo CSV adapter active</div>
        <div>Voice: DEMO MODE — BHASHINI_API_KEY not set, using DemoVoiceProvider</div>
        <div>Database: SQLite demo · PostGIS ready for production</div>
      </div>
    </div>
    <div className="card"><b>Health</b><div style={{fontSize:12,marginTop:6}}>API: ONLINE · DB: ONLINE · ML: LOADED · NLP: ONLINE · GIS: ONLINE · Voice: DEMO MODE · Notifications: ONLINE</div></div>
  </div>
}
