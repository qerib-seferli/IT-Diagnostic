# IT Diagnostic — Quraşdırma və test

## 1. GitHub
ZIP-in **içindəki bütün faylları və gizli `.github` qovluğunu** `qerib-seferli/IT-Diagnostic` reposunun **kökünə** yükləyin. `index.html` kökdədir; `web/` qovluğu YOXDUR.
Settings → Pages → Source: **Deploy from a branch** → `main` → `/(root)` → Save.
Əsas ünvan: https://qerib-seferli.github.io/IT-Diagnostic/

## 2. Supabase
Mövcud layihəni silməyin. SQL Editor-da `sql/01_schema.sql` işlədin. Sonra Authentication → Users → Add user bölməsində `hesen.hesenli@diagnostic.az` hesabını və özünüzün güclü şifrənizi yaradın (istifadə edilə bilən real e-poçt olmalıdır; hesabı təsdiqləyin). `sql/02_admin_ve_idare.sql` içindəki TEST İDARƏSİ adını və qeydiyyat kodunu dəyişib işə salın. Son SELECT **bir sətir** qaytarmalıdır. Şifrə SQL və GitHub-a yazılmır.

## 3. Edge Function
Supabase → Edge Functions → `ingest` yaradın və `supabase/functions/ingest/index.ts` məzmununu yerləşdirib deploy edin. `SUPABASE_URL` və `SUPABASE_SERVICE_ROLE_KEY` Edge Function mühitində mövcud olmalıdır. **Service role açarını heç vaxt GitHub və EXE-yə yazmayın.** `verify_enrollment` yalnız service_role tərəfindən çağırılır.

## 4. EXE
GitHub → Actions → `Windows Portable EXE` → Run workflow. Yaşıl olduqdan sonra Artifacts-dən `IT-Diagnostic-Windows-Portable` yükləyin. Bu mühitdə Windows EXE yaradılmayıb: GitHub Actions Windows runner-də yaradılacaq.
EXE-də təşkilatın adı SQL-dəki təşkilat adı ilə eyni olmalıdır. İdarə qeydiyyat kodunu EXE-yə daxil edin; skan nəticəsini yoxlayın və yalnız icazə ilə göndərin.

## 5. Vacib məhdudiyyətlər
Windows 7 üçün Python 3.8/PyInstaller 5 ilə uyğunluq nəzərdə tutulub, lakin Win7/10/11 üzərində real sınaq aparılmayıb. Windows 7-də TLS/sertifikat yeniləmələri lazım ola bilər. Cihaz ID-si SMBIOS UUID sabit qaldıqda OS yenilənməsindən sonra qorunur; UUID dəyişərsə avtomatik uyğunlaşdırmaya zəmanət yoxdur. Şəbəkə bölməsi yalnız skan anındakı məlumatları göstərir, canlı SNMP deyil. Bu layihə avtomatik fon monitorinqi aparmır.
