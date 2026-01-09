import{a4 as w,y as B,a5 as I,L as K,r as x,j as N,z as $,w as z,a6 as E,k as v,A as _,B as h,H as A,I as O,C as S,K as V,J as q,l as F,N as H,D as P,P as U,u as D,a7 as Z,n as J}from"./frappe-ui-0468379b.js";/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */var p={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const W=l=>l.replace(/([a-z0-9])([A-Z])/g,"$1-$2").toLowerCase(),c=(l,i)=>({size:s,strokeWidth:u=2,absoluteStrokeWidth:d,color:y,class:k,...n},{attrs:f,slots:a})=>w("svg",{...p,width:s||p.width,height:s||p.height,stroke:y||p.stroke,"stroke-width":d?Number(u)*24/Number(s):u,...f,class:["lucide",`lucide-${W(l)}`],...n},[...i.map(g=>w(...g)),...a.default?[a.default()]:[]]);/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const G=c("CheckSquareIcon",[["path",{d:"m9 11 3 3L22 4",key:"1pflzl"}],["path",{d:"M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11",key:"1jnkn4"}]]);/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Q=c("ClockIcon",[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["polyline",{points:"12 6 12 12 16 14",key:"68esgv"}]]);/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const X=c("FolderIcon",[["path",{d:"M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z",key:"1kt360"}]]);/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Y=c("TimerIcon",[["line",{x1:"10",x2:"14",y1:"2",y2:"2",key:"14vaq8"}],["line",{x1:"12",x2:"15",y1:"14",y2:"11",key:"17fdiu"}],["circle",{cx:"12",cy:"14",r:"8",key:"1e1u0o"}]]);/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ee=c("UsersIcon",[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2",key:"1yyitq"}],["circle",{cx:"9",cy:"7",r:"4",key:"nufk8"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87",key:"kshegd"}],["path",{d:"M16 3.13a4 4 0 0 1 0 7.75",key:"1da9ce"}]]);const te={class:"flex items-center gap-3"},oe={class:"flex items-center gap-2 px-1"},ae={class:"absolute -bottom-5 left-1/2 -translate-x-1/2 text-[11px] text-gray-500 hidden sm:block"},se={__name:"OutlinerNav",setup(l){const i=I(),s=K(),u=[{key:"projects",to:"/project-hub",labelKey:"Projects",icon:X,color:"text-blue-600",bg:"bg-blue-50"},{key:"tasks",to:"/project-hub/my-tasks",labelKey:"Tasks",icon:G,color:"text-blue-500",bg:"bg-blue-50"},{key:"my-time",to:"/project-hub/my-time-logs",labelKey:"My Time",icon:Y,color:"text-amber-600",bg:"bg-amber-50"},{key:"team",to:"/project-hub/team-manager",labelKey:"Team",icon:ee,color:"text-purple-600",bg:"bg-purple-50"},{key:"time",to:"/project-hub/time-management",labelKey:"Time",icon:Q,color:"text-emerald-600",bg:"bg-emerald-50"}],d=e=>typeof window<"u"&&typeof window.__=="function"?window.__(e):e,y=x(null),k=x({}),n=e=>e?e.$el||e:null,f=()=>m("auto"),a=N(()=>{const{name:e}=i;return e==="ProjectList"||e==="ProjectOutliner"?"projects":e==="MyTasks"?"tasks":e==="MyTimeLogs"?"my-time":e==="TeamManager"?"team":e==="TimeManagement"?"time":"projects"});function g(e,o){const t=n(o);t&&(k.value[e]=t)}async function m(e="smooth"){await J();const o=n(y.value),t=n(k.value[a.value]);if(!o||!t||typeof o.getBoundingClientRect!="function"||typeof t.getBoundingClientRect!="function")return;const r=o.getBoundingClientRect(),b=t.getBoundingClientRect(),j=o.scrollLeft,M=o.scrollWidth-o.clientWidth,R=b.left-r.left-(r.width/2-b.width/2),T=j+R,L=Math.min(Math.max(0,T),M);o.scrollTo({left:L,behavior:e})}function C(e){i.path!==e?s.push(e):m()}return $(()=>{m("auto"),window.addEventListener("resize",f)}),z(a,()=>{m()}),E(()=>{window.removeEventListener("resize",f)}),(e,o)=>(v(),_("div",te,[h("div",{ref_key:"scrollerRef",ref:y,class:"relative w-full max-w-[200px] sm:max-w-[260px] overflow-x-auto scrollbar-hide py-1"},[h("div",oe,[(v(),_(A,null,O(u,t=>S(D(Z),{key:t.key,to:t.to,title:d(t.labelKey),class:"group relative flex-shrink-0",ref_for:!0,ref:r=>g(t.key,r),onClick:U(r=>C(t.to),["prevent"])},{default:V(()=>[h("div",{class:q(["flex items-center justify-center w-11 h-11 rounded-2xl transition-all duration-300 ease-out shadow-sm",a.value===t.key?`${t.bg} ${t.color} scale-100`:"bg-white text-gray-500 hover:bg-gray-50 hover:scale-95"])},[(v(),F(H(t.icon),{class:"w-5 h-5"}))],2),h("span",ae,P(d(t.labelKey)),1)]),_:2},1032,["to","title","onClick"])),64))])],512)]))}},re=B(se,[["__scopeId","data-v-a6958cfe"]]);export{Q as C,X as F,re as O,Y as T,ee as U,G as a,c};
//# sourceMappingURL=OutlinerNav-a9c96e0f.js.map
