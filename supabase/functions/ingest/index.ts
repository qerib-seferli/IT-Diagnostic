import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null,{status:204,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'authorization,apikey,content-type','Access-Control-Allow-Methods':'POST,OPTIONS'}});
  if (req.method !== 'POST') return new Response('Method not allowed', {status:405});
  try {
    const size=Number(req.headers.get('content-length')||0);
    if(size>1024*1024) return new Response('Payload too large',{status:413});
    const cleanText = (value: unknown): unknown => {
      if (typeof value === 'string') return value.replace(/\u0000/g, '').replace(/[\u0001-\u0008\u000B\u000C\u000E-\u001F]/g, '');
      if (Array.isArray(value)) return value.map(cleanText);
      if (value !== null && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k,v]) => [k, cleanText(v)]));
      return value;
    };
    const {code,report}=cleanText(await req.json()) as {code: unknown;report: any};
    if(typeof code!=='string'||code.length<16||code.length>256||!report||![1,2].includes(report.schema_version)) return new Response('Invalid request',{status:400});
    const reg=report.registration||{};
    if(!reg.organization||!reg.employee||!report.hostname||JSON.stringify(report).length>1024*1024) return new Response('Invalid report',{status:400});
    const client=createClient(Deno.env.get('SUPABASE_URL')!,Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!);
    const {data:org,error:lookupError}=await client.rpc('verify_enrollment',{org_name:reg.organization,submitted_code:code as string});
    if(lookupError||!org) return new Response('Invalid organization or code',{status:403});
    const {error}=await client.from('computer_scans').insert({organization_id:org,hostname:String(report.hostname).slice(0,128),device_id:typeof report.device_id==='string'?report.device_id.slice(0,80):null,employee:String(reg.employee).slice(0,256),department:String(reg.department||'').slice(0,256),position:String(reg.position||'').slice(0,256),room:String(reg.room||'').slice(0,128),scanned_at:report.scanned_at,payload:report});
    if(error) throw error;
    return Response.json({ok:true},{headers:{'Access-Control-Allow-Origin':'*'}});
  } catch(e){console.error(e);return new Response('Server error',{status:500});}
});
