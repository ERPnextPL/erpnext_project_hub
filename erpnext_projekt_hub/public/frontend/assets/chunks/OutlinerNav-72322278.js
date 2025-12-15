import{a3 as x,y as j,a4 as I,L as N,r as w,j as z,z as $,w as E,a5 as S,k as v,A as b,B as k,H as A,I as O,C as T,K as V,J as F,l as H,N as U,D as Z,S as q,u as D,a6 as K,n as P}from"./frappe-ui-40f043dd.js";/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */var g={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const J=l=>l.replace(/([a-z0-9])([A-Z])/g,"$1-$2").toLowerCase(),m=(l,c)=>({size:s,strokeWidth:i=2,absoluteStrokeWidth:u,color:d,class:f,...h},{attrs:n,slots:p})=>x("svg",{...g,width:s||g.width,height:s||g.height,stroke:d||g.stroke,"stroke-width":u?Number(i)*24/Number(s):i,...n,class:["lucide",`lucide-${J(l)}`],...h},[...c.map(o=>x(...o)),...p.default?[p.default()]:[]]);/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const W=m("CheckSquareIcon",[["path",{d:"m9 11 3 3L22 4",key:"1pflzl"}],["path",{d:"M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11",key:"1jnkn4"}]]);/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const G=m("ClockIcon",[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["polyline",{points:"12 6 12 12 16 14",key:"68esgv"}]]);/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Q=m("FolderIcon",[["path",{d:"M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z",key:"1kt360"}]]);/**
 * @license lucide-vue-next v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const X=m("UsersIcon",[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2",key:"1yyitq"}],["circle",{cx:"9",cy:"7",r:"4",key:"nufk8"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87",key:"kshegd"}],["path",{d:"M16 3.13a4 4 0 0 1 0 7.75",key:"1da9ce"}]]);const Y={class:"flex items-center gap-3"},ee={class:"flex items-center gap-2 px-1"},te={class:"absolute -bottom-5 left-1/2 -translate-x-1/2 text-[11px] text-gray-500 hidden sm:block"},ae={__name:"OutlinerNav",setup(l){const c=I(),s=N(),i=[{key:"projects",to:"/outliner",label:"Projekty",icon:Q,color:"text-blue-600",bg:"bg-blue-50"},{key:"tasks",to:"/outliner/my-tasks",label:"Zadania",icon:W,color:"text-blue-500",bg:"bg-blue-50"},{key:"team",to:"/outliner/team-manager",label:"Zespół",icon:X,color:"text-purple-600",bg:"bg-purple-50"},{key:"time",to:"/outliner/time-management",label:"Czas",icon:G,color:"text-emerald-600",bg:"bg-emerald-50"}],u=w(null),d=w({}),f=e=>e?e.$el||e:null,h=()=>o("auto"),n=z(()=>{const{name:e}=c;return e==="ProjectList"||e==="ProjectOutliner"?"projects":e==="MyTasks"?"tasks":e==="TeamManager"?"team":e==="TimeManagement"?"time":"projects"});function p(e,a){const t=f(a);t&&(d.value[e]=t)}async function o(e="smooth"){await P();const a=f(u.value),t=f(d.value[n.value]);if(!a||!t||typeof a.getBoundingClientRect!="function"||typeof t.getBoundingClientRect!="function")return;const r=a.getBoundingClientRect(),y=t.getBoundingClientRect(),C=a.scrollLeft,R=a.scrollWidth-a.clientWidth,M=y.left-r.left-(r.width/2-y.width/2),B=C+M,L=Math.min(Math.max(0,B),R);a.scrollTo({left:L,behavior:e})}function _(e){c.path!==e?s.push(e):o()}return $(()=>{o("auto"),window.addEventListener("resize",h)}),E(n,()=>{o()}),S(()=>{window.removeEventListener("resize",h)}),(e,a)=>(v(),b("div",Y,[k("div",{ref_key:"scrollerRef",ref:u,class:"relative w-full max-w-[200px] sm:max-w-[260px] overflow-x-auto scrollbar-hide py-1"},[k("div",ee,[(v(),b(A,null,O(i,t=>T(D(K),{key:t.key,to:t.to,title:t.label,class:"group relative flex-shrink-0",ref_for:!0,ref:r=>p(t.key,r),onClick:q(r=>_(t.to),["prevent"])},{default:V(()=>[k("div",{class:F(["flex items-center justify-center w-11 h-11 rounded-2xl transition-all duration-300 ease-out shadow-sm",n.value===t.key?`${t.bg} ${t.color} scale-100`:"bg-white text-gray-500 hover:bg-gray-50 hover:scale-95"])},[(v(),H(U(t.icon),{class:"w-5 h-5"}))],2),k("span",te,Z(t.label),1)]),_:2},1032,["to","title","onClick"])),64))])],512)]))}},se=j(ae,[["__scopeId","data-v-2c9344a7"]]);export{G as C,Q as F,se as O,X as U,W as a,m as c};
//# sourceMappingURL=OutlinerNav-72322278.js.map
