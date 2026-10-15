import tkinter as tk
from tkinter import ttk,messagebox,filedialog
import json,os,sys,threading,urllib.request,urllib.error,datetime
from pathlib import Path
from diagnostic import scan

ROOT=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).parent
CONFIG=ROOT/'config.json'
if not CONFIG.exists(): CONFIG=Path(getattr(sys,'_MEIPASS',ROOT))/'config.json'

def cfg():
 try:return json.loads(CONFIG.read_text(encoding='utf-8'))
 except:return {}

class App:
 def __init__(self,root):
  self.root=root;root.title('IT Diagnostic Pro — Portable | Dövlət Su Ehtiyatları Agentliyi');root.geometry('760x650');root.minsize(640,550)
  self.c=cfg();self.fields={};self.report=None
  f=ttk.Frame(root,padding=20);f.pack(fill='both',expand=True)
  ttk.Label(f,text='AZƏRBAYCAN DÖVLƏT SU EHTİYATLARI AGENTLİYİ',font=('Segoe UI',12,'bold')).pack(anchor='w')
  ttk.Label(f,text='IT DIAGNOSTIC PRO',font=('Segoe UI',19,'bold')).pack(anchor='w')
  ttk.Label(f,text='Kompüter diaqnostikası və inventar qeydiyyatı',foreground='#666').pack(anchor='w',pady=(0,12))
  form=ttk.Frame(f);form.pack(fill='x')
  for i,(key,label) in enumerate([('organization','İdarənin tam adı *'),('organization_short','İdarənin qısa adı'),('employee','Ad, soyad, ata adı *'),('position','Vəzifə'),('department','Şöbə'),('room','Otaq'),('enrollment_code','İdarə qeydiyyat kodu (mərkəzi göndəriş üçün)')]):
   ttk.Label(form,text=label).grid(row=i,column=0,sticky='w',pady=4)
   ent=ttk.Entry(form,width=62,show='*' if key=='enrollment_code' else '')
   ent.grid(row=i,column=1,sticky='ew',padx=(12,0),pady=4);ent.insert(0,self.c.get(key,''));self.fields[key]=ent
  form.columnconfigure(1,weight=1)
  buttons=ttk.Frame(f);buttons.pack(fill='x',pady=14)
  self.start=ttk.Button(buttons,text='Diaqnostikanı başlat',command=self.begin);self.start.pack(side='left')
  self.save=ttk.Button(buttons,text='JSON hesabatını saxla',command=self.export,state='disabled');self.save.pack(side='left',padx=8)
  self.send=ttk.Button(buttons,text='Bazaya göndər',command=self.upload,state='disabled');self.send.pack(side='left')
  self.status=tk.StringVar(value='Hazırdır. Diaqnostika yalnız bu kompüterdə aparılır.')
  ttk.Label(f,textvariable=self.status,wraplength=700).pack(anchor='w')
  self.text=tk.Text(f,height=17,wrap='word',font=('Consolas',9));self.text.pack(fill='both',expand=True,pady=(8,0))
  self.text.insert('end','Yalnız icazəli kompüterlərdə istifadə edin. Məlumatları göndərməzdən əvvəl yoxlayın.\n');self.text.configure(state='disabled')
 def values(self):return {k:v.get().strip() for k,v in self.fields.items()}
 def begin(self):
  v=self.values()
  if not v['organization'] or not v['employee']:messagebox.showwarning('Məlumat çatışmır','İdarənin adı və əməkdaşın adı tələb olunur.');return
  self.start.configure(state='disabled');self.status.set('Diaqnostika aparılır. Bir qədər gözləyin...')
  threading.Thread(target=self.worker,args=(v,),daemon=True).start()
 def worker(self,v):
  try:
   report=scan();report['registration']={k:value for k,value in v.items() if k!='enrollment_code'}
   self.report=report;self.root.after(0,lambda:self.done(report))
  except Exception as e:self.root.after(0,lambda:self.fail(str(e)))
 def done(self,report):
  self.start.configure(state='normal');self.save.configure(state='normal');self.send.configure(state='normal')
  self.status.set('Diaqnostika tamamlandı. Hesabatı yoxlayın, sonra saxlayın və ya göndərin.')
  self.text.configure(state='normal');self.text.delete('1.0','end');self.text.insert('end',json.dumps(report,ensure_ascii=False,indent=2,default=str));self.text.configure(state='disabled')
 def fail(self,e):self.start.configure(state='normal');self.status.set('Xəta: '+e)
 def export(self):
  if not self.report:return
  path=filedialog.asksaveasfilename(defaultextension='.json',initialfile='IT-'+self.report['hostname']+'.json',filetypes=[('JSON','*.json')])
  if path:Path(path).write_text(json.dumps(self.report,ensure_ascii=False,indent=2),encoding='utf-8');messagebox.showinfo('Hazırdır','Hesabat saxlanıldı.')
 def upload(self):
  if not self.report:return
  v=self.values();url=self.c.get('ingest_url','').strip()
  if not url or not url.startswith('https://'):messagebox.showwarning('Konfiqurasiya','config.json faylında ingest_url HTTPS ünvanını yazın.');return
  if not v['enrollment_code']:messagebox.showwarning('Kod tələb olunur','İdarənin qeydiyyat kodunu daxil edin.');return
  if not messagebox.askyesno('Təsdiq','Diaqnostika məlumatları və daxil etdiyiniz əməkdaş məlumatları mərkəzi bazaya göndərilsin?'):return
  self.send.configure(state='disabled');self.status.set('Məlumatlar göndərilir...')
  threading.Thread(target=self.sender,args=(url,v['enrollment_code']),daemon=True).start()
 def sender(self,url,code):
  try:
   payload=json.dumps({'code':code,'report':self.report},ensure_ascii=False).encode('utf-8')
   req=urllib.request.Request(url,data=payload,headers={'Content-Type':'application/json','apikey':self.c.get('anon_key',''),'Authorization':'Bearer '+self.c.get('anon_key','')},method='POST')
   with urllib.request.urlopen(req,timeout=25) as res:result=res.read().decode('utf-8')
   self.root.after(0,lambda:self.upload_done('Göndərildi: '+result[:200]))
  except Exception as e:self.root.after(0,lambda:self.upload_done('Göndərmə xətası: '+str(e)))
 def upload_done(self,msg):self.send.configure(state='normal');self.status.set(msg)

if __name__=='__main__':
 root=tk.Tk();style=ttk.Style();style.theme_use('clam' if 'clam' in style.theme_names() else style.theme_use());App(root);root.mainloop()
