import Icon, {type IconName} from './Icon';
export type WorkspaceView='home'|'investigate'|'saved'|'compare'|'methodology';
const ITEMS:readonly {id:WorkspaceView;label:string;icon:IconName}[]=[
  {id:'home',label:'Workspace',icon:'workspace'},{id:'investigate',label:'Investigate',icon:'search'},
  {id:'saved',label:'Saved properties',icon:'saved'},{id:'compare',label:'Compare',icon:'compare'},
  {id:'methodology',label:'Methodology',icon:'info'}];
/** Common navigation only. Each application retains its own service and state. */
export default function WorkspaceNavigation({view,onNavigate,disabled=false,prefix='nav',label='Main navigation'}:{
  view:WorkspaceView;onNavigate:(next:WorkspaceView)=>void;disabled?:boolean;prefix?:string;label?:string;
}){
  return <nav aria-label={label}>{ITEMS.map(item=><button key={item.id} type="button"
    data-testid={prefix+'-'+item.id} aria-current={view===item.id?'page':undefined} disabled={disabled}
    onClick={()=>onNavigate(item.id)}><Icon name={item.icon}/>{item.label}</button>)}</nav>;
}
