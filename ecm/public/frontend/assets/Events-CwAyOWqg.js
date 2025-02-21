var G=Object.defineProperty,H=Object.defineProperties;var W=Object.getOwnPropertyDescriptors;var A=Object.getOwnPropertySymbols;var Y=Object.prototype.hasOwnProperty,Z=Object.prototype.propertyIsEnumerable;var B=(s,a,l)=>a in s?G(s,a,{enumerable:!0,configurable:!0,writable:!0,value:l}):s[a]=l,I=(s,a)=>{for(var l in a||(a={}))Y.call(a,l)&&B(s,l,a[l]);if(A)for(var l of A(a))Z.call(a,l)&&B(s,l,a[l]);return s},K=(s,a)=>H(s,W(a));import{x as u,y as g,G as t,J as m,K as S,H as T,ac as R,a as ee,w as te,k as q,Z as D,$ as O,L as d,I as c,an as se,a9 as ae,aa as le,r as w,j as V,a5 as oe,F as p,T as ne,X as re,ao as P,Q,W as ie,Y as ce,a4 as de,C as j,a7 as L,a0 as ue,a3 as ve,n as me,ad as fe,d as _e,ap as pe,a8 as ge,a2 as M,O as he,aq as xe,ar as ye}from"./frappe-ui-BA0w7BnF.js";import{s as be,X as we,u as ke,S as $e,P as J}from"./index-CXG1Q5KM.js";const Ce={key:0,class:"flex flex-col h-full rounded-md shadow-md text-base overflow-auto",style:{"min-height":"320px"}},Ve=t("div",{class:"flex relative top-4 left-4 w-fit flex-wrap"},null,-1),Ee={key:0,class:"image-placeholder"},Se={class:"flex flex-col flex-auto p-4"},Ue=t("div",{class:"flex items-center justify-between mb-2"},null,-1),je={class:"text-xl font-semibold leading-6"},Fe={class:"short-introduction"},Ne={class:"flex items-center justify-between mt-auto"},Me={class:"flex avatar-group overlap"},Te={class:"font-thin"},De={class:"flex items-center justify-between mt-auto"},Oe={class:"flex avatar-group overlap"},ze={class:"font-semibold"},Ie={class:"font-semibold"},Ke={__name:"EventCard",props:{eventv:{type:Object,default:null}},setup(s){return be(),(a,l)=>s.eventv.title?(u(),g("div",Ce,[t("div",{class:T(["course-image",{"default-image":!s.eventv.cover_image}]),style:R({backgroundImage:"url('"+encodeURI(s.eventv.cover_image)+"')"})},[Ve,s.eventv.cover_image?S("",!0):(u(),g("div",Ee,m(s.eventv.title[0]),1))],6),t("div",Se,[Ue,t("div",je,m(s.eventv.title),1),t("div",Fe,m(s.eventv.about_event),1),t("div",Ne,[t("div",Me,[t("div",Te,m(s.eventv.start_date)+" - "+m(s.eventv.start_time)+" to "+m(s.eventv.finish_time),1)])]),t("div",De,[t("div",Oe,[t("div",ze,m(s.eventv.location),1)]),t("div",Ie," Cost "+m(s.eventv.suggested_cost)+" USD ",1)])])])):S("",!0)}},Le={class:"flex justify-between items-center"},qe={class:"flex space-x-2 text-xl"},Ae={class:"flex flex-wrap gap-4"},Be={__name:"CategoryFilter",props:{categories:{type:Array,required:!0}},setup(s){const a=s,l=ee({categories:a.categories.map(i=>K(I({},i),{checked:i.checked!==void 0?i.checked:!0}))});return te(()=>a.categories,i=>{l.categories=i.map(f=>K(I({},f),{checked:f.checked!==void 0?f.checked:!0}))}),q({url:"ecm.events_connect_management.utils.get_categories",params:{category_filter:JSON.stringify(a.categories)},auto:!0,onSuccess(i){a.categories.splice(0,a.categories.length,...i)}}),(i,f)=>(u(),g("div",Le,[t("div",qe,m(i.__("Filter Events")),1),t("div",Ae,[(u(!0),g(D,null,O(s.categories,(h,k)=>(u(),g("div",{key:k,class:"flex items-center"},[d(c(se),{size:"sm",label:h.category,disabled:!1,modelValue:h.checked,"onUpdate:modelValue":x=>h.checked=x},null,8,["label","modelValue","onUpdate:modelValue"])]))),128))])]))}},Pe={class:"grid grid-cols-3 gap-1"},Qe={class:""},Je={class:"mt-1 rounded-lg bg-white py-1 text-base shadow-2xl"},Xe={class:"flex flex-col gap-1 p-1"},Ge={class:"text-base font-medium"},He={class:"text-sm text-gray-600"},We={__name:"MultiSelect",props:ae({label:{type:String},size:{type:String,default:"sm"},doctype:{type:String,required:!0},filters:{type:Object,default:()=>({})},validate:{type:Function,default:null},errorMessage:{type:Function,default:s=>`${s} is an Invalid value`}},{modelValue:{},modelModifiers:{}}),emits:["update:modelValue"],setup(s,{expose:a}){const l=s,i=le(s,"modelValue"),f=w([]),h=w(null),k=w(null),x=w(""),E=w(""),y=w(!1),F=V({get:()=>x.value||"",set:e=>{x.value="",e&&(y.value=!1),e!=null&&e.value&&N(e.value)}});oe(x,e=>{e=e||"",E.value!==e&&(E.value=e,z(e))},{debounce:300,immediate:!0});const U=q({url:"frappe.desk.search.search_link",method:"POST",cache:[E.value,l.doctype],params:{txt:E.value,doctype:l.doctype}}),$=V(()=>U.data||[]);function z(e){U.update({params:{txt:e,doctype:l.doctype}}),U.reload()}const N=e=>{k.value=null,e&&(e.split(",").forEach(r=>{var b;if(r=r.trim(),r&&!((b=i.value)!=null&&b.includes(r))){if(r&&l.validate&&!l.validate(r)){k.value=l.errorMessage(r);return}i.value?i.value.push(r):i.value=[r],r=r.replace(r,"")}}),!k.value&&(e=""))},v=e=>{i.value=i.value.filter(_=>_!==e)},o=()=>{var _;if(x.value)return;let e=(_=f.value[f.value.length-1])==null?void 0:_.$el;document.activeElement===e?(i.value.pop(),me(()=>{i.value.length?(e=f.value[f.value.length-1].$el,e==null||e.focus()):C()})):e==null||e.focus()};function C(){h.value.$el.focus()}a({setFocus:C});const n=V(()=>[{sm:"text-xs",md:"text-base"}[l.size||"sm"],"text-gray-600"]);return(e,_)=>(u(),g("div",null,[s.label?(u(),g("label",{key:0,class:T(["block mb-1",n.value])},m(s.label),3)):S("",!0),t("div",Pe,[(u(!0),g(D,null,O(i.value,r=>(u(),j(c(L),{ref_for:!0,ref_key:"emails",ref:f,key:r,label:r,theme:"gray",variant:"subtle",class:"rounded-md",onKeydownCapture:P(Q(o,["stop"]),["delete"])},{suffix:p(()=>[d(c(we),{onClick:b=>v(r),class:"h-4 w-4 stroke-1.5"},null,8,["onClick"])]),_:2},1032,["label","onKeydownCapture"]))),128)),t("div",Qe,[d(c(de),{modelValue:F.value,"onUpdate:modelValue":_[2]||(_[2]=r=>F.value=r),nullable:""},{default:p(()=>[d(c(ne),{class:"w-full",show:y.value,"onUpdate:show":_[1]||(_[1]=r=>y.value=r)},{target:p(({togglePopover:r})=>[d(c(re),{ref_key:"search",ref:h,class:"search-input form-input w-full focus-visible:!ring-0",type:"text",value:x.value,onChange:_[0]||(_[0]=b=>{x.value=b.target.value,y.value=!0}),autocomplete:"off",onFocus:()=>r(),onKeydownCapture:P(Q(o,["stop"]),["delete"])},null,8,["value","onFocus","onKeydownCapture"])]),body:p(({isOpen:r})=>[ie(t("div",null,[t("div",Je,[d(c(ce),{class:"my-1 max-h-[12rem] overflow-y-auto px-1.5",static:""},{default:p(()=>[(u(!0),g(D,null,O($.value,b=>(u(),j(c(ue),{key:b.value,value:b},{default:p(({active:X})=>[t("li",{class:T(["flex cursor-pointer items-center rounded px-2 py-1 text-base",{"bg-gray-100":X}])},[t("div",Xe,[t("div",Ge,m(b.description),1),t("div",He,m(b.value),1)])],2)]),_:2},1032,["value"]))),128))]),_:1})])],512),[[ve,r]])]),_:1},8,["show"])]),_:1},8,["modelValue"])])])]))}},Ye={key:0},Ze={class:"sticky top-0 z-10 flex flex-col border-b bg-white px-3 py-2.5 sm:px-5"},Re={class:"flex justify-between items-center mb-2"},et={class:"flex space-x-2"},tt={class:"flex justify-between items-center"},st=t("div",{class:"flex space-x-2"},null,-1),at={class:"flex items-center"},lt={class:"flex flex-wrap gap-4"},ot={class:""},nt={key:0,class:"grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 my-5 mx-5"},rt={key:1,class:"grid flex-1 place-items-center text-xl font-medium text-gray-500"},it={class:"flex flex-col items-center justify-center mt-4"},vt={__name:"Events",setup(s){var N;const a=_e("$user"),l=w(""),i=w([]),f=w([]),h=q({url:"ecm.events_connect_management.utils.get_events",cache:["events",(N=a.data)==null?void 0:N.email],auto:!0}),k=w(0);let x;const E=V(()=>{var v,o;return x=[],y("Featured",$("featured")),y("New",$("new")),y("Upcoming",$("upcoming")),a.data&&(y("Enrolled",$("enrolled")),(a.data.is_moderator||a.data.is_instructor||(o=(v=h.data)==null?void 0:v.created)!=null&&o.length)&&y("Created",$("created")),a.data.is_moderator&&y("Under Review",$("under_review"))),x}),y=(v,o)=>{x.push({label:v,events:V(()=>o),count:V(()=>o==null?void 0:o.length)})};function F(v){i.value=v}function U(){h.reload()}const $=v=>h.data[v].filter(o=>{const C=!l.value||o.title.toLowerCase().includes(l.value.toLowerCase()),n=i.value.filter(_=>_.checked).map(_=>_.category),e=n.length===0||n.includes(o.category)&&(f.value.length===0||f.value.includes(o.country));return console.log("filter",f.value),C&&e}),z=V(()=>({title:"Events",description:"All Events divided by categories"}));return ke(z),(v,o)=>{const C=fe("router-link");return c(h).data?(u(),g("div",Ye,[t("header",Ze,[t("div",Re,[t("div",null,[d(c(pe),{class:"h-7",items:[{label:v.__("All Events"),route:{name:"Events"}}]},null,8,["items"])]),t("div",et,[d(c(ge),{type:"text",placeholder:"Search Event",modelValue:l.value,"onUpdate:modelValue":o[0]||(o[0]=n=>l.value=n),onInput:o[1]||(o[1]=n=>c(h).reload())},{prefix:p(()=>[d(c($e),{class:"w-4 stroke-1.5 text-gray-600",name:"search"})]),_:1},8,["modelValue"]),d(C,{to:{name:"CreateEvent",params:{eventName:"new"}}},{default:p(()=>{var n;return[(n=c(a).data)!=null&&n.is_moderator?(u(),j(c(L),{key:0,variant:"solid"},{prefix:p(()=>[d(c(J),{class:"h-4 w-4"})]),default:p(()=>[M(" "+m(v.__("New Event")),1)]),_:1})):S("",!0)]}),_:1})])]),d(Be,{theme:"gray",categories:i.value,"onUpdate:categories":F},null,8,["categories"]),t("div",tt,[st,t("div",at,[d(We,{modelValue:f.value,"onUpdate:modelValue":o[2]||(o[2]=n=>f.value=n),doctype:"Country",label:v.__("Country")},null,8,["modelValue","label"])]),t("div",lt,[d(c(L),{variant:"solid",onClick:o[3]||(o[3]=n=>U())},{prefix:p(()=>[d(c(J),{class:"h-4 w-4"})]),default:p(()=>[M(" "+m(v.__("Apply filter")),1)]),_:1})])])]),t("div",ot,[d(c(ye),{modelValue:k.value,"onUpdate:modelValue":o[4]||(o[4]=n=>k.value=n),tablistClass:"overflow-x-visible flex-wrap !gap-3 md:flex-nowrap",tabs:E.value},{tab:p(({tab:n,selected:e})=>[t("div",null,[t("button",{class:T(["group -mb-px flex items-center gap-2 overflow-hidden border-b border-transparent py-2.5 text-base text-gray-600 duration-300 ease-in-out hover:border-gray-400 hover:text-gray-900",{"text-gray-900":e}])},[n.icon?(u(),j(he(n.icon),{key:0,class:"h-5"})):S("",!0),M(" "+m(v.__(n.label))+" ",1),d(c(xe),{theme:"gray"},{default:p(()=>[M(m(n.count),1)]),_:2},1024)],2)])]),default:p(({tab:n})=>[n.events?(u(),g("div",nt,[(u(!0),g(D,null,O(n.events.value,e=>(u(),j(C,{to:{name:"EventDetail",params:{eventName:e.name}}},{default:p(()=>[d(Ke,{eventv:e},null,8,["eventv"])]),_:2},1032,["to"]))),256))])):(u(),g("div",rt,[t("div",it,[t("div",null,m(v.__("No {0} Events found").format(n.label.toLowerCase())),1)])]))]),_:1},8,["modelValue","tabs"])])])):S("",!0)}}};export{vt as default};
//# sourceMappingURL=Events-CwAyOWqg.js.map
