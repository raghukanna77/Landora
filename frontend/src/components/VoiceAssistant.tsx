import { useState, useRef, useEffect } from 'react'
import { Mic, MicOff, Volume2, X, Pause, Play, RotateCcw } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'

type VoiceResp = { intent:string, response:string, route?:string, filters?:any, data?:any, speak?:boolean }
type VState = 'IDLE'|'LISTENING'|'PROCESSING'|'SPEAKING'|'ERROR'

const SUGGESTIONS = [
  "Show critical projects",
  "Why is this project high risk?",
  "What are today's alerts?",
  "Show grievance hotspots",
  "Give me a project briefing",
  "What actions do you recommend?",
  "Open Risk Intelligence",
  "Open the What-If Simulator",
]

function Waveform({ state, volume }: { state: VState, volume: number }){
  const bars = 24
  // volume 0-1 affects bar height when listening/speaking
  return <div style={{display:'flex',gap:3,alignItems:'center',justifyContent:'center',height:28}}>
    {Array.from({length: bars}).map((_,i)=>{
      const base = state==='LISTENING' ? 6 + volume*22 + Math.sin(Date.now()/180 + i)*4
                 : state==='SPEAKING' ? 8 + Math.abs(Math.sin(Date.now()/140 + i*0.6))*18
                 : state==='PROCESSING' ? 6 + Math.abs(Math.sin(Date.now()/300 + i))*10
                 : 4
      const h = Math.max(4, Math.min(24, base + (i%3)*2))
      return <div key={i} style={{width:3,height:h,borderRadius:999,background: state==='LISTENING' ? '#ff6b35' : state==='SPEAKING' ? '#0a1930' : state==='PROCESSING' ? '#64748b' : '#cbd5e1', transition:'height 0.08s', opacity: state==='IDLE' ? 0.6 : 1}}/>
    })}
  </div>
}

export default function VoiceAssistant({ inline=false }:{inline?:boolean}){
  const [open,setOpen]=useState(false)
  const [state,setState]=useState<VState>('IDLE')
  const [transcript,setTranscript]=useState("")
  const [interim,setInterim]=useState("")
  const [response,setResponse]=useState<VoiceResp|null>(null)
  const [volume,setVolume]=useState(0.2)
  const [error,setError]=useState("")
  const nav=useNavigate()
  const loc=useLocation()
  const recRef=useRef<any>(null)
  const audioContextRef=useRef<AudioContext|null>(null)
  const analyserRef=useRef<AnalyserNode|null>(null)

  // Extract project_id from current route for context awareness
  const projectIdFromRoute = ()=>{
    const m = loc.pathname.match(/\/projects\/(\d+)/)
    return m ? m[1] : null
  }

  // Voice selection for deep male commanding presence
  const selectDeepVoice = ()=>{
    const voices = speechSynthesis.getVoices()
    // Prefer en-IN male, then en-US male low pitch
    const preferred = voices.find(v=> v.lang==='en-IN' && /male/i.test(v.name)) ||
                      voices.find(v=> v.lang.startsWith('en') && /male/i.test(v.name)) ||
                      voices.find(v=> v.name.toLowerCase().includes('google uk english male')) ||
                      voices.find(v=> v.name.toLowerCase().includes('aaron')) ||
                      voices.find(v=> v.lang==='en-IN') ||
                      voices.find(v=> v.lang.startsWith('en')) ||
                      voices[0]
    return preferred || null
  }
  useEffect(()=>{
    // preload voices
    speechSynthesis.getVoices()
    const h = ()=> speechSynthesis.getVoices()
    speechSynthesis.onvoiceschanged = h
    return ()=> { speechSynthesis.onvoiceschanged = null }
  },[])

  // Poll volume for waveform when listening
  useEffect(()=>{
    if(state!=='LISTENING' || !analyserRef.current) return
    let raf:number
    const tick=()=>{
      if(analyserRef.current){
        const data = new Uint8Array(analyserRef.current.frequencyBinCount)
        analyserRef.current.getByteFrequencyData(data)
        const avg = data.reduce((a,b)=>a+b,0)/data.length / 255
        setVolume(avg)
      }
      raf=requestAnimationFrame(tick)
    }
    tick()
    return ()=> cancelAnimationFrame(raf)
  },[state])

  const startListening=async()=>{
    setError("")
    // barge-in: stop speaking
    speechSynthesis.cancel()
    if(state==='SPEAKING') setState('IDLE')

    const SR = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
    if(!SR){
      setError("SpeechRecognition not supported — use Chrome. Type your query below.")
      setOpen(true)
      setState('ERROR')
      return
    }
    try{
      // Try to get mic for waveform volume
      try{
        const stream = await navigator.mediaDevices.getUserMedia({audio:true})
        const ctx = new (window.AudioContext || (window as any).webkitAudioContext)()
        const src = ctx.createMediaStreamSource(stream)
        const analyser = ctx.createAnalyser()
        analyser.fftSize = 256
        src.connect(analyser)
        audioContextRef.current = ctx
        analyserRef.current = analyser
      }catch{}
    }catch{}

    const rec = new SR()
    rec.lang = 'en-IN'
    rec.interimResults = true
    rec.continuous = false
    rec.maxAlternatives = 1
    rec.onstart=()=>{ setState('LISTENING'); setResponse(null); setTranscript(""); setInterim("")}
    rec.onresult=(e:any)=>{
      let interimText=""
      let finalText=""
      for(let i=e.resultIndex;i<e.results.length;i++){
        const r=e.results[i]
        if(r.isFinal) finalText+=r[0].transcript
        else interimText+=r[0].transcript
      }
      if(interimText) setInterim(interimText)
      if(finalText){
        setTranscript(finalText)
        setInterim("")
        setState('PROCESSING')
        handleQuery(finalText)
      }
    }
    rec.onerror=(e:any)=>{
      if(e.error==='not-allowed') setError("Microphone access is required for voice input.")
      else if(e.error==='no-speech') setError("I couldn't understand that. Please try again.")
      else setError(e.error || "Voice temporarily unavailable.")
      setState('ERROR')
    }
    rec.onend=()=>{
      if(state==='LISTENING') setState('IDLE')
      try{ audioContextRef.current?.close() }catch{}
      audioContextRef.current=null
      analyserRef.current=null
    }
    recRef.current=rec
    try{ rec.start(); setOpen(true); }catch(e:any){ setError(e.message); setState('ERROR')}
    setOpen(true)
  }
  const stopListening=()=>{
    try{ recRef.current?.stop()}catch{}
    setState('IDLE')
    try{ audioContextRef.current?.close()}catch{}
  }
  const stopSpeaking=()=>{
    speechSynthesis.cancel()
    setState('IDLE')
  }

  const handleQuery=async(q:string)=>{
    const token=localStorage.getItem('token')
    if(!token){ setResponse({intent:'AUTH', response:'Please login as officer to use BHOOMI Intelligence.'}); speak('Please login as officer to use BHOOMI Intelligence.'); setState('SPEAKING'); return }
    setState('PROCESSING')
    try{
      const context = { project_id: projectIdFromRoute(), current_route: loc.pathname }
      const r = await fetch('/api/voice/query', {method:'POST', headers:{'Content-Type':'application/json', Authorization:`Bearer ${token}`}, body: JSON.stringify({query:q, language:'en-IN', context})})
      const j = await r.json()
      if(!j.success) throw new Error(j.error?.message||'Voice intelligence is temporarily unavailable.')
      const data:VoiceResp=j.data
      setResponse(data)
      // speak concise response (1-4 sentences, already concise from backend)
      if(data.speak!==false) speak(data.response)
      else setState('IDLE')
      if(data.route){
        let target=data.route
        if(data.filters){
          const qs=new URLSearchParams()
          Object.entries(data.filters).forEach(([k,v])=> { if(v) qs.set(k, String(v))})
          if(qs.toString()) target+=`?${qs.toString()}`
        }
        setTimeout(()=> nav(target), 850)
      } else {
        setState('SPEAKING')
      }
    }catch(e:any){
      setError(e.message || "Voice intelligence is temporarily unavailable.")
      setResponse({intent:'ERROR', response: e.message})
      setState('ERROR')
      // fallback to text display
    }
  }

  const speak=(text:string)=>{
    if(!text) return
    const clean = text.replace(/\s+/g,' ').trim()
    // Respect Barge-in: if user starts speaking, this will be cancelled via startListening
    const u = new SpeechSynthesisUtterance(clean)
    const voice = selectDeepVoice()
    if(voice) u.voice = voice
    u.lang='en-IN'
    u.rate=0.92 // moderate, commanding
    u.pitch=0.85 // low, deep
    u.volume=0.95
    u.onstart=()=> setState('SPEAKING')
    u.onend=()=> setState('IDLE')
    u.onerror=()=> setState('ERROR')
    speechSynthesis.cancel()
    speechSynthesis.speak(u)
  }

  const handleTyped=(q:string)=>{
    if(!q.trim()) return
    setTranscript(q)
    setState('PROCESSING')
    handleQuery(q)
  }

  // Keyboard activation
  useEffect(()=>{
    const h=(e:KeyboardEvent)=>{
      if((e.ctrlKey || e.metaKey) && e.key.toLowerCase()==='k'){ e.preventDefault(); startListening() }
      if(e.key==='Escape' && open){ setOpen(false); stopSpeaking(); stopListening()}
    }
    window.addEventListener('keydown', h)
    return ()=> window.removeEventListener('keydown', h)
  },[open, state])

  if(inline){
    return <div className="card" style={{display:'flex',gap:8,alignItems:'center',border:'1px solid #e2e8f0'}}>
      <button className="btn saffron" onClick={startListening} style={{display:'flex',gap:6,alignItems:'center'}} aria-label="Voice Intelligence"><Mic size={16}/> BHOOMI Intelligence</button>
      <span style={{fontSize:11,color:'#64748b'}}>Ask: “Show critical projects” “Why is this project high risk?”</span>
    </div>
  }

  return <>
    {/* Persistent premium button */}
    <button onClick={startListening} aria-label="Voice Intelligence — BHOOMI" title="BHOOMI Intelligence — Ctrl+K"
      style={{position:'fixed',bottom:18,right:18,width:62,height:62,borderRadius:999,background: state==='LISTENING' ? '#dc2626' : 'radial-gradient(120% 120% at 30% 20%, #1e3a5f 0%, #0a1930 60%)',color:'#fff',border:'1px solid rgba(255,255,255,0.12)',boxShadow:'0 10px 28px rgba(10,25,48,0.35), 0 0 0 1px rgba(255,255,255,0.06) inset',display:'grid',placeItems:'center',zIndex:50, cursor:'pointer', transition:'transform 0.15s'}}>
      <span style={{position:'absolute',inset:-6,borderRadius:999,border:'1px solid rgba(255,107,53,0.25)', opacity: state==='LISTENING' || state==='SPEAKING' ? 1 : 0, animation: state==='LISTENING' ? 'voicePulse 1.6s infinite' : state==='SPEAKING' ? 'voicePulse 1.2s infinite' : undefined}}/>
      <Mic size={24} style={{filter: state==='LISTENING' ? 'drop-shadow(0 0 6px rgba(255,255,255,0.6))' : undefined}}/>
      <span style={{position:'absolute',bottom:-8,background:'#0a1930',color:'#fff',fontSize:9,fontWeight:800,padding:'2px 6px',borderRadius:999,letterSpacing:0.6,border:'1px solid #1e3a5f'}}>VOICE</span>
    </button>
    <style>{`@keyframes voicePulse{0%{transform:scale(1);opacity:0.7}50%{transform:scale(1.08);opacity:0.35}100%{transform:scale(1);opacity:0.7}} @keyframes scan{0%{transform:translateX(-100%)}100%{transform:translateX(100%)}}`}</style>
    {open && <div role="dialog" aria-modal="true" aria-label="BHOOMI Intelligence Voice" style={{position:'fixed',inset:0,background:'rgba(10,25,48,0.55)',backdropFilter:'blur(6px)',zIndex:60,display:'grid',placeItems:'center',padding:16}} onClick={(e)=>{ if(e.target===e.currentTarget){ setOpen(false); stopSpeaking(); stopListening() }}}>
      <div className="card" style={{width:'min(560px, 96vw)',padding:0,overflow:'hidden',border:'1px solid #1e3a5f',boxShadow:'0 20px 60px rgba(0,0,0,0.35)',position:'relative'}}>
        {/* Header: BHOOMI INTELLIGENCE */}
        <div style={{background:'linear-gradient(180deg,#0a1930 0%, #0f264a 100%)',color:'#fff',padding:'14px 16px',display:'flex',justifyContent:'space-between',alignItems:'center'}}>
          <div style={{display:'flex',gap:10,alignItems:'center'}}>
            <span style={{width:36,height:36,borderRadius:10,background:'#ff6b35',display:'grid',placeItems:'center',fontWeight:900}}>◉</span>
            <div><div style={{fontWeight:900,letterSpacing:0.6,fontSize:13}}>BHOOMI INTELLIGENCE</div><div style={{fontSize:10,opacity:0.7,letterSpacing:0.4}}>NATIONAL INFRASTRUCTURE COMMAND — DEMO MODE</div></div>
          </div>
          <button onClick={()=>{setOpen(false); stopSpeaking(); stopListening()}} aria-label="Close" style={{background:'rgba(255,255,255,0.08)',border:'1px solid rgba(255,255,255,0.12)',color:'#fff',borderRadius:999,width:30,height:30,display:'grid',placeItems:'center'}}><X size={14}/></button>
        </div>

        {/* State badge */}
        <div style={{display:'flex',justifyContent:'center',padding:'10px 12px',gap:8,alignItems:'center',background: state==='LISTENING' ? '#fef2f2' : state==='SPEAKING' ? '#f0f4ff' : state==='PROCESSING' ? '#f8fafc' : state==='ERROR' ? '#fef2f2' : '#f8fafc',borderBottom:'1px solid #e2e8f0'}}>
          <span style={{width:8,height:8,borderRadius:999,background: state==='LISTENING' ? '#dc2626' : state==='SPEAKING' ? '#0a1930' : state==='PROCESSING' ? '#d97706' : state==='ERROR' ? '#dc2626' : '#94a3b8', display:'inline-block', boxShadow: state==='LISTENING' ? '0 0 8px #dc2626' : undefined}}/>
          <span style={{fontSize:11,fontWeight:800,letterSpacing:0.6,color: state==='LISTENING' ? '#dc2626' : state==='SPEAKING' ? '#0a1930' : '#475569'}}>{state==='LISTENING' ? '● LISTENING' : state==='PROCESSING' ? '● ANALYZING REQUEST' : state==='SPEAKING' ? '● SPEAKING' : state==='ERROR' ? '● ERROR' : '● IDLE'} — BHOOMI</span>
          {state==='SPEAKING' && <button className="btn" onClick={stopSpeaking} style={{marginLeft:8,padding:'4px 8px',fontSize:11,display:'flex',gap:4,alignItems:'center'}}><Pause size={12}/> Stop</button>}
        </div>

        <div style={{padding:16,display:'grid',gap:10}}>
          {/* Waveform */}
          <div style={{background:'#f8fafc',border:'1px solid #e2e8f0',borderRadius:12,padding:'10px 8px'}}>
            <Waveform state={state} volume={volume}/>
            <div style={{textAlign:'center',fontSize:10,color:'#64748b',marginTop:4}}>{state==='LISTENING' ? 'How can I assist you?' : state==='PROCESSING' ? 'Querying project intelligence...' : state==='SPEAKING' ? 'BHOOMI is responding — 1–4 sentences, precise' : 'Tap mic or type — barge-in: speak while BHOOMI speaks to interrupt'}</div>
          </div>

          {/* Transcript */}
          {(transcript || interim) && <div style={{background:'#0a1930',color:'#fff',padding:10,borderRadius:10,border:'1px solid #1e3a5f'}}>
            <div style={{fontSize:10,opacity:0.7,letterSpacing:0.6}}>YOU</div>
            <div style={{fontSize:13,fontWeight:700,marginTop:2,lineHeight:1.4}}>"{transcript || interim}" {interim && <span style={{opacity:0.6}}>{interim}</span>}</div>
          </div>}

          {/* Processing shimmer */}
          {state==='PROCESSING' && <div style={{height:2,background:'#e2e8f0',borderRadius:999,overflow:'hidden',position:'relative'}}><div style={{position:'absolute',inset:0,background:'linear-gradient(90deg, transparent, #0a1930, transparent)', animation:'scan 1s linear infinite', width:'50%'}}/></div>}

          {/* Response */}
          {response && state!=='LISTENING' && <div style={{background:'#ffffff',border:'1px solid #e2e8f0',padding:12,borderRadius:10}}>
            <div style={{fontSize:10,letterSpacing:0.6,color:'#64748b',fontWeight:800}}>{response.intent} {response.intent==='ERROR' ? '— error' : '— BHOOMI INTELLIGENCE'}</div>
            <div style={{fontWeight:700,marginTop:4,lineHeight:1.5,fontSize:13,whiteSpace:'pre-wrap'}}>{response.response}</div>
            {response.route && <div style={{fontSize:11,background:'#f1f5f9',padding:'6px 8px',borderRadius:8,marginTop:8}}>→ Navigating to {response.route} {response.filters && Object.keys(response.filters).length>0 ? `with ${JSON.stringify(response.filters)}` : ''}</div>}
            <div style={{display:'flex',gap:6,marginTop:8}}>
              <button className="btn" onClick={()=> speak(response.response)} style={{display:'flex',gap:4,alignItems:'center',fontSize:11}}><Play size={12}/> Replay</button>
              <button className="btn" onClick={stopSpeaking} style={{fontSize:11}}><Pause size={12}/> Pause</button>
            </div>
          </div>}

          {error && <div style={{background:'#fef2f2',border:'1px solid #fecaca',color:'#991b1b',padding:10,borderRadius:8,fontSize:12}}>{error} <button className="btn" onClick={startListening} style={{marginLeft:8,padding:'4px 8px',fontSize:11}}><RotateCcw size={12}/> Try Again</button></div>}

          {/* Input */}
          <div style={{display:'flex',gap:6}}>
            <input className="input" placeholder="Type: Show critical projects" id="voice-typed" aria-label="Type voice command" onKeyDown={e=>{ if(e.key==='Enter'){ const v=(e.target as HTMLInputElement).value; if(v){ setTranscript(v); handleTyped(v)} } }} style={{flex:1}}/>
            <button className="btn primary" onClick={()=>{ const el=document.getElementById('voice-typed') as HTMLInputElement; if(el?.value){ setTranscript(el.value); handleTyped(el.value)} }}>Ask</button>
            {state==='LISTENING' ? <button className="btn" onClick={stopListening} style={{display:'flex',gap:4,alignItems:'center'}}><MicOff size={14}/> Cancel</button> : <button className="btn saffron" onClick={startListening} style={{display:'flex',gap:4,alignItems:'center'}}><Mic size={14}/> Speak</button>}
          </div>

          {/* Suggestions */}
          <div>
            <div style={{fontSize:10,fontWeight:800,letterSpacing:0.6,color:'#64748b'}}>TRY ASKING</div>
            <div style={{display:'flex',flexWrap:'wrap',gap:6,marginTop:6}}>
              {SUGGESTIONS.map(s=> <button key={s} onClick={()=>{ setTranscript(s); handleTyped(s)}} style={{fontSize:11,background:'#f1f5f9',border:'1px solid #e2e8f0',padding:'6px 8px',borderRadius:999,cursor:'pointer'}}>{s}</button>)}
            </div>
          </div>

          <div style={{fontSize:10,color:'#64748b',textAlign:'center',borderTop:'1px solid #f1f5f9',paddingTop:8}}>Speech recognition: Demo Mode (browser) • TTS: Deep male commanding (browser fallback, BHASHINI adapter ready) • RBAC enforced • Ctrl+K to open • Esc to close • Never make voice the only way</div>
        </div>
      </div>
    </div>}
  </>
}
