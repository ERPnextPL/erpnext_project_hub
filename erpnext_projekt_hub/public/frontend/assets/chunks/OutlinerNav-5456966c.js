import{a3 as b,y as I,a4 as K,L as N,r as _,j as T,z as $,w as z,a5 as E,k as v,A as x,B as p,H as S,I as A,C as O,K as V,J as F,l as H,N as U,D as q,S as D,u as P,a6 as Z,n as J}from"./frappe-ui-40f043dd.js";/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */var y={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const W=c=>c.replace(/([a-z0-9])([A-Z])/g,"$1-$2").toLowerCase(),k=(c,l)=>({size:s,strokeWidth:i=2,absoluteStrokeWidth:u,color:d,class:m,...n},{attrs:f,slots:a})=>b("svg",{...y,width:s||y.width,height:s||y.height,stroke:d||y.stroke,"stroke-width":u?Number(i)*24/Number(s):i,...f,class:["lucide",`lucide-${W(c)}`],...n},[...l.map(g=>b(...g)),...a.default?[a.default()]:[]]);/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const G=k("CheckSquareIcon",[["path",{d:"m9 11 3 3L22 4",key:"1pflzl"}],["path",{d:"M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11",key:"1jnkn4"}]]);/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Q=k("ClockIcon",[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["polyline",{points:"12 6 12 12 16 14",key:"68esgv"}]]);/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const X=k("FolderIcon",[["path",{d:"M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z",key:"1kt360"}]]);/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Y=k("UsersIcon",[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2",key:"1yyitq"}],["circle",{cx:"9",cy:"7",r:"4",key:"nufk8"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87",key:"kshegd"}],["path",{d:"M16 3.13a4 4 0 0 1 0 7.75",key:"1da9ce"}]]);const ee={class:"flex items-center gap-3"},te={class:"flex items-center gap-2 px-1"},oe={class:"absolute -bottom-5 left-1/2 -translate-x-1/2 text-[11px] text-gray-500 hidden sm:block"},ae={__name:"OutlinerNav",setup(c){const l=K(),s=N(),i=[{key:"projects",to:"/project-hub",labelKey:"Projects",icon:X,color:"text-blue-600",bg:"bg-blue-50"},{key:"tasks",to:"/project-hub/my-tasks",labelKey:"Tasks",icon:G,color:"text-blue-500",bg:"bg-blue-50"},{key:"team",to:"/project-hub/team-manager",labelKey:"Team",icon:Y,color:"text-purple-600",bg:"bg-purple-50"},{key:"time",to:"/project-hub/time-management",labelKey:"Time",icon:Q,color:"text-emerald-600",bg:"bg-emerald-50"}],u=e=>typeof window<"u"&&typeof window.__=="function"?window.__(e):e,d=_(null),m=_({}),n=e=>e?e.$el||e:null,f=()=>h("auto"),a=T(()=>{const{name:e}=l;return e==="ProjectList"||e==="ProjectOutliner"?"projects":e==="MyTasks"?"tasks":e==="TeamManager"?"team":e==="TimeManagement"?"time":"projects"});function g(e,o){const t=n(o);t&&(m.value[e]=t)}async function h(e="smooth"){await J();const o=n(d.value),t=n(m.value[a.value]);if(!o||!t||typeof o.getBoundingClientRect!="function"||typeof t.getBoundingClientRect!="function")return;const r=o.getBoundingClientRect(),w=t.getBoundingClientRect(),j=o.scrollLeft,R=o.scrollWidth-o.clientWidth,M=w.left-r.left-(r.width/2-w.width/2),B=j+M,L=Math.min(Math.max(0,B),R);o.scrollTo({left:L,behavior:e})}function C(e){l.path!==e?s.push(e):h()}return $(()=>{h("auto"),window.addEventListener("resize",f)}),z(a,()=>{h()}),E(()=>{window.removeEventListener("resize",f)}),(e,o)=>(v(),x("div",ee,[p("div",{ref_key:"scrollerRef",ref:d,class:"relative w-full max-w-[200px] sm:max-w-[260px] overflow-x-auto scrollbar-hide py-1"},[p("div",te,[(v(),x(S,null,A(i,t=>O(P(Z),{key:t.key,to:t.to,title:u(t.labelKey),class:"group relative flex-shrink-0",ref_for:!0,ref:r=>g(t.key,r),onClick:D(r=>C(t.to),["prevent"])},{default:V(()=>[p("div",{class:F(["flex items-center justify-center w-11 h-11 rounded-2xl transition-all duration-300 ease-out shadow-sm",a.value===t.key?`${t.bg} ${t.color} scale-100`:"bg-white text-gray-500 hover:bg-gray-50 hover:scale-95"])},[(v(),H(U(t.icon),{class:"w-5 h-5"}))],2),p("span",oe,q(u(t.labelKey)),1)]),_:2},1032,["to","title","onClick"])),64))])],512)]))}},ne=I(ae,[["__scopeId","data-v-0def573a"]]);export{Q as C,X as F,ne as O,Y as U,G as a,k as c};
//# sourceMappingURL=OutlinerNav-5456966c.js.map
