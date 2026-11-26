export type WorkspaceView='home'|'investigate'|'saved'|'compare'|'methodology';
const ITEMS:readonly {id:WorkspaceView;label:string;symbol:string}[]=[
  {id:'home',label:'Workspace',symbol:'⌂'},{id:'investigate',label:'Investigate',symbol:'⌕'},
  {id:'saved',label:'Saved properties',symbol:'▤'},{id:'compare',label:'Compare',symbol:'▥'},
  {id:'methodology',label:'Methodology',symbol:'ⓘ'}];
/** Common navigation only. Each application retains its own service and state. */
export default function WorkspaceNavigation({view,onNavigate,disabled=false,prefix='nav',label='Main navigation'}:{
  view:WorkspaceView;onNavigate:(next:WorkspaceView)=>void;disabled?:boolean;prefix?:string;label?:string;
}){
  return <nav aria-label={label}>{ITEMS.map(item=><button key={item.id} type="button"
    data-testid={prefix+'-'+item.id} aria-current={view===item.id?'page':undefined} disabled={disabled}
    onClick={()=>onNavigate(item.id)}><span aria-hidden="true">{item.symbol}</span>{item.label}</button>)}</nav>;
}
