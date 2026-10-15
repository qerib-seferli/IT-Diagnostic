# IT Diagnostic Pro V2 — Quraşdırma və test

**Vacib:** İdarə və nazirlik kompüterlərində yalnız səlahiyyətli razılıqla işlədin. Buluda şəxsi məlumat göndərilməsinə ayrıca icazə alın.

## 1. GitHub
Yeni, ayrıca `IT-Diagnostic-Pro` repository yaradın. Bu ZIP-in içindəki `IT-Diagnostic-Pro-V2` qovluğunun **içindəki** faylları repo kökünə yükləyin (xüsusilə `.github/workflows` gizli qovluğunu). GitHub Pages üçün `Settings > Pages > Deploy from branch > main /web` seçin. Qeyd: GitHub Pages `/web` folderini birbaşa source kimi qəbul etməyə bilər; buna görə `Deploy Admin Panel` workflow-u əlavə edilib və `Settings > Pages > GitHub Actions` seçilməlidir.

## 2. Supabase
Yeni Supabase layihəsinin SQL Editor bölməsində `sql/schema.sql`-i **bir dəfə** işlədin. Project URL və anon key bu paketdə istifadəçinin verdiyi layihəyə bağlıdır. Heç bir service_role açarı frontend və ya EXE-də yoxdur.

`Authentication > Users > Add user` ilə Həsən Həsənlinin **real email ünvanını** və güclü şifrəni təyin edin. İstifadəçi email ünvanı təqdim etmədiyi üçün proqramda uydurma email yazılmayıb.

`organizations` cədvəlinə idarə əlavə edin (SQL-dəki nümunəyə baxın); uzun, təsadüfi qeydiyyat kodu yaradın. Sonra Auth Users-dən admin UUID götürüb `admin_members` cədvəlinə daxil edin. **Kod və şifrəni GitHub-a yazmayın.**

## 3. Edge Function
`supabase/functions/ingest/index.ts` funksiyasını Supabase CLI ilə deploy edin. Endpoint `https://djbelccbrabnimqqbqhd.supabase.co/functions/v1/ingest`. `Verify JWT` açıqdır; EXE public anon `apikey` header göndərir, amma bəzi Supabase versiyalarında `Authorization: Bearer <anon>` də lazımdır; bu halda `app/main.py`-də header əlavə edilməlidir. `service_role` yalnız server secret-dir.

## 4. Portable EXE
GitHub Actions > `Build Windows Portable EXE` > Run workflow. Artifacts bölməsindən ZIP yükləyin, çıxarın, `IT-Diagnostic-Pro.exe` və `config.json`-u eyni qovluqda saxlayın. Windows 7 üçün Python 3.8 / PyInstaller 5.13.2 istifadə olunur; Windows 7 SP1 və uyğun sistem yeniləmələri tələb oluna bilər. Windows 7 real cihazda test edilmədən dəstək zəmanəti vermək olmaz.

## 5. İlk sınaq
EXE-ni öz test kompüterinizdə açın, məlumatları yazın, diaqnostika edin və əvvəlcə JSON saxlayın. Məlumatları yoxlayın, sonra təşkilat kodu ilə Supabase-ə göndərin. Admin paneldə daxil olub son skanı və CSV-ni yoxlayın. OS yeniləndikdə SMBIOS UUID dəyişməyibsə eyni cihaz kimi görünəcək; anakart dəyişməsi və ya qeyri-unikal UUID olduqda manual birləşdirmə lazım ola bilər.

## Məhdudiyyətlər
Windows 7-də bəzi PowerShell cmdlet-ləri mövcud deyil; həmin sahələr boş qala bilər. Disk SMART, temperatur, VLAN, SNMP, switch portları və real-time online status bu V2 paketində tam monitorinq deyil. Admin panel **son skan vəziyyətini** göstərir, canlı 24/7 agent deyil. Lokal HTML `file://` ilə deyil, GitHub Pages HTTPS üzərindən açılmalıdır.
