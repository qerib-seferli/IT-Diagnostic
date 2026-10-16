import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json, os, sys, threading, urllib.request, urllib.error, csv, socket, time
from pathlib import Path
from diagnostic import scan

ROOT = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
BUNDLE = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))
CONFIG = ROOT / 'config.json'
if not CONFIG.exists():
    CONFIG = BUNDLE / 'config.json'

def cfg():
    try:
        return json.loads(CONFIG.read_text(encoding='utf-8'))
    except Exception:
        return {}

def organizations():
    path = BUNDLE / 'organizations.csv'
    with path.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    result = {r['name'].strip(): r['short_name'].strip() for r in rows if r.get('status') == 'Aktiv' and r.get('name')}
    if len(result) != 117:
        raise ValueError('Təşkilat siyahısı natamamdır (117 tələb olunur).')
    alphabet = 'aabcçdeəfgğhxıijkqlmnoöprsştuüvyz'
    def az_key(item):
        text = item[0].casefold()
        return tuple((alphabet.index(ch) if ch in alphabet else 100 + ord(ch), ch) for ch in text)
    return dict(sorted(result.items(), key=az_key))

def clean_unicode(value):
    """Remove invalid PostgreSQL text characters without changing Azerbaijani letters."""
    if isinstance(value, str):
        return ''.join(ch for ch in value if ch != '\x00' and (ord(ch) >= 32 or ch in '\t\n\r'))
    if isinstance(value, dict):
        return {clean_unicode(k): clean_unicode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean_unicode(v) for v in value]
    return value

BG = '#edf3fa'
WHITE = '#ffffff'
NAVY = '#122943'
MUTED = '#657991'
BLUE = '#1267dc'
BORDER = '#dce5f0'

class App:
    def __init__(self, root):
        self.root = root
        self.root.title('IT Diagnostic')
        self.root.geometry('920x690')
        self.root.minsize(760, 610)
        self.root.configure(bg=BG)
        self.c = cfg()
        self.fields = {}
        self.report = None
        self.orgs = organizations()
        self.logo = None
        self.upload_seq = 0
        self.upload_active = False
        self.setup_styles()
        self.build()

    def setup_styles(self):
        s = ttk.Style(self.root)
        if 'clam' in s.theme_names():
            s.theme_use('clam')
        s.configure('App.TCombobox', font=('Segoe UI', 10), padding=4, fieldbackground=WHITE, background=WHITE, foreground=NAVY)
        s.map('App.TCombobox', fieldbackground=[('readonly', WHITE)], foreground=[('readonly', NAVY)])
        s.configure('App.TEntry', font=('Segoe UI', 10), padding=4, fieldbackground=WHITE, foreground=NAVY)
        s.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'), padding=(11, 7), background=BLUE, foreground=WHITE, borderwidth=0)
        s.map('Primary.TButton', background=[('active', '#0b56bc'), ('disabled', '#b7c9dd')], foreground=[('disabled', '#f7faff')])
        s.configure('Secondary.TButton', font=('Segoe UI', 10, 'bold'), padding=(11, 7), background='#e5effa', foreground=NAVY, borderwidth=0)
        s.map('Secondary.TButton', background=[('active', '#d2e3f7'), ('disabled', '#e8edf3')], foreground=[('disabled', '#98a8ba')])

    def label(self, parent, text, size=10, color=NAVY, bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=parent.cget('bg'), fg=color, font=('Segoe UI', size, 'bold' if bold else 'normal'), **kwargs)

    def build(self):
        shell = tk.Frame(self.root, bg=BG)
        shell.pack(fill='both', expand=True, padx=14, pady=12)
        header = tk.Frame(shell, bg=WHITE, padx=14, pady=8, highlightbackground=BORDER, highlightthickness=1)
        header.pack(fill='x')
        logo_path = BUNDLE / 'logo.png'
        if logo_path.exists():
            try:
                self.logo = tk.PhotoImage(file=str(logo_path))
                tk.Label(header, image=self.logo, bg=WHITE).pack(side='left', padx=(0, 16))
            except tk.TclError:
                self.logo = None
        title = tk.Frame(header, bg=WHITE)
        title.pack(side='right', fill='x', expand=True, padx=(28, 0))
        tk.Label(title, text='IT DIAGNOSTIC', font=('Segoe UI', 20, 'bold'), fg=NAVY, bg=WHITE).pack(anchor='w', pady=(2, 0))
        tk.Label(title, text='Kompüter diaqnostikası və inventar qeydiyyatı', font=('Segoe UI', 9), fg=MUTED, bg=WHITE).pack(anchor='w')

        card = tk.Frame(shell, bg=WHITE, padx=16, pady=9, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill='x', pady=(8, 6))
        self.label(card, 'Təşkilat və əməkdaş məlumatları', 11, bold=True).pack(anchor='w', pady=(0, 6))
        form = tk.Frame(card, bg=WHITE)
        form.pack(fill='x')
        form.columnconfigure(1, weight=1)
        names = [
            ('organization', 'Təşkilatın tam adı *'),
            ('organization_short', 'Təşkilatın qısa adı'),
            ('employee', 'Ad, soyad, ata adı *'),
            ('position', 'Vəzifə'),
            ('department', 'Şöbə'),
            ('room', 'Otaq'),
            ('enrollment_code', 'Təşkilat qeydiyyat kodu'),
        ]
        for i, (key, label) in enumerate(names):
            self.label(form, label, 10, MUTED, bold=(key in ('organization', 'employee'))).grid(row=i, column=0, sticky='w', pady=2, padx=(0, 12))
            if key == 'organization':
                widget = ttk.Combobox(form, values=list(self.orgs), state='readonly', style='App.TCombobox')
                widget.bind('<<ComboboxSelected>>', self.organization_changed)
                preset = self.c.get('organization', '')
                if preset in self.orgs:
                    widget.set(preset)
            else:
                widget = ttk.Entry(form, style='App.TEntry', show='•' if key == 'enrollment_code' else '')
                if key != 'enrollment_code':
                    widget.insert(0, self.c.get(key, ''))
                if key == 'organization_short':
                    widget.configure(state='readonly')
            widget.grid(row=i, column=1, sticky='ew', pady=2)
            self.fields[key] = widget
        self.organization_changed()

        actions = tk.Frame(shell, bg=BG)
        actions.pack(fill='x', pady=(2, 6))
        self.start = ttk.Button(actions, text='▶  Diaqnostikanı başlat', command=self.begin, style='Primary.TButton')
        self.start.pack(side='left', padx=(0, 8))
        self.send = ttk.Button(actions, text='↑  Bazaya göndər', command=self.upload, state='disabled', style='Secondary.TButton')
        self.send.pack(side='left')

        panel = tk.Frame(shell, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        panel.pack(fill='both', expand=True)
        top = tk.Frame(panel, bg=WHITE, padx=12, pady=6)
        top.pack(fill='x')
        self.label(top, 'Diaqnostika hesabatı', 12, bold=True).pack(side='left')
        self.status = tk.StringVar(value='Hazırdır. Diaqnostika yalnız bu kompüterdə aparılır.')
        tk.Label(panel, textvariable=self.status, font=('Segoe UI', 9), bg='#eaf3ff', fg='#164e96', anchor='w', padx=10, pady=6, wraplength=800, justify='left').pack(fill='x', padx=8, pady=(0, 5))
        area = tk.Frame(panel, bg=WHITE, padx=8, pady=2)
        area.pack(fill='both', expand=True)
        scroll = ttk.Scrollbar(area)
        scroll.pack(side='right', fill='y')
        self.text = tk.Text(area, height=12, wrap='word', font=('Consolas', 10), bg='#f7faff', fg=NAVY, relief='flat', padx=13, pady=13, yscrollcommand=scroll.set)
        self.text.pack(fill='both', expand=True)
        scroll.configure(command=self.text.yview)
        self.set_text('Yalnız icazəli kompüterlərdə istifadə edin. Məlumatları göndərməzdən əvvəl yoxlayın.\n')

    def set_text(self, value):
        self.text.configure(state='normal')
        self.text.delete('1.0', 'end')
        self.text.insert('end', value)
        self.text.configure(state='disabled')

    def organization_changed(self, _event=None):
        name = self.fields['organization'].get().strip()
        short = self.fields['organization_short']
        short.configure(state='normal')
        short.delete(0, 'end')
        if name in self.orgs:
            short.insert(0, self.orgs[name])
        short.configure(state='readonly')

    def values(self):
        return {k: v.get().strip() for k, v in self.fields.items()}

    def begin(self):
        v = self.values()
        if v['organization'] not in self.orgs or not v['employee']:
            messagebox.showwarning('Məlumat çatışmır', 'Təşkilatı siyahıdan seçin və əməkdaşın adını daxil edin.')
            return
        self.report = None
        self.send.configure(state='disabled')
        self.start.configure(state='disabled')
        self.status.set('Diaqnostika aparılır. Bir qədər gözləyin...')
        threading.Thread(target=self.worker, args=(v,), daemon=True).start()

    def worker(self, v):
        try:
            report = scan()
            report['registration'] = {k: value for k, value in v.items() if k != 'enrollment_code'}
            self.root.after(0, lambda: self.done(report))
        except Exception as e:
            self.root.after(0, lambda: self.fail(str(e)))

    def done(self, report):
        self.report = report
        self.start.configure(state='normal')
        failed = isinstance(report.get('data'), dict) and bool(report['data'].get('error'))
        self.send.configure(state='disabled' if failed else 'normal')
        self.status.set('Diaqnostika xətası: hesabatı yoxlayın; göndəriş dayandırıldı.' if failed else 'Diaqnostika tamamlandı. Hesabatı yoxlayın, sonra saxlayın və ya göndərin.')
        self.set_text(json.dumps(report, ensure_ascii=False, indent=2, default=str))

    def fail(self, error):
        self.start.configure(state='normal')
        self.status.set('Xəta: ' + error)

    def export(self):
        if not self.report:
            return
        path = filedialog.asksaveasfilename(defaultextension='.json', initialfile='IT-' + self.report['hostname'] + '.json', filetypes=[('JSON', '*.json')])
        if path:
            Path(path).write_text(json.dumps(self.report, ensure_ascii=False, indent=2), encoding='utf-8')
            messagebox.showinfo('Hazırdır', 'Hesabat saxlanıldı.')

    def upload(self):
        if not self.report:
            return
        if isinstance(self.report.get('data'), dict) and self.report['data'].get('error'):
            messagebox.showerror('Diaqnostika xətası', 'Natamam hesabat göndərilmir. Yenidən diaqnostika aparın.')
            return
        v = self.values()
        original = self.report.get('registration', {})
        if any(v[k] != original.get(k, '') for k in ('organization', 'organization_short', 'employee', 'position', 'department', 'room')):
            messagebox.showwarning('Məlumat dəyişib', 'Qeydiyyat məlumatları dəyişib. Yenidən diaqnostika aparın.')
            return
        url = self.c.get('ingest_url', '').strip()
        if not url or not url.startswith('https://'):
            messagebox.showwarning('Konfiqurasiya', 'config.json faylında ingest_url HTTPS ünvanını yazın.')
            return
        if not v['enrollment_code']:
            messagebox.showwarning('Kod tələb olunur', 'İdarənin qeydiyyat kodunu daxil edin.')
            return
        if not messagebox.askyesno('Təsdiq', 'Diaqnostika məlumatları və daxil etdiyiniz əməkdaş məlumatları mərkəzi bazaya göndərilsin?'):
            return
        if self.upload_active:
            return
        self.upload_active = True
        self.upload_seq += 1
        seq = self.upload_seq
        self.send.configure(state='disabled')
        self.status.set('Məlumatlar göndərilir...')
        payload_report = clean_unicode(json.loads(json.dumps(self.report, ensure_ascii=False, default=str)))
        threading.Thread(target=self.sender, args=(url, v['enrollment_code'], payload_report, seq), daemon=True).start()
        self.root.after(20000, lambda: self.upload_timeout(seq))

    def upload_timeout(self, seq):
        if self.upload_active and seq == self.upload_seq:
            self.upload_active = False
            self.send.configure(state='normal')
            self.status.set('20 saniyə ərzində cavab alınmadı. Serverdə qeydin yaranıb-yaranmadığını yoxlayın; təkrar göndərməzdən əvvəl nəticəni dəqiqləşdirin.')

    def sender(self, url, code, report, seq):
        try:
            payload = json.dumps(clean_unicode({'code': code, 'report': report}), ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json', 'apikey': self.c.get('anon_key', ''), 'Authorization': 'Bearer ' + self.c.get('anon_key', '')}, method='POST')
            with urllib.request.urlopen(req, timeout=12) as res:
                result = res.read().decode('utf-8')
            self.root.after(0, lambda: self.upload_done(seq, 'Məlumatlar bazaya uğurla göndərildi.' if json.loads(result).get('ok') is True else 'Server cavabı: ' + result[:200]))
        except urllib.error.HTTPError as e:
            details = e.read(600).decode('utf-8', errors='replace')
            self.root.after(0, lambda: self.upload_done(seq, 'Server xətası HTTP ' + str(e.code) + ': ' + details))
        except Exception as e:
            self.root.after(0, lambda: self.upload_done(seq, 'Göndərmə xətası: ' + str(e)))

    def upload_done(self, seq, msg):
        if seq != self.upload_seq or not self.upload_active:
            return
        self.upload_active = False
        self.send.configure(state='normal')
        self.status.set(msg)

if __name__ == '__main__':
    root = tk.Tk()
    try:
        App(root)
    except Exception as exc:
        messagebox.showerror('Başlatma xətası', str(exc))
        root.destroy()
    else:
        root.mainloop()
