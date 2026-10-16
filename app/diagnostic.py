import os,sys,json,subprocess,datetime,platform,socket,uuid,re
from pathlib import Path

def powershell(script):
    try:
        p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-EncodedCommand',__import__('base64').b64encode(script.encode('utf-16le')).decode('ascii')],capture_output=True,text=True,timeout=110,encoding='utf-8-sig',errors='replace',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if p.returncode: return {'error':(p.stderr.strip() or p.stdout.strip())[:1000]}
        return json.loads(__import__('base64').b64decode(p.stdout.strip()).decode('utf-8-sig'))
    except Exception as e:return {'error':str(e)}

def device_identity():
    # Persist across OS upgrades when app folder is retained; hardware UUID is only a fallback.
    import hashlib
    machine = powershell("(Get-WmiObject Win32_ComputerSystemProduct).UUID | ConvertTo-Json -Compress")
    ident = machine if isinstance(machine,str) and machine.strip('\"0- ').strip() else socket.gethostname()
    return hashlib.sha256(('ITDP-v2:'+ident).encode('utf-8')).hexdigest()[:40]

def scan():
    script=r'''
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$ErrorActionPreference='SilentlyContinue'
function Wmi($class,$namespace='root/cimv2') { Get-WmiObject -Class $class -Namespace $namespace -ErrorAction SilentlyContinue }
function TryCmd($name,$args) { if(Get-Command $name -ErrorAction SilentlyContinue){ & $name @args } }

function Items($x){ @($x | Where-Object { $null -ne $_ }) }
$cs=Wmi Win32_ComputerSystem
$os=Wmi Win32_OperatingSystem
$cpu=Wmi Win32_Processor
$bios=Wmi Win32_BIOS
$board=Wmi Win32_BaseBoard
$ram=Wmi Win32_PhysicalMemory
$disks=Wmi Win32_DiskDrive
$volumes=Wmi Win32_LogicalDisk -Filter 'DriveType=3'
$gpu=Wmi Win32_VideoController
$net=Wmi Win32_NetworkAdapterConfiguration -Filter 'IPEnabled=True'
$adapters=Wmi Win32_NetworkAdapter -Filter 'PhysicalAdapter=True'
$mon=Wmi WmiMonitorID root/wmi
$apps=@()
foreach($path in @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*')){
 $apps+=Get-ItemProperty $path | Where-Object {$_.DisplayName} | Select-Object DisplayName,DisplayVersion,Publisher,InstallDate
}
$apps=@($apps | Sort-Object DisplayName,DisplayVersion -Unique)
$av=Wmi AntiVirusProduct root/SecurityCenter2 | Select-Object displayName,productState,pathToSignedProductExe
$defender=TryCmd Get-MpComputerStatus @() | Select-Object AMServiceEnabled,AntivirusEnabled,RealTimeProtectionEnabled,AntivirusSignatureVersion,AntivirusSignatureLastUpdated
$profiles=TryCmd Get-NetConnectionProfile @() | Select-Object Name,InterfaceAlias,NetworkCategory,IPv4Connectivity,IPv6Connectivity
$ipconfig=TryCmd Get-NetIPConfiguration @() | Select-Object InterfaceAlias,IPv4Address,IPv4DefaultGateway,DNSServer
$fw=TryCmd Get-NetFirewallProfile @() | Select-Object Name,Enabled
$boot=TryCmd Confirm-SecureBootUEFI @()
$bitlocker=TryCmd Get-BitLockerVolume @() | Select-Object MountPoint,ProtectionStatus,VolumeStatus
$physical=TryCmd Get-PhysicalDisk @() | Select-Object FriendlyName,MediaType,HealthStatus,OperationalStatus,Size
$health=@()
if(Get-Command Get-StorageReliabilityCounter -ErrorAction SilentlyContinue){
 foreach($pd in @(Get-PhysicalDisk -ErrorAction SilentlyContinue)){
  try { $health+= @(Get-StorageReliabilityCounter -PhysicalDisk $pd -ErrorAction Stop | Select-Object DeviceId,Temperature,ReadErrorsTotal,WriteErrorsTotal,Wear) } catch {}
 }
}
$logon=(Wmi Win32_OperatingSystem).LastBootUpTime
$dnsTest=$false; $internet=$false; $gateway=$false
$diskMedia=@(); foreach($d in @($disks)) { $diskMedia+= [pscustomobject]@{Index=$d.Index; Model=$d.Model; InterfaceType=$d.InterfaceType; MediaType=$d.MediaType; Size=$d.Size} }

try{$dnsTest=[bool]([System.Net.Dns]::GetHostAddresses('www.microsoft.com').Count -gt 0)}catch{}
try{$req=[System.Net.HttpWebRequest]::Create('https://www.microsoft.com');$req.Timeout=3500;$req.Method='HEAD';$resp=$req.GetResponse();$internet=$true;$resp.Close()}catch{}
try{$gw=($net | Where-Object {$_.DefaultIPGateway} | Select-Object -First 1).DefaultIPGateway[0];if($gw){$gateway=Test-Connection -ComputerName $gw -Count 1 -Quiet}}catch{}
[pscustomobject]@{
 computer=$cs | Select-Object Name,Manufacturer,Model,Domain,PartOfDomain,UserName,TotalPhysicalMemory,PCSystemType
 os=$os | Select-Object Caption,Version,BuildNumber,OSArchitecture,SerialNumber,InstallDate,LastBootUpTime
 cpu=Items($cpu | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed,LoadPercentage)
 bios=$bios | Select-Object Manufacturer,SMBIOSBIOSVersion,SerialNumber,ReleaseDate
 motherboard=$board | Select-Object Manufacturer,Product,SerialNumber
 ram=Items($ram | Select-Object Manufacturer,Capacity,Speed,PartNumber,SerialNumber)
 disks=Items($disks | Select-Object Model,SerialNumber,Size,InterfaceType,MediaType,Index)
 physical_disks=Items($physical)
 disk_health=Items($health)
 volumes=Items($volumes | Select-Object DeviceID,VolumeName,Size,FreeSpace,FileSystem)
 gpu=Items($gpu | Select-Object Name,DriverVersion,AdapterRAM)
 monitors=Items($mon | Select-Object InstanceName,ManufacturerName,UserFriendlyName,SerialNumberID)
 network=Items($net | Select-Object Description,MACAddress,IPAddress,IPSubnet,DefaultIPGateway,DNSServerSearchOrder,DHCPEnabled,DHCPServer)
 adapters=Items($adapters | Select-Object Name,NetConnectionID,MACAddress,Speed,NetEnabled)
 profiles=Items($profiles)
 programs=Items($apps)
 antivirus=Items($av)
 defender=$defender
 firewall=Items($fw)
 bitlocker=Items($bitlocker)
 secure_boot=$boot
 connectivity=@{dns=$dnsTest;internet=$internet;gateway_ping=$gateway;lan_adapter=[bool](@($net).Count -gt 0)}
 } | ConvertTo-Json -Depth 9 -Compress | ForEach-Object { [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($_)) }
'''
    data=powershell(script)
    return {'schema_version':2,'scanned_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostname':socket.gethostname(),'device_id':device_identity(),'platform':platform.platform(),'data':data}
