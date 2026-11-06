import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { api } from './services/api'

function App() {
  const [files, setFiles] = useState([]), [documents, setDocuments] = useState([]), [busy, setBusy] = useState(false)
  const [question, setQuestion] = useState(''), [messages, setMessages] = useState([]), [drag, setDrag] = useState(false), [notice, setNotice] = useState('')
  const input = useRef(null)
  const refresh = async () => { try { const { data } = await api.get('/documents'); setDocuments(data.documents || []) } catch { setNotice('Could not reach the backend. Start FastAPI on port 8000.') } }
  useEffect(() => { refresh() }, [])
  const upload = async () => {
    if (!files.length) return
    const body = new FormData(); files.forEach(file => body.append('files', file)); setBusy(true); setNotice('Processing documents…')
    try { const { data } = await api.post('/documents/upload', body, { onUploadProgress: e => { if (e.total) setNotice(`Uploading ${Math.round(e.loaded / e.total * 100)}% · extracting and indexing…`) } }); setNotice(data.documents.map(d => `${d.document_name}: ${d.chunk_count} chunks indexed`).join(' · ')); setFiles([]); if (input.current) input.current.value = ''; await refresh() }
    catch (error) { setNotice(error.response?.data?.detail || 'Upload failed. Check file type, size, API key, and backend logs.') }
    finally { setBusy(false) }
  }
  const ask = async e => {
    e?.preventDefault(); const text = question.trim(); if (!text || busy) return
    setQuestion(''); setMessages(old => [...old, { role: 'user', text }]); setBusy(true)
    try { const { data } = await api.post('/chat', { question: text }); setMessages(old => [...old, { role: 'assistant', ...data }]) }
    catch (error) { setMessages(old => [...old, { role: 'assistant', answer: error.response?.data?.detail || 'The request failed. Is the backend running?' }]) }
    finally { setBusy(false) }
  }
  const remove = async id => { try { await api.delete(`/documents/${id}`); await refresh() } catch { setNotice('Could not remove the document.') } }
  const addFiles = list => setFiles(old => [...old, ...Array.from(list).filter(f => /\.(pdf|docx|txt)$/i.test(f.name))])
  return <main className="shell">
    <header className="topbar"><a className="brand" href="#"><span className="brand-icon">✳</span> atlas<span className="brand-light">/local</span></a><div className="status"><i/> LOCAL WORKSPACE <span className="divider"/> OPENAI CONNECTED</div><div className="avatar">R</div></header>
    <section className="hero"><div className="eyebrow"><span/> PRIVATE KNOWLEDGE ASSISTANT</div><h1>Your documents,<br/><em>with answers.</em></h1><p>Upload what matters. Ask anything. Get answers grounded in your own library.</p><div className="hero-stats"><span><b>{documents.length.toString().padStart(2, '0')}</b> DOCUMENTS</span><span><b>{documents.reduce((n,d)=>n+d.chunk_count,0).toLocaleString()}</b> SEARCHABLE CHUNKS</span><span><b>FAISS</b> LOCAL INDEX</span></div></section>
    <section className="workspace">
      <aside className="library"><div className="section-head"><div><div className="eyebrow">YOUR LIBRARY</div><h2>Knowledge base <small>{documents.length}</small></h2></div><button className="icon-btn" onClick={refresh} title="Refresh">↻</button></div>
        <label className={`dropzone ${drag?'drag':''}`} onDragOver={e=>{e.preventDefault();setDrag(true)}} onDragLeave={()=>setDrag(false)} onDrop={e=>{e.preventDefault();setDrag(false);addFiles(e.dataTransfer.files)}}><input ref={input} type="file" multiple accept=".pdf,.docx,.txt" onChange={e=>addFiles(e.target.files)}/><div className="upload-icon">↑</div><strong>Drop files to upload</strong><span>or <u>browse your computer</u></span><small>PDF, DOCX, TXT <b>·</b> UP TO 20 MB EACH</small></label>
        {!!files.length && <div className="selected">{files.map((f,i)=><div key={i} className="file-row">▤ <span>{f.name}</span><button onClick={()=>setFiles(files.filter((_,j)=>j!==i))}>×</button></div>)}<button className="upload-button" disabled={busy} onClick={upload}>{busy?'Processing…':`Index ${files.length} file${files.length>1?'s':''} →`}</button></div>}
        {notice && <div className="notice">{notice}</div>}<div className="list-title">INDEXED DOCUMENTS <span>{documents.length}</span></div>
        <div className="doc-list">{documents.map(doc=><div className="doc-card" key={doc.document_id}><span className="doc-type">{doc.document_name.toLowerCase().endsWith('.pdf')?'PDF':doc.document_name.toLowerCase().endsWith('.docx')?'DOC':'TXT'}</span><div className="doc-info"><strong title={doc.document_name}>{doc.document_name}</strong><small>{doc.chunk_count} chunks · {new Date(doc.uploaded_at).toLocaleDateString()}</small></div><button className="remove" onClick={()=>remove(doc.document_id)} title="Remove document">×</button></div>)}{!documents.length && <div className="empty">Your indexed documents will appear here.</div>}</div>
        <div className="privacy"><span>⌑</span><div><strong>Your data stays yours</strong><small>Files and vectors are stored locally.</small></div></div>
      </aside>
      <section className="chat-panel"><div className="section-head chat-head"><div><div className="eyebrow">ASK YOUR KNOWLEDGE BASE</div><h2>New conversation <span className="live-dot"/></h2></div><button className="new-chat" onClick={()=>setMessages([])}>＋ <span>New chat</span></button></div>
        <div className="conversation">{!messages.length ? <div className="welcome"><div className="orb">✳</div><h3>What would you like to know?</h3><p>Answers are synthesized from your uploaded documents,<br/>with page-level references so you can verify every detail.</p><div className="suggestions">{['Summarize the main themes','What are the key dates?','Find the approval process'].map(s=><button key={s} onClick={()=>setQuestion(s)}>{s}<span>↗</span></button>)}</div></div> : messages.map((m,i)=><article className={`message ${m.role}`} key={i}><div className="bubble-label">{m.role==='user'?'YOU':'✳  ATLAS'}</div><div className="bubble">{m.role==='user'?m.text:<><ReactMarkdown>{m.answer}</ReactMarkdown>{m.sources?.length>0&&<div className="sources"><div className="source-heading">SOURCES <span>{m.sources.length}</span></div>{m.sources.map((s,j)=><details key={j}><summary><span className="doc-type mini">{s.document_name.split('.').pop().toUpperCase()}</span>{s.document_name}<b>{s.page_number?`p. ${s.page_number}`:'source'}</b></summary><p>{s.content}</p></details>)}</div>}</>}</div></article>)}{busy && !files.length && <div className="thinking"><span/><span/><span/> Searching your knowledge base…</div>}</div>
        <form className="composer" onSubmit={ask}><textarea rows="1" value={question} onChange={e=>setQuestion(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();ask()}}} placeholder="Ask a question about your documents…"/><div className="composer-bottom"><span>↵ Enter to send <b>·</b> Shift + Enter for a new line</span><button disabled={!question.trim()||busy}>Send <span>↑</span></button></div></form><div className="disclaimer">AI responses can be inaccurate. Always verify key information with the cited sources.</div>
      </section>
    </section><footer>ATLAS / LOCAL <span>BUILT FOR YOUR KNOWLEDGE</span></footer>
  </main>
}
export default App

