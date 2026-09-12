import { useEffect, useState } from "react";
import { Activity, Bot, CheckCircle2, CircleHelp, LayoutDashboard, MessageSquare, Plus, Send, ShieldCheck, Ticket, Wifi } from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
type TicketItem = {ticket_id:string; title:string; category:string; priority:string; status:string; created_at:string};
type Message = {role:"user"|"assistant"; content:string; trace?:string[]; sources?:string[]};

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [email, setEmail] = useState("demo@helpdesk.local");
  const [password, setPassword] = useState("demo1234");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([{role:"assistant", content:"Hi! I’m your AI Help Desk agent. Tell me what’s going wrong, or ask about a ticket or system outage."}]);
  const [tickets, setTickets] = useState<TicketItem[]>([]);
  const [services, setServices] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState<"chat"|"tickets"|"status">("chat");

  async function login() {
    const r = await fetch(`${API}/api/auth/login`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({email,password})});
    if (!r.ok) return alert("Login failed. Use demo@helpdesk.local / demo1234.");
    const data = await r.json(); localStorage.setItem("token", data.access_token); setToken(data.access_token);
  }
  async function load() {
    const headers = {Authorization:`Bearer ${token}`};
    const [t,s] = await Promise.all([fetch(`${API}/api/tickets`,{headers}), fetch(`${API}/api/system/status`)]);
    if (t.ok) setTickets(await t.json()); if (s.ok) setServices(await s.json());
  }
  useEffect(()=>{if(token) load()}, [token]);
  async function send(text=input) {
    if (!text.trim() || !token) return; setInput(""); setBusy(true);
    setMessages(m=>[...m,{role:"user",content:text},{role:"assistant",content:"Working through the request…"}]);
    const r = await fetch(`${API}/api/chat`, {method:"POST", headers:{"Content-Type":"application/json",Authorization:`Bearer ${token}`}, body:JSON.stringify({message:text})});
    const data = await r.json();
    setMessages(m=>[...m.slice(0,-1), {role:"assistant",content:data.answer,trace:data.tool_trace,sources:data.sources}]);
    setBusy(false); load();
  }
  if (!token) return <div className="login"><div className="login-card"><div className="logo"><Bot size={26}/> HelixDesk</div><h1>Support that thinks ahead.</h1><p>Agentic IT support for your team.</p><input value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email"/><input value={password} onChange={e=>setPassword(e.target.value)} type="password" placeholder="Password"/><button onClick={login}>Sign in <Send size={16}/></button><small>Demo: demo@helpdesk.local / demo1234</small></div></div>;
  return <div className="shell">
    <aside><div className="logo"><Bot size={24}/> HelixDesk</div><div className="workspace">ACME • IT OPERATIONS</div><nav>
      <button className={view==="chat"?"active":""} onClick={()=>setView("chat")}><MessageSquare/> AI Help Desk</button>
      <button className={view==="tickets"?"active":""} onClick={()=>setView("tickets")}><Ticket/> My tickets <b>{tickets.length}</b></button>
      <button className={view==="status"?"active":""} onClick={()=>setView("status")}><Activity/> System status</button>
    </nav><div className="side-bottom"><ShieldCheck/> Secure workspace<br/><span>JWT protected · audit ready</span></div></aside>
    <main><header><div><span className="eyebrow">IT SERVICE CENTER</span><h2>{view==="chat"?"AI Help Desk":view==="tickets"?"My tickets":"System status"}</h2></div><div className="user-pill"><span className="avatar">DU</span> Demo User <span className="online"></span></div></header>
      {view==="chat" && <section className="chat-layout"><div className="chat-card"><div className="chat-top"><div className="agent-title"><span className="agent-icon"><Bot/></span><div><strong>Helix AI</strong><small>Agentic support assistant · Online</small></div></div><button className="new-chat" onClick={()=>setMessages([{role:"assistant",content:"New conversation started. What can I help you solve?"}])}><Plus size={16}/> New chat</button></div><div className="messages">{messages.map((m,i)=><div className={`message ${m.role}`} key={i}><div className="message-avatar">{m.role==="assistant"?<Bot size={17}/>: "DU"}</div><div><div className="bubble">{m.content.split("\n").map((line,j)=><p key={j}>{line}</p>)}</div>{m.trace&&<div className="trace">{m.trace.map(x=><span key={x}><CheckCircle2 size={12}/>{x}</span>)}</div>}{m.sources?.length>0&&<div className="sources">Sources: {m.sources.join(" · ")}</div>}</div></div>)}</div><div className="suggestions"><button onClick={()=>send("My WiFi is not working")}>My WiFi is not working</button><button onClick={()=>send("Is authentication down?")}>Check system outage</button><button onClick={()=>send("Create a ticket for my laptop issue")}>Create a support ticket</button></div><div className="composer"><input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==="Enter"&&send()} placeholder="Describe your issue…"/><button disabled={busy} onClick={()=>send()}><Send size={18}/></button></div></div><div className="insight"><div className="panel-title"><CircleHelp size={17}/> What I can do</div><p>Understand issues, search trusted support knowledge, check live service health, and create tickets when you need a human.</p><div className="mini-stat"><span><Wifi size={16}/> Services</span><strong>{services.filter(x=>x.status==="Operational").length}/{services.length || 7} operational</strong></div><div className="mini-stat"><span><Ticket size={16}/> Open tickets</span><strong>{tickets.filter(x=>x.status!=="RESOLVED").length}</strong></div></div></section>}
      {view==="tickets" && <section className="page-card"><div className="section-head"><div><span className="eyebrow">REQUEST HISTORY</span><h3>Tickets assigned to you</h3></div><button onClick={()=>setView("chat")} className="primary"><MessageSquare size={16}/> Ask Helix AI</button></div>{tickets.length===0?<div className="empty">No tickets yet. Ask the AI to create one when troubleshooting does not solve your issue.</div>:<div className="ticket-list">{tickets.map(t=><div className="ticket-row" key={t.ticket_id}><div className="ticket-icon"><Ticket size={17}/></div><div className="ticket-main"><strong>{t.ticket_id} · {t.title}</strong><small>{t.category} · {new Date(t.created_at).toLocaleDateString()}</small></div><span className={`priority ${t.priority.toLowerCase()}`}>{t.priority}</span><span className="status">{t.status.replace("_"," ")}</span></div>)}</div>}</section>}
      {view==="status" && <section className="page-card"><div className="section-head"><div><span className="eyebrow">LIVE MONITORING</span><h3>Service health</h3></div><span className="healthy"><span className="online"/> All systems operational</span></div><div className="service-grid">{services.map(s=><div className="service" key={s.name}><div><strong>{s.name}</strong><small>{s.message}</small></div><span className="service-status"><span className="online"/>{s.status}</span></div>)}</div></section>}
    </main>
  </div>
}
export default App;