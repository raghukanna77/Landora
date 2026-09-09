import { useState, useRef, useEffect } from 'react'
import { Mic, MicOff, Volume2, X, Sparkles, Activity, AlertCircle } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'

type VoiceResp = { intent:string, response:string, navigation?:string, route?:string, filters?:any, data?:any, action?:string, voice_profile?:any }

type State = 'IDLE'|'LISTENING'|'PROCESSING'|'SPEAKING'|'ERROR'

function selectDeepVoice(): SpeechSynthesisVoice | null {
  const voices = speechSynthesis.getVoices()
  if(!voices.length) return null
  // Prefer deep male English voices
  const prefs = [
    (v:SpeechSynthesisVoice)=> /Guy|Male|David|James|George|Alex/i.test(v.name) && /en/i.test(v.lang),
    (v:SpeechSynthesisVoice)=> /en-IN/i.test(v.lang) && /Male|Guy/i.test(v.name),
    (v:SpeechSynthesisVoice)=> /en-GB.*Male/i.test(v.name),
    (v:SpeechSynthesisVoice)=> /en/i.test(v.lang),
  ]
  for(const fn of prefs){
    const f=voices.find(fn)
    if(f) return f
  }
  return voices[0]
}

function Waveform({ active, mode }:{active:boolean, mode:State}){
  const canvasRef=useRef<HTMLCanvasElement>(null)
  const animRef=useRef<number>(0)
  useEffect(()=>{
    const canvas=canvasRef.current
    if(!canvas) return
    const ctx=canvas.getContext('2d')!
    let t=0
    const draw=()=>{
      t+=0.14
      ctx.clearRect(0,0,canvas.width,canvas.height)
      const bars=18
      const w=canvas.width/bars
      for(let i=0;i<bars;i++){
        let h=4
        if(mode==='LISTENING' && active){
          h= 6 + Math.abs(Math.sin(t + i*0.55))*22 + Math.random()*6
        } else if(mode==='PROCESSING'){
          h= 10 + Math.abs(Math.sin(t*0.6 + i*0.35))*10
        } else if(mode==='SPEAKING' && active){
          h= 8 + Math.abs(Math.sin(t*0.9 + i*0.7))*18
        } else {
          h= 4 + Math.abs(Math.sin(t*0.2 + i*0.4))*3
        }
        const x=i*w + w*0.18
        const y=(canvas.height - h)/2
        ctx.fillStyle= mode==='LISTENING' ? '#ff6b35' : mode==='SPEAKING' ? '#38bdf8' : mode==='PROCESSING' ? '#f59e0b' : '#334155'
        // rounded bar
        ctx.beginPath()
        const r=3
        // @ts-ignore
        if(ctx.roundRect) ctx.roundRect(x, y, w*0.64, h, r)
        else ctx.fillRect(x,y,w*0.64,h)
        if((ctx as any).roundRect) ctx.fill()
        else ctx.fill()
      }
      animRef.current=requestAnimationFrame(draw)
    }
    draw()
    return ()=> cancelAnimationFrame(animRef.current)
  },[active, mode])
  return <canvas ref={canvasRef} width={220} height={36} style={{width:220,height:36}}/>
}

export default function VoiceAssistant({ inline=false }:{inline?:boolean}){
  const [open,setOpen]=useState(false)
  const [state,setState]=useState<State>('IDLE')
  const [transcript,setTranscript]=useState("")
  const [response,setResponse]=useState<VoiceResp|null>(null)
  const [error,setError]=useState("")
  const nav=useNavigate()
  const loc=useLocation()
  const recRef=useRef<any>(null)
  const audioCtxRef=useRef<AudioContext|null>(null)

  // preload voices
  useEffect(()=>{ speechSynthesis.getVoices(); },[])

  const currentProjectId=(()=>{
    const m=loc.pathname.match(/\/projects\/(\d+)/)
    return m? parseInt(m[1]): null
  })()

  const startListening=()=>{
    // barge-in: if speaking, stop
    if(state==='SPEAKING'){
      speechSynthesis.cancel()
      setState('IDLE')
    }
    const SR = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
    if(!SR){
      setError("SpeechRecognition not supported — use Chrome. Type below.")
      setOpen(true)
      setState('IDLE')
      return
    }
    const rec = new SR()
    rec.lang = 'en-IN'
    rec.interimResults = false
    rec.maxAlternatives = 1
    rec.continuous = false
    rec.onstart=()=>{
      setState('LISTENING'); setResponse(null); setError(""); setTranscript("")
    }
    rec.onresult=(e:any)=>{
      const txt = e.results[0][0].transcript as string
      setTranscript(txt)
      setState('PROCESSING')
      handleQuery(txt)
    }
    rec.onerror=(e:any)=>{
      setError(e.error==='not-allowed' ? "Microphone access is required for voice input." : "I couldn't understand that. Please try again.")
      setState('ERROR')
      setTimeout(()=> setState('IDLE'), 2200)
    }
    rec.onend=()=>{
      if(state==='LISTENING') setState('IDLE')
    }
    recRef.current=rec
    try{ rec.start(); setOpen(true) }catch{ setState('ERROR')}
  }

  const stopListening=()=>{
    try{ recRef.current?.stop()}catch{}
    if(state==='LISTENING') setState('IDLE')
  }

  const stopSpeaking=()=>{
    speechSynthesis.cancel()
    setState('IDLE')
  }

  const handleQuery=async(q:string)=>{
    const token=localStorage.getItem('token')
    if(!token){
      const r={intent:'AUTH', response:'Please login as officer to use voice intelligence.'}
      setResponse(r as any); setState('SPEAKING'); speak(r.response); return
    }
    setState('PROCESSING')
    try{
      const r = await fetch('/api/voice/query', {
        method:'POST',
        headers:{'Content-Type':'application/json', Authorization:`Bearer ${token}`},
        body: JSON.stringify({query:q, language:'en-IN', context:{project_id: currentProjectId, current_route: loc.pathname}})
      })
      const j = await r.json()
      if(!j.success) throw new Error(j.error?.message||'Voice intelligence is temporarily unavailable.')
      const data:VoiceResp=j.data
      setResponse(data)
      setState('SPEAKING')
      speak(data.response)
      // audit log is server side; navigation after short delay so user hears start
      const route = (data as any).navigation || (data as any).route
      if(route){
        let target=route
        const filters=(data as any).filters
        if(filters && Object.keys(filters).length){
          const qs=new URLSearchParams()
          Object.entries(filters).forEach(([k,v])=> qs.set(k, String(v)))
          if(qs.toString()) target+=`?${qs.toString()}`
        }
        // Close overlay so map/content is not stuck under backdrop — keep speaking
        setTimeout(()=>{ setOpen(false); nav(target); // allow Leaflet to measure container after navigation
          setTimeout(()=> { window.dispatchEvent(new Event('resize')); }, 320)
        }, 800)
      } else {
        // No navigation — keep overlay open for reading, auto-close after 4s if speaking done
        setTimeout(()=>{ if(state!=='LISTENING') setOpen(false)}, 4200)
      }
    }catch(e:any){
      setError(e.message || "Voice intelligence is temporarily unavailable.")
      setState('ERROR')
      speak(e.message)
      setTimeout(()=> setState('IDLE'), 1800)
    }
  }

  const speak=(text:string)=>{
    if(!text) return
    speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(text)
    const v=selectDeepVoice()
    if(v) u.voice=v
    u.lang='en-IN'
    u.rate=0.92
    u.pitch=0.72
    u.volume=1.0
    u.onstart=()=> setState('SPEAKING')
    u.onend=()=> setState('IDLE')
    u.onerror=()=> setState('IDLE')
    speechSynthesis.speak(u)
  }

  const handleTyped=(q:string)=>{
    if(!q.trim()) return
    setTranscript(q)
    handleQuery(q)
  }

  // inline variant for project detail "Generate Voice Briefing" style (not altering dashboard)
  if(inline){
    return <div className="card" style={{display:'flex',gap:8,alignItems:'center'}}>
      <button className="btn saffron" onClick={startListening} style={{display:'flex',gap:6,alignItems:'center'}}><Mic size={16}/> Voice Intelligence</button>
      <span style={{fontSize:11,color:'#64748b'}}>Ask: “Show critical projects” • “Why is this project high risk?” • “Open simulator”</span>
    </div>
  }

  return <>
    {/* Persistent circular mic — bottom-right, premium glass/dark navy, animated ring */}
    <button
      onClick={state==='SPEAKING' ? stopSpeaking : startListening}
      onKeyDown={e=>{ if(e.key==='Enter' || e.key===' ') { e.preventDefault(); startListening() } }}
      aria-label="Voice Intelligence — Ask BHOOMI"
      title="Voice Intelligence — Ask BHOOMI (Enter to activate)"
      style={{
        position:'fixed',bottom:18,right:18,width:58,height:58,borderRadius:999,
        background: state==='LISTENING' ? '#dc2626' : state==='SPEAKING' ? '#0a1930' : '#0a1930',
        color:'#fff',border:'2px solid rgba(255,255,255,0.16)',boxShadow:'0 10px 28px rgba(2,12,28,0.35), 0 0 0 1px rgba(255,107,53,0.18)',
        display:'grid',placeItems:'center',zIndex:55,cursor:'pointer',transition:'transform 0.16s',
      }}
    >
      {/* subtle animated ring */}
      <span style={{
        position:'absolute',inset:-6,borderRadius:999,border:`1px solid ${state==='LISTENING' ? 'rgba(220,38,38,0.35)' : state==='SPEAKING' ? 'rgba(56,189,248,0.28)' : 'rgba(255,107,53,0.22)'}`,
        animation: state==='IDLE' ? 'pulse 2.6s infinite' : state!=='ERROR' ? 'pulse 1.1s infinite' : undefined
      }}/>
      {state==='LISTENING' ? <Mic size={22}/> : state==='SPEAKING' ? <Volume2 size={22}/> : state==='PROCESSING' ? <Sparkles size={20}/> : <Mic size={20}/>}
    </button>

    {open && <div style={{position:'fixed',inset:0,background:'rgba(7,16,32,0.52)',backdropFilter:'blur(8px)',zIndex:60,display:'grid',placeItems:'center',padding:16}}>
      <div className="card" style={{
        width:'min(560px, 96vw)',padding:18,position:'relative',
        background:'linear-gradient(180deg, #0a1930 0%, #0f264a 100%)', color:'#e2e8f0', border:'1px solid rgba(255,255,255,0.10)',
        boxShadow:'0 20px 60px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.06)', borderRadius:16
      }}>
        <button
          onClick={()=>{setOpen(false); stopSpeaking(); stopListening(); setState('IDLE')}}
          aria-label="Close voice"
          style={{position:'absolute',top:10,right:10,background:'rgba(255,255,255,0.08)',border:'1px solid rgba(255,255,255,0.12)',borderRadius:999,width:30,height:30,display:'grid',placeItems:'center',color:'#cbd5e1'}}>
          <X size={14}/>
        </button>

        <div style={{textAlign:'center'}}>
          {/* BHOOMI INTELLIGENCE header */}
          <div style={{fontSize:10,letterSpacing:1,opacity:0.7,fontWeight:800}}>BHOOMI INTELLIGENCE</div>
          <div style={{fontSize:11,marginTop:2,display:'inline-flex',gap:6,alignItems:'center',padding:'4px 8px',borderRadius:999,background: state==='LISTENING' ? 'rgba(220,38,38,0.18)' : state==='PROCESSING' ? 'rgba(245,158,11,0.18)' : state==='SPEAKING' ? 'rgba(56,189,248,0.16)' : state==='ERROR' ? 'rgba(220,38,38,0.18)' : 'rgba(255,255,255,0.06)', border:'1px solid rgba(255,255,255,0.08)'}}>
            <span style={{width:7,height:7,borderRadius:999,background: state==='LISTENING' ? '#ef4444' : state==='PROCESSING' ? '#f59e0b' : state==='SPEAKING' ? '#38bdf8' : state==='ERROR' ? '#ef4444' : '#94a3b8', boxShadow: state!=='IDLE' ? '0 0 8px currentColor' : undefined}}/>
            {state==='LISTENING' ? '● LISTENING' : state==='PROCESSING' ? '● ANALYZING REQUEST' : state==='SPEAKING' ? '● SPEAKING' : state==='ERROR' ? '● ERROR' : '● READY'}
            <span style={{opacity:0.7,marginLeft:4,fontSize:10}}>DEMO MODE — browser SpeechSynthesis • BHASHINI adapter</span>
          </div>

          {/* Orb + waveform */}
          <div style={{marginTop:12,display:'grid',placeItems:'center',gap:8}}>
            <div style={{
              width:72,height:72,borderRadius:999,
              background: state==='LISTENING' ? 'radial-gradient(circle at 30% 30%, #ff6b35, #7f1d1d)' : state==='SPEAKING' ? 'radial-gradient(circle at 30% 30%, #0ea5e9, #0a1930)' : 'radial-gradient(circle at 30% 30%, #1e3a5f, #0a1930)',
              display:'grid',placeItems:'center',color:'#fff',
              border:'1px solid rgba(255,255,255,0.14)', boxShadow: state==='LISTENING' ? '0 0 24px rgba(220,38,38,0.45)' : state==='SPEAKING' ? '0 0 22px rgba(56,189,248,0.35)' : '0 0 18px rgba(255,107,53,0.22)',
              animation: state==='LISTENING' || state==='SPEAKING' ? 'pulse 1.2s infinite' : state==='PROCESSING' ? 'pulse 1.6s infinite' : undefined
            }}>
              {state==='SPEAKING' ? <Volume2 size={28}/> : state==='PROCESSING' ? <Activity size={26}/> : state==='ERROR' ? <AlertCircle size={26}/> : <Mic size={26}/>}
            </div>
            <Waveform active={state==='LISTENING' || state==='SPEAKING'} mode={state}/>
            <div style={{fontSize:11,color:'#94a3b8',minHeight:16}}>
              {state==='LISTENING' ? '"How can I assist you?"' : state==='PROCESSING' ? 'Querying project intelligence...' : state==='SPEAKING' ? 'BHOOMI Intelligence responding — calm command-center authority' : 'Tap mic and speak or type'}
            </div>
          </div>

          {transcript && <div style={{marginTop:10,background:'rgba(255,255,255,0.06)',border:'1px solid rgba(255,255,255,0.08)',padding:'8px 10px',borderRadius:10,fontSize:12,color:'#e2e8f0',backdropFilter:'blur(4px)'}}>&gt; “{transcript}”</div>}
          {state==='LISTENING' && <button className="btn" onClick={stopListening} style={{marginTop:10,background:'rgba(255,255,255,0.08)',color:'#e2e8f0',border:'1px solid rgba(255,255,255,0.12)'}}><MicOff size={14}/> Cancel</button>}
          {state==='PROCESSING' && <div style={{marginTop:10,fontSize:11,color:'#f59e0b',display:'flex',gap:6,alignItems:'center',justifyContent:'center'}}><Sparkles size={14}/> Analyzing request — querying project intelligence...</div>}
          {error && <div style={{marginTop:10,background:'rgba(220,38,38,0.12)',border:'1px solid rgba(220,38,38,0.22)',padding:'8px 10px',borderRadius:8,fontSize:12,color:'#fecaca'}}>{error}</div>}

          {!['LISTENING','PROCESSING'].includes(state) && response && <div style={{marginTop:12,background:'#0a1930',border:'1px solid rgba(255,255,255,0.08)',color:'#e2e8f0',padding:12,borderRadius:12,textAlign:'left',boxShadow:'inset 0 1px 0 rgba(255,255,255,0.04)'}}>
            <div style={{fontSize:10,opacity:0.6,letterSpacing:0.6}}>{response.intent} {response.action ? `• ${response.action}` : ''}</div>
            <div style={{fontWeight:700,marginTop:4,lineHeight:1.45, fontSize:13}}>{response.response}</div>
            {response.navigation && <div style={{fontSize:11,opacity:0.6,marginTop:6}}>→ Navigating to {response.navigation}</div>}
            <div style={{marginTop:8,display:'flex',gap:6}}>
              <button className="btn" style={{background:'rgba(255,255,255,0.08)',color:'#e2e8f0',border:'1px solid rgba(255,255,255,0.12)',padding:'6px 10px',fontSize:12}} onClick={()=> response.response && (()=>{
                const u=new SpeechSynthesisUtterance(response.response); const v=selectDeepVoice(); if(v) u.voice=v; u.lang='en-IN'; u.rate=0.92; u.pitch=0.72; speechSynthesis.cancel(); speechSynthesis.speak(u);
              })()}><Volume2 size={14}/> Replay</button>
              <button className="btn" style={{background:'rgba(255,255,255,0.08)',color:'#e2e8f0',border:'1px solid rgba(255,255,255,0.12)',padding:'6px 10px',fontSize:12}} onClick={stopSpeaking}><MicOff size={14}/> Stop</button>
            </div>
          </div>}

          {/* Suggestions */}
          <div style={{marginTop:12,textAlign:'left'}}>
            <div style={{fontSize:10,letterSpacing:0.6,opacity:0.6,fontWeight:800}}>TRY ASKING</div>
            <div style={{display:'flex',flexWrap:'wrap',gap:6,marginTop:6}}>
              {[
                "Show critical projects",
                "Why is this project high risk?",
                "What are today's alerts?",
                "Show grievance hotspots",
                "Give me a project briefing",
                "What actions do you recommend?",
                "Open Risk Intelligence",
                "Open What-If Simulator"
              ].map(s=> <button key={s} onClick={()=> handleTyped(s)} style={{fontSize:11,padding:'6px 8px',borderRadius:999,background:'rgba(255,255,255,0.06)',border:'1px solid rgba(255,255,255,0.10)',color:'#cbd5e1'}}>{s}</button>)}
            </div>
          </div>

          <div style={{marginTop:12,display:'flex',gap:6}}>
            <input className="input" placeholder="Type: Show critical projects" id="voice-typed" onKeyDown={e=>{ if(e.key==='Enter'){ const v=(e.target as HTMLInputElement).value; if(v) handleTyped(v); (e.target as HTMLInputElement).value=''} }} style={{flex:1,background:'rgba(255,255,255,0.06)',border:'1px solid rgba(255,255,255,0.10)',color:'#e2e8f0'}}/>
            <button className="btn" style={{background:'#ff6b35',color:'#fff',border:'none',fontWeight:800}} onClick={()=>{ const el=document.getElementById('voice-typed') as HTMLInputElement; if(el?.value) { handleTyped(el.value); el.value='' }}}>Ask</button>
          </div>
          <div style={{fontSize:10,color:'#64748b',marginTop:8,display:'flex',justifyContent:'space-between'}}>
            <span>Voice: BHOOMI Intelligence — Deep mature male, calm authority • Pitch 0.72 • Rate 0.92</span>
            <span>RBAC enforced • Audit logged</span>
          </div>
        </div>
      </div>
    </div>}
  </>
}
