import { useState, useRef } from 'react'
import { Mic, MicOff, Volume2, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

type VoiceResp = { intent:string, response:string, route?:string, filters?:any, data?:any }

export default function VoiceAssistant({ inline=false }:{inline?:boolean}){
  const [open,setOpen]=useState(false)
  const [listening,setListening]=useState(false)
  const [transcript,setTranscript]=useState("")
  const [response,setResponse]=useState<VoiceResp|null>(null)
  const [speaking,setSpeaking]=useState(false)
  const nav=useNavigate()
  const recRef=useRef<any>(null)

  const startListening=()=>{
    const SR = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
    if(!SR){ alert("SpeechRecognition not supported — use Chrome. Fallback: type query below."); setOpen(true); return }
    const rec = new SR()
    rec.lang = 'en-IN'
    rec.interimResults = false
    rec.onstart=()=>{ setListening(true); setResponse(null)}
    rec.onresult=(e:any)=>{
      const txt = e.results[0][0].transcript
      setTranscript(txt)
      setListening(false)
      handleQuery(txt)
    }
    rec.onerror=()=> setListening(false)
    rec.onend=()=> setListening(false)
    recRef.current=rec
    rec.start()
    setOpen(true)
  }
  const stopListening=()=>{
    try{ recRef.current?.stop()}catch{}
    setListening(false)
  }

  const handleQuery=async(q:string)=>{
    const token=localStorage.getItem('token')
    if(!token){ setResponse({intent:'AUTH', response:'Please login as officer to use voice intelligence.'}); speak('Please login'); return }
    try{
      const r = await fetch('/api/voice/query', {method:'POST', headers:{'Content-Type':'application/json', Authorization:`Bearer ${token}`}, body: JSON.stringify({query:q, language:'en-IN'})})
      const j = await r.json()
      if(!j.success) throw new Error(j.error?.message||'Failed')
      const data:VoiceResp=j.data
      setResponse(data)
      speak(data.response)
      if(data.route){
        // navigate with filters via query string if needed
        let target=data.route
        if(data.filters){
          const qs=new URLSearchParams()
          Object.entries(data.filters).forEach(([k,v])=> qs.set(k, String(v)))
          if(qs.toString()) target+=`?${qs.toString()}`
        }
        setTimeout(()=> nav(target), 900)
      }
    }catch(e:any){
      setResponse({intent:'ERROR', response: e.message})
      speak(e.message)
    }
  }

  const speak=(text:string)=>{
    if(!text) return
    // prefer browser TTS, backend TTS fallback via /voice/speak not needed for demo
    const u = new SpeechSynthesisUtterance(text)
    u.lang='en-IN'
    u.rate=0.95
    u.onstart=()=> setSpeaking(true)
    u.onend=()=> setSpeaking(false)
    speechSynthesis.cancel()
    speechSynthesis.speak(u)
  }
  const handleTyped=(q:string)=>{
    setTranscript(q)
    handleQuery(q)
  }

  if(inline){
    return <div className="card" style={{display:'flex',gap:8,alignItems:'center'}}>
      <button className="btn saffron" onClick={startListening} style={{display:'flex',gap:6,alignItems:'center'}}><Mic size={16}/> Voice Intelligence</button>
      <span style={{fontSize:11,color:'#64748b'}}>Ask: “Show critical projects” “Why is Project BD-EXP-004 at high risk?” “Open simulator”</span>
    </div>
  }

  return <>
    <button onClick={startListening} title="Voice Intelligence" style={{position:'fixed',bottom:18,right:18,width:56,height:56,borderRadius:999,background:'#ff6b35',color:'#fff',border:'none',boxShadow:'0 8px 20px rgba(0,0,0,0.25)',display:'grid',placeItems:'center',zIndex:50, cursor:'pointer'}}>
      <Mic size={22}/>
    </button>
    {open && <div style={{position:'fixed',inset:0,background:'rgba(10,25,48,0.45)',zIndex:60,display:'grid',placeItems:'center',padding:16}}>
      <div className="card" style={{width:'min(520px, 96vw)',padding:18,position:'relative'}}>
        <button onClick={()=>{setOpen(false); speechSynthesis.cancel(); stopListening()}} style={{position:'absolute',top:10,right:10,background:'#f1f5f9',border:'none',borderRadius:999,width:28,height:28,display:'grid',placeItems:'center'}}><X size={14}/></button>
        <div style={{textAlign:'center'}}>
          <div style={{width:64,height:64,borderRadius:999,background: listening? '#dc2626':'#0a1930',display:'grid',placeItems:'center',margin:'0 auto',color:'#fff',animation: listening? 'pulse 1.2s infinite': undefined}}>
            {listening? <Mic size={26}/> : <Volume2 size={26}/>}
          </div>
          <div style={{fontWeight:900,marginTop:8}}>🎙️ VOICE INTELLIGENCE</div>
          <div style={{fontSize:11,color:'#64748b'}}>{listening ? 'Listening...' : speaking ? '🔊 Playing response' : 'Tap mic and speak or type'}</div>
          {transcript && <div style={{marginTop:10,background:'#f8fafc',padding:8,borderRadius:8,fontSize:12,border:'1px solid #e2e8f0'}}>"{transcript}"</div>}
          {listening && <button className="btn" onClick={stopListening} style={{marginTop:10}}><MicOff size={14}/> Cancel</button>}
          {!listening && response && <div style={{marginTop:10,background:'#0a1930',color:'#fff',padding:12,borderRadius:10,textAlign:'left'}}>
            <div style={{fontSize:11,opacity:0.7}}>{response.intent}</div>
            <div style={{fontWeight:700,marginTop:4,lineHeight:1.4}}>{response.response}</div>
            {response.route && <div style={{fontSize:11,opacity:0.7,marginTop:4}}>→ Navigating to {response.route}</div>}
          </div>}
          <div style={{marginTop:12,display:'flex',gap:6}}>
            <input className="input" placeholder="Type: Show critical projects" id="voice-typed" onKeyDown={e=>{ if(e.key==='Enter'){ const v=(e.target as HTMLInputElement).value; if(v) handleTyped(v)}}} style={{flex:1}}/>
            <button className="btn primary" onClick={()=>{ const el=document.getElementById('voice-typed') as HTMLInputElement; if(el?.value) handleTyped(el.value)}}>Ask</button>
          </div>
          <div style={{fontSize:10,color:'#64748b',marginTop:8}}>Multilingual: EN/HI/TA via BHASHINI adapter (demo fallback). RBAC enforced on backend.</div>
        </div>
      </div>
    </div>}
  </>
}
