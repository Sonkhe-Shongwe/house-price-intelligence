/** Same-origin writes for the offline HTTPS session harness.
 * The existing HTTP-only fictional Basic/SQLite paths are unchanged.
 * No tokens in localStorage, query strings, logs or cross-origin requests.
 */
/** An explicit server rejection, distinct from network or validation failure. */
export class SessionUnconfirmed extends Error{
  constructor(){super('Session could not be confirmed');this.name='SessionUnconfirmed';}
}
export async function fixtureFetch(path:string,init:RequestInit={}):Promise<Response>{
  if(!path.startsWith('/')||path.startsWith('//')||path.includes('\\'))throw Error('Invalid local route');
  const headers=new Headers(init.headers);
  const method=(init.method??'GET').toUpperCase();
  if(window.location.protocol==='https:'&&!['GET','HEAD'].includes(method)){
    const res=await fetch('/auth/session',{credentials:'same-origin',cache:'no-store',signal:init.signal,redirect:'error'});
    if(res.status===401)throw new SessionUnconfirmed();
    if(!res.ok)throw Error('Fictional session unavailable');
    const value:unknown=await res.json();
    const csrf=value&&typeof value==='object'&&!Array.isArray(value)?(value as Record<string,unknown>).csrf:undefined;
    if(typeof csrf!=='string'||!/^[A-Za-z0-9_-]{43}$/.test(csrf))throw Error('Invalid session confirmation');
    headers.set('X-HPI-CSRF',csrf);
  }
  return fetch(path,{...init,headers,credentials:'same-origin',cache:'no-store',redirect:'error'});
}
