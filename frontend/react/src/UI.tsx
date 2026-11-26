import {useId,useLayoutEffect,useRef,useState,type ComponentPropsWithoutRef,type ReactNode} from 'react';
import Icon,{type IconName} from './Icon';

/** Native controls preserve submit, disabled, fieldset, keyboard and form semantics. */
type ButtonProps=ComponentPropsWithoutRef<'button'>&{icon:IconName;variant?:'primary'|'secondary'|'danger'|'inverse'};
export function ActionButton({icon,variant='secondary',type='button',className='',children,...props}:ButtonProps){
  return <button {...props} type={type} className={('hpi-action '+className).trim()} data-variant={variant}><Icon name={icon}/>{children}</button>;
}

type FieldProps=ComponentPropsWithoutRef<'input'>&{id:string;label:ReactNode;hint?:string};
export function Field({id,label,hint,className='',...props}:FieldProps){
  const description=[props['aria-describedby'],hint?id+'-hint':undefined].filter(Boolean).join(' ')||undefined;
  return <><label htmlFor={id}>{label}</label><input {...props} id={id} className={('hpi-field '+className).trim()} aria-describedby={description}/>{hint&&<small id={id+'-hint'} className="hpi-field-hint">{hint}</small>}</>;
}

export function PageHeading({eyebrow,title,description,action,className='hpi-page-heading',eyebrowClass='hpi-eyebrow'}:{eyebrow:string;title:ReactNode;description:ReactNode;action?:ReactNode;className?:string;eyebrowClass?:string}){
  return <div className={className}><div><p className={eyebrowClass}>{eyebrow}</p><h1>{title}</h1><p>{description}</p></div>{action}</div>;
}

type MessageProps=ComponentPropsWithoutRef<'p'>&{tone?:'info'|'error'|'success'};
export function StatusMessage({tone='info',className='',children,...props}:MessageProps){
  return <p {...props} className={('hpi-status '+className).trim()} data-tone={tone} role={tone==='error'?'alert':'status'}>{children}</p>;
}

export function EmptyState({className='',children,...props}:ComponentPropsWithoutRef<'p'>){
  return <p {...props} className={('hpi-empty-state '+className).trim()}>{children}</p>;
}

export function LoadingState({className='',children,...props}:ComponentPropsWithoutRef<'div'>){
  return <div {...props} className={('hpi-loading-state '+className).trim()}><p role="status">{children}</p><div className="hpi-skeleton-lines" aria-hidden="true"><span/><span/><span/></div></div>;
}

/** Native disclosure, initially compact on mobile. A viewport change never hides focused content. */
export function CompactDetails({summary,className='',children,...props}:ComponentPropsWithoutRef<'details'>&{summary:ReactNode}){
  const ref=useRef<HTMLDetailsElement>(null);
  useLayoutEffect(()=>{
    const media=window.matchMedia('(max-width:540px)');
    const update=()=>{
      const el=ref.current;
      if(el&&!el.contains(document.activeElement))el.open=!media.matches;
    };
    update();media.addEventListener('change',update);
    return ()=>media.removeEventListener('change',update);
  },[]);
  return <details {...props} ref={ref} className={('hpi-compact-details '+className).trim()} open><summary>{summary}</summary>{children}</details>;
}

/** Keep the native table and focusable scroll region. Only advertise overflow when measured. */
export function ScrollRegion({label,className='',children}:{label:string;className?:string;children:ReactNode}){
  const id=useId(),ref=useRef<HTMLDivElement>(null);
  const [overflow,setOverflow]=useState(false);
  useLayoutEffect(()=>{
    const el=ref.current;
    if(!el)return;
    const update=()=>setOverflow(el.clientWidth>0&&el.scrollWidth>el.clientWidth+1);
    const observer=new ResizeObserver(update);
    observer.observe(el);
    const table=el.querySelector('table');
    if(table)observer.observe(table);
    update();
    return ()=>observer.disconnect();
  },[children]);
  return <div className="hpi-scroll-shell">
    {overflow&&<p id={id} className="hpi-scroll-hint"><Icon name="next"/>More columns: scroll sideways or focus the table and use arrow keys.</p>}
    <div ref={ref} className={className} role="region" tabIndex={0} aria-label={label} aria-describedby={overflow?id:undefined}>{children}</div>
  </div>;
}
