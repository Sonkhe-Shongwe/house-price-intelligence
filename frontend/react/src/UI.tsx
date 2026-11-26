import type {ComponentPropsWithoutRef,ReactNode} from 'react';
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
