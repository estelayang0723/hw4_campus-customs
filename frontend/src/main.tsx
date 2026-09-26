import React, { useEffect, useState, createContext, useContext } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Link, NavLink, Route, Routes, useParams, useNavigate, useLocation } from 'react-router-dom';
import './style.css';

type User = {id: number; name: string; first_name: string | null; last_name: string | null; email: string};
const AuthContext = createContext<{user: User | null; loading: boolean; setUser: (user: User | null) => void}>({user:null, loading:true, setUser:() => {}});
async function authRequest(path: string, body?: unknown): Promise<User> {
  const response = await fetch(`/api/auth/${path}`, {method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json','X-Campus-Request':'1'}, body: JSON.stringify(body ?? {})});
  if (!response.ok) {const data = await response.json(); throw new Error(typeof data.detail === 'string' ? data.detail : 'Please check your entries.');}
  return response.status === 204 ? null : response.json();
}
function AuthProvider({children}: {children: React.ReactNode}) {
  const [user, setUser] = useState<User | null>(null); const [loading,setLoading] = useState(true);
  useEffect(() => {fetch('/api/auth/me').then(r => r.ok ? r.json() : null).then(setUser).catch(() => setUser(null)).finally(() => setLoading(false));}, []);
  return <AuthContext.Provider value={{user,loading,setUser}}>{children}</AuthContext.Provider>;
}
function AuthNav() {
  const {user,loading,setUser} = useContext(AuthContext); const [error,setError] = useState('');
  return loading ? <span>Loading account…</span> : user ? <><span className="signed-in">Hi, {user.first_name || user.name}</span><button className="logout" onClick={async () => {try {await authRequest('logout');setUser(null);setError('');} catch {setError('Could not log out. Try again.');}}}>Log out</button>{error && <span role="alert">{error}</span>}</> : <><NavLink to="/login">Log in</NavLink><NavLink to="/register">Create account</NavLink></>;
}
type Product = { total_stock?: number | null; product_id: string; name: string; garment_type: string; description: string; colors: string[]; search_tags: string[]; image_url: string; price: number; inventory?: {size: string; quantity: number}[] };
const money = (value: number) => new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD'}).format(value);
function useData<T>(url: string) {
  const [data, setData] = useState<T>();
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController(); setData(undefined); setError('');
    fetch(url, {signal: controller.signal}).then(async response => {
      if (!response.ok) throw new Error(response.status === 404 ? 'This product could not be found.' : 'Unable to load products. Please try again.');
      return response.json();
    }).then(setData).catch(error => {if (error.name !== 'AbortError') setError(error.message)});
    return () => controller.abort();
  }, [url]);
  return {data, error};
}
type ProductCardData = Pick<Product, 'product_id' | 'name' | 'price' | 'description' | 'image_url' | 'total_stock'>;
function Card({product}: {product: ProductCardData}) {
  return <Link className="card" to={`/products/${product.product_id}`}><div className="product-image"><img src={product.image_url} alt={product.name} loading="lazy"/><span>View details ↗</span>{product.total_stock === 0 && <strong className="stock-badge">Out of Stock</strong>}</div><div className="card-top"><h3>{product.name}</h3><strong>{money(product.price)}</strong></div><p className="short-description">{product.description}</p></Link>;
}
function Products({featured = false}: {featured?: boolean}) {
  const {data, error} = useData<Product[]>('/api/products');
  const [search, setSearch] = useState('');
  const filtered = data?.filter(p => `${p.name} ${p.garment_type} ${p.search_tags.join(' ')}`.toLowerCase().includes(search.toLowerCase()));
  return <section className="collection"><div className="section-heading"><div><p className="eyebrow">THE CAMPUS EDIT</p><h2>{featured ? 'Find your everyday favorite.' : 'Wear your campus pride.'}</h2></div>{featured ? <Link className="text-link" to="/products">Shop all products ↗</Link> : <label className="search">Search the collection<input value={search} onChange={e => setSearch(e.target.value)} placeholder="Try a hoodie or your college" type="search"/></label>}</div>{error ? <p role="alert">{error} Check that the backend is running.</p> : !data ? <p role="status">Loading the collection…</p> : <><p className="muted">{featured ? 'A few favorites to get you started' : `${filtered?.length} products`}</p><div className="grid">{(featured ? data.slice(0,4) : filtered)?.map(product => <Card key={product.product_id} product={product}/>)}</div>{filtered?.length === 0 && <p>No products match your search.</p>}</>}</section>;
}
function Home() {
  return <><section className="hero"><div><p className="eyebrow">CAMPUS CUSTOMS</p><h1>Welcome to Campus Customs</h1><h2><em>Wear Your True Blue Pride.</em></h2><p>Gear up and show your spirit! Whether you're cheering on the Bulldogs at the Yale Bowl, heading to class, or representing from across the globe, Campus Customs is your ultimate destination for premium campus apparel. Dive into our exclusive collections and find the perfect gear to let your Bulldog pride shine in classic Yale Blue.</p><Link className="button" to="/products">Explore the collection <span>↗</span></Link></div><div className="hero-art"><span className="edition">THE EVERYDAY / CAMPUS EDIT</span><div className="monogram">CC<span>EST. IN CAMPUS SPIRIT</span></div><span className="art-bottom">Your people. Your place. Your style.</span></div></section><div className="ribbon">CLASS DAYS <span>✦</span> GAME DAYS <span>✦</span> EVERY DAY <span>✦</span> CAMPUS CUSTOMS</div><Products featured/></>;
}
function About() {return <section className="about"><p className="eyebrow">ABOUT US</p><h1>Our Story: Rooted in Bulldog Spirit</h1><p>Born in the heart of New Haven, Campus Customs is more than just a merchandise store—it's a celebration of tradition, community, and the unmistakable Bulldog spirit. We know that wearing Yale Blue isn't just a color choice; it's a statement of pride. Our mission is to provide students, alumni, and passionate fans with high-quality, stylish, and comfortable gear. From classic tees to cozy winter hoodies, every item we curate is designed to help you carry a piece of campus with you wherever you go. Go Bulldogs!</p><Link className="button" to="/products">Find your favorite ↗</Link></section>}
function Detail() {
  const {id} = useParams(); const {data: p, error} = useData<Product>(`/api/products/${encodeURIComponent(id ?? '')}`);
  if (error) return <section><h1>Product unavailable</h1><p role="alert">{error}</p><Link to="/products">Back to products</Link></section>;
  if (!p) return <p role="status">Loading product…</p>;
  return <section><Link className="text-link" to="/products">← All products</Link><div className="detail"><div className="detail-image"><img src={p.image_url} alt={p.name}/></div><div><p className="eyebrow">{p.garment_type}</p><h1>{p.name}</h1><p className="price">{money(p.price)}</p><p>{p.description}</p><h3>Colors in this design</h3><div className="tags">{p.colors.map(c => <span key={c}>{c}</span>)}</div><h3>Size availability</h3><div className="sizes">{p.inventory?.map(item => <div key={item.size}><strong>{item.size}</strong><span>{item.quantity > 0 ? `${item.quantity} in stock` : 'Sold out'}</span></div>)}</div><p className="muted">Stock is tracked by size, not by individual color.</p><p className="product-code">Product ID: {p.product_id}</p></div></div></section>;
}
function Account({create = false}: {create?: boolean}) {
  const {user,loading,setUser} = useContext(AuthContext); const navigate = useNavigate();
  const [error,setError] = useState(''); const [busy,setBusy] = useState(false);
  if (loading) return <section role="status">Loading account…</section>;
  if (user) return <section className="account"><h1>Welcome, {user.first_name || user.name}.</h1><p>You are signed in as {user.email}.</p><Link className="button" to="/products">Browse products ↗</Link></section>;
  return <section className="account"><p className="eyebrow">YOUR CAMPUS CUSTOMS</p><h1>{create ? 'Create your account.' : 'Welcome back.'}</h1><form className="auth-form" onSubmit={async e => {
    e.preventDefault(); setError(''); const form = e.currentTarget; const values = Object.fromEntries(new FormData(form));
    if(create && values.password !== values.confirm_password) {setError('Passwords do not match.');return;}
    setBusy(true); try {const result = await authRequest(create ? 'register' : 'login', values); form.reset();setUser(result);navigate('/products');} catch(error) {setError(error instanceof Error ? error.message : 'Unable to connect. Please try again.');} finally {setBusy(false);}
  }}>{create && <div className="name-fields"><label>First name<input name="first_name" autoComplete="given-name" required maxLength={100}/></label><label>Last name<input name="last_name" autoComplete="family-name" required maxLength={100}/></label></div>}<label>Email<input name="email" type="email" autoComplete="email" required maxLength={254}/></label><label>Password<input name="password" type="password" autoComplete={create ? 'new-password' : 'current-password'} required minLength={create ? 12 : 1} maxLength={128} aria-describedby={create ? 'password-help' : undefined}/></label>{create && <><p id="password-help" className="muted">Use 12–128 characters. A long, unique passphrase works well.</p><label>Confirm password<input name="confirm_password" type="password" autoComplete="new-password" required maxLength={128}/></label></>}{error && <p className="auth-error" role="alert">{error}</p>}<button className="button" type="submit" disabled={busy}>{busy ? 'Please wait…' : create ? 'Create account' : 'Log in'}</button></form><p>{create ? 'Already have an account?' : 'New to Campus Customs?'} <Link className="text-link" to={create ? '/login' : '/register'}>{create ? 'Log in' : 'Create account'}</Link></p></section>;
}
function ChatBoundary() {
 const {user,loading}=useContext(AuthContext);
 return loading ? null : <Chat key={user?.id ?? 'guest'}/>;
}
function Chat() {
 const {user}=useContext(AuthContext); const location=useLocation();
 const [restoring,setRestoring]=useState(!!user); const [historyFailed,setHistoryFailed]=useState(false);

 const [open,setOpen]=useState(false); const [input,setInput]=useState(''); const [busy,setBusy]=useState(false); const [error,setError]=useState('');
 const [messages,setMessages]=useState<{role:'user'|'assistant';content:string;products?:ProductCardData[]}[]>([]);
 useEffect(()=>{
  if(!user)return;
  const controller=new AbortController();
  fetch('/api/chat/history',{signal:controller.signal}).then(async r=>{if(!r.ok)throw new Error('Could not restore chat. Refresh or log in again.');return r.json()}).then(data=>setMessages(data.messages)).catch(e=>{if(e.name!=='AbortError'){setError(e.message);setHistoryFailed(true)}}).finally(()=>setRestoring(false));
  return ()=>controller.abort();
 },[user?.id]);

 async function send(e: React.FormEvent) {
   e.preventDefault(); const message=input.trim(); if(!message || busy || restoring || historyFailed)return;
   setBusy(true);setError('');
   try {
     const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json','X-Campus-Request':'1'},body:JSON.stringify({message,page:{path:location.pathname},history:messages.slice(-12).map(({role,content})=>({role,content}))}),signal:AbortSignal.timeout(55000)});
     const data=await response.json();
     if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Unable to send your message.');
     setMessages(previous=>[...previous,{role:'user',content:message},{role:'assistant',content:data.reply,products:data.products ?? []}]);setInput('');
   }catch(error){setError(error instanceof Error && error.name==='TimeoutError' ? 'The assistant took too long. Please try again.' : error instanceof Error ? error.message : 'Unable to connect. Please try again.');}
   finally{setBusy(false);}
 }
 return <div className="chat">{open && <section className="chat-panel" aria-label="Campus assistant"><header><div><strong>Campus assistant</strong><small>{user ? 'Chat saved to your account' : 'Guest chat · not saved'}</small></div><button aria-label="Close chat" onClick={()=>setOpen(false)}>×</button></header><div className="messages" role="log" aria-live="polite"><p>Hi! How can I help you find your campus style? Please keep passwords and payment details out of chat.</p>{messages.map((m,i)=><div key={i}><p className={m.role}>{m.content}</p>{!!m.products?.length && <div className="chat-products" aria-label="Matching products">{m.products.map(product=><Card key={product.product_id} product={product}/>)}</div>}</div>)}{restoring && <p role="status">Restoring your chat…</p>}{busy && <div className="typing-indicator" role="status" aria-label="Assistant is typing"><span>Typing...</span><span className="typing-dots" aria-hidden="true"><i/><i/><i/></span></div>}{error && <p role="alert">{error}</p>}</div><form onSubmit={send}><input aria-label="Message" placeholder="Ask about campus favorites…" value={input} onChange={e=>setInput(e.target.value)} maxLength={2000} disabled={busy || restoring || historyFailed}/><button aria-label="Send message" type="submit" disabled={busy || restoring || historyFailed || !input.trim()}>↑</button></form></section>}<button className="chat-toggle" aria-expanded={open} onClick={()=>setOpen(!open)}><span className="bulldog-icon" aria-hidden="true"><span className="bulldog-eyes"/><span className="bulldog-muzzle"/></span>{open ? 'Close chat' : 'Let’s chat'}</button></div>;
}
function App() {const location=useLocation(); return <><div className="announcement">A little Yale spirit. A lot of everyday style.</div><header className="nav"><Link className="brand" to="/">CAMPUS<span>CUSTOMS<span className="brand-dot">®</span></span></Link><nav aria-label="Main navigation">{[['/','Home'],['/products','Products'],['/about','About us']].map(([to,label]) => <NavLink key={to} to={to} end={to === '/'}>{label}</NavLink>)}<AuthNav/></nav></header><main><div key={location.pathname} className="page-transition"><Routes><Route path="/" element={<Home/>}/><Route path="/products" element={<Products/>}/><Route path="/products/:id" element={<Detail/>}/><Route path="/about" element={<About/>}/><Route path="/login" element={<Account key="login"/>}/><Route path="/register" element={<Account key="register" create/>}/><Route path="*" element={<section><h1>Page not found.</h1><Link to="/">Go home</Link></section>}/></Routes></div></main><footer><strong>CAMPUS CUSTOMS</strong><span>Campus spirit, carried with you.</span><small>Student storefront prototype</small></footer><ChatBoundary/></>}
createRoot(document.getElementById('root')!).render(<React.StrictMode><BrowserRouter><AuthProvider><App/></AuthProvider></BrowserRouter></React.StrictMode>);
