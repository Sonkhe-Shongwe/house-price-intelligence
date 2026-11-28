import type {ReactNode} from 'react';

// Small, first-party geometry; all icons are decorative. Controls own their accessible names.
const shapes = {
  workspace: <><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M10 9v12"/></>,
  search: <><circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/></>,
  saved: <path d="M6 4h12v17l-6-4-6 4z"/>,
  compare: <><rect x="3" y="5" width="7" height="14" rx="1"/><rect x="14" y="5" width="7" height="14" rx="1"/><path d="M5.5 9h2M16.5 9h2M5.5 13h2M16.5 13h2"/></>,
  info: <><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.5v.1"/></>,
  parcel: <><path d="m3 11 9-7 9 7M5 10v10h14V10M10 20v-6h4v6"/></>,
  previous: <path d="m15 5-7 7 7 7"/>,
  next: <path d="m9 5 7 7-7 7"/>,
  down: <path d="M12 4v16m-6-6 6 6 6-6"/>,
  plus: <path d="M12 5v14M5 12h14"/>,
  minus: <path d="M5 12h14"/>,
  save: <><path d="M5 3h12l4 4v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M7 3v6h10V3M7 21v-8h10v8"/></>,
  refresh: <><path d="M20 10a8 8 0 0 0-14-4L3 9m0-5v5h5M4 14a8 8 0 0 0 14 4l3-3m0 5v-5h-5"/></>,
  open: <><path d="M13 4h7v7M20 4l-9 9M10 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-5"/></>,
  remove: <><path d="M5 7h14M9 7V4h6v3M7 7l1 13h8l1-13M10 10v7M14 10v7"/></>,
  signout: <><path d="M10 4H5v16h5M9 12h12m-5-5 5 5-5 5"/></>,
  map: <><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3zM9 3v15M15 6v15"/></>,
  warning: <><path d="M12 3 22 20H2zM12 9v5M12 17v.1"/></>,
} satisfies Record<string, ReactNode>;
export type IconName = keyof typeof shapes;

export default function Icon({name,size=18}:{name:IconName;size?:number}){
  return <svg className="hpi-icon" data-icon={name} width={size} height={size} viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round"
    aria-hidden="true" focusable="false">{shapes[name]}</svg>;
}
