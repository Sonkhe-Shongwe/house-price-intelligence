import type {ReactNode} from 'react';
import './comparisonMatrix.css';

type Column=Readonly<{key:string;title:string}>;
type Row=Readonly<{label:string;kind?:'money'|'status'|'count';values:readonly ReactNode[]}>;

/** Presentation only: callers supply already validated, source-specific evidence.
 * Neither membership, note persistence, property identity nor matching changes here.
 */
export default function ComparisonMatrix({columns,rows,caption='Saved property comparison'}:{
  columns:readonly Column[];rows:readonly Row[];caption?:string;
}){
  if(columns.length<2||columns.length>3||rows.some(row=>row.values.length!==columns.length))return null;
  return <div className="cm-region" role="region" aria-label="Property evidence comparison, scroll horizontally if needed" tabIndex={0}>
    <table className="cm-table" data-columns={columns.length} role="table">
      <caption>{caption}</caption>
      <thead role="rowgroup"><tr role="row"><th scope="col" role="columnheader">Decision factor</th>
        {columns.map((column,index)=><th key={column.key} scope="col" role="columnheader"><small>PROPERTY {String(index+1).padStart(2,'0')}</small><span>{column.title}</span></th>)}
      </tr></thead>
      <tbody role="rowgroup">{rows.map(row=><tr key={row.label} role="row"><th scope="row" role="rowheader">{row.label}</th>
        {row.values.map((value,index)=><td key={columns[index].key} role="cell" className={row.kind?'cm-'+row.kind:undefined}>{value}</td>)}
      </tr>)}</tbody>
    </table>
  </div>;
}
