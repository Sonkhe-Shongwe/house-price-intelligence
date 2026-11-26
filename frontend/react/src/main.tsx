import {createRoot} from 'react-dom/client';
import BuyerWorkflow from './BuyerWorkflow';
import PrivateBetaRehearsal from './PrivateBetaRehearsal';
import './style.css';
import './productRefinement.css';
import './icons.css';
import './ui.css';
createRoot(document.getElementById('root')!).render(window.location.pathname==='/private-beta-rehearsal'?<PrivateBetaRehearsal/>:<BuyerWorkflow/>);
