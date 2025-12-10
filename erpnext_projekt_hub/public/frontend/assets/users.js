import{$ as c}from"./frappe-ui.js";/**
 * @license lucide-vue-next v0.484.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const i=e=>e.replace(/([a-z0-9])([A-Z])/g,"$1-$2").toLowerCase(),u=e=>e.replace(/^([A-Z])|[\s-_]+(\w)/g,(t,a,r)=>r?r.toUpperCase():a.toLowerCase()),k=e=>{const t=u(e);return t.charAt(0).toUpperCase()+t.slice(1)},w=(...e)=>e.filter((t,a,r)=>!!t&&t.trim()!==""&&r.indexOf(t)===a).join(" ").trim();/**
 * @license lucide-vue-next v0.484.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */var o={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-vue-next v0.484.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const y=({size:e,strokeWidth:t=2,absoluteStrokeWidth:a,color:r,iconNode:d,name:s,class:m,...l},{slots:h})=>c("svg",{...o,width:e||o.width,height:e||o.height,stroke:r||o.stroke,"stroke-width":a?Number(t)*24/Number(e):t,class:w("lucide",...s?[`lucide-${i(k(s))}-icon`,`lucide-${i(s)}`]:["lucide-icon"]),...l},[...d.map(p=>c(...p)),...h.default?[h.default()]:[]]);/**
 * @license lucide-vue-next v0.484.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const n=(e,t)=>(a,{slots:r})=>c(y,{...a,iconNode:t,name:e},r);/**
 * @license lucide-vue-next v0.484.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const g=n("calendar",[["path",{d:"M8 2v4",key:"1cmpym"}],["path",{d:"M16 2v4",key:"4m81vk"}],["rect",{width:"18",height:"18",x:"3",y:"4",rx:"2",key:"1hopcy"}],["path",{d:"M3 10h18",key:"8toen8"}]]);/**
 * @license lucide-vue-next v0.484.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const v=n("chevron-right",[["path",{d:"m9 18 6-6-6-6",key:"mthhwq"}]]);/**
 * @license lucide-vue-next v0.484.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const f=n("users",[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2",key:"1yyitq"}],["circle",{cx:"9",cy:"7",r:"4",key:"nufk8"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87",key:"kshegd"}],["path",{d:"M16 3.13a4 4 0 0 1 0 7.75",key:"1da9ce"}]]);export{v as C,f as U,g as a,n as c};
//# sourceMappingURL=users.js.map
