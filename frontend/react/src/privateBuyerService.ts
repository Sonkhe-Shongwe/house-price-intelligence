/** Named, same-origin private buyer operations. Transport retains session/CSRF confirmation.
 * No arbitrary route exposed, no fallback to synthetic endpoints, no client-side matching.
 */
import {fixtureFetch} from './fixtureFetch';
import {decode,decodeComparison,decodeWorkspace,decodeSearch,decodeLogout,UUID,type Entry} from './privateBuyerContract';
const ROOT='/v1/private-beta-rehearsal';
async function request(path:string,body?:object,signal?:AbortSignal):Promise<unknown>{
  const res=await fixtureFetch(ROOT+path,body===undefined?{signal}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal});
  if(!res.ok)throw Error('Unavailable');
  return await res.json() as unknown;
}
function identifier(id:string){if(!UUID.test(id))throw Error('Unavailable');return id;}
export const privateBuyerService={
  async search(query:string,analysisDate:string){
    return decodeSearch(await request('/search',{query,analysis_date:analysisDate}));
  },
  async createInvestigation(input:{addressId:string;analysisDate:string;area:number;askingPrice:string|null}){
    return decode(await request('/investigations',{township_code:'17',class_code:'203',analysis_date:input.analysisDate,subject:{address_id:input.addressId,building_area_sqft:input.area,asking_price_usd:input.askingPrice}}));
  },
  async reopenInvestigation(id:string){
    const result=decode(await request('/investigations/'+identifier(id)));
    if(result.investigation_id!==id)throw Error('Unavailable');
    return result;
  },
  async listWorkspace(signal?:AbortSignal){return decodeWorkspace(await request('/workspace',undefined,signal));},
  async createComparison(label:string,entries:readonly Pick<Entry,'investigation_id'|'note_text'>[]){
    return decodeComparison(await request('/shortlists',{label,entries:entries.map(({investigation_id,note_text})=>({investigation_id,note_text}))}));
  },
  async reopenComparison(id:string){
    const result=decodeComparison(await request('/shortlists/'+identifier(id)));
    if(result.shortlist_id!==id)throw Error('Unavailable');
    return result;
  },
  async signOut(){
    const res=await fixtureFetch('/auth/logout',{method:'POST'});
    if(!res.ok)throw Error('Sign out unavailable');
    decodeLogout(await res.json());
  },
};
