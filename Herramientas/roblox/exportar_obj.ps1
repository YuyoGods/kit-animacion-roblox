# Exporta a .obj lo que haya en el Workspace de Roblox Studio (Archivo > Exportar como .obj),
# manejando el menu y el dialogo de Windows solo. Usar despues de aislar el personaje con
# studio_personajes.luau (_G.CL_isolate), porque "Exportar como .obj" exporta TODO el lugar.
#
# Uso (PowerShell, desde la raiz del kit):
#   powershell -STA -File Herramientas\roblox\exportar_obj.ps1 -Ruta "C:\...\Personajes\Pueblo_NPC\Juan\Juan.obj" [-Titulo "Place1"]
# -Titulo: parte del titulo de la ventana de Studio (si hay varias abiertas). No sobrescribe archivos.
# -Espera N: deja Studio al frente N segundos antes de exportar (2026-11-11). Studio pinta la ropa clasica y la cara en la
#   textura del cuerpo poco a poco y solo mientras dibuja: en personajes recien creados (copias R6->R15) usar -Espera 25
#   y revisar que el .mtl tenga la textura del cuerpo (916x568); si no, borrar y repetir.
param([Parameter(Mandatory = $true)][string]$Ruta, [string]$Titulo = "", [int]$Espera = 0)

if (Test-Path $Ruta) { "YA EXISTE (no se sobrescribe): $Ruta"; exit 1 }
$dir = Split-Path $Ruta
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }

Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes, System.Windows.Forms
Add-Type @"
using System; using System.Runtime.InteropServices;
public class KitW { [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h); [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n); }
"@ -ErrorAction SilentlyContinue
$A = [System.Windows.Automation.AutomationElement]; $C = [System.Windows.Automation.TreeScope]
function P($prop, $val) { New-Object System.Windows.Automation.PropertyCondition($prop, $val) }

$proc = Get-Process RobloxStudioBeta -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowTitle -like "*Roblox Studio*" -and $_.MainWindowTitle -like "*$Titulo*" -and $_.MainWindowTitle -ne "Roblox Studio" } |
    Select-Object -First 1
if (-not $proc) { "ERROR: no encontre una ventana de Roblox Studio con un lugar abierto"; exit 1 }
$root = $A::FromHandle($proc.MainWindowHandle)
if ($Espera -gt 0) { [KitW]::ShowWindow($proc.MainWindowHandle, 9) | Out-Null; [KitW]::SetForegroundWindow($proc.MainWindowHandle) | Out-Null; Start-Sleep -Seconds $Espera }

$dlg = $root.FindFirst($C::Children, (P $A::ClassNameProperty '#32770'))
if (-not $dlg) {
    $it = $null
    for ($t = 0; $t -lt 6 -and -not $it; $t++) {
        [KitW]::SetForegroundWindow($proc.MainWindowHandle) | Out-Null
        $m = $root.FindFirst($C::Descendants, (P $A::NameProperty 'Archivo'))
        if (-not $m) { $m = $root.FindFirst($C::Descendants, (P $A::NameProperty 'File')) }
        $ec = $m.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern)
        try { $ec.Collapse() } catch {}
        Start-Sleep -Milliseconds 300
        $ec.Expand()
        Start-Sleep -Milliseconds (700 + 300 * $t)
        $it = $A::RootElement.FindFirst($C::Descendants, (P $A::NameProperty 'Exportar como .obj'))
        if (-not $it) { $it = $A::RootElement.FindFirst($C::Descendants, (P $A::NameProperty 'Export as .obj')) }
    }
    if (-not $it) { "ERROR: no encontre 'Exportar como .obj' en el menu Archivo"; exit 1 }
    $it.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
    for ($k = 0; $k -lt 40 -and -not $dlg; $k++) { Start-Sleep -Milliseconds 300; $dlg = $root.FindFirst($C::Children, (P $A::ClassNameProperty '#32770')) }
}
if (-not $dlg) { "ERROR: no aparecio el dialogo de guardar"; exit 1 }
Start-Sleep -Milliseconds 700
[System.Windows.Forms.Clipboard]::SetText($Ruta)
[KitW]::SetForegroundWindow([IntPtr]$dlg.Current.NativeWindowHandle) | Out-Null
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait("%n")        # Alt+N = "Nombre de archivo"
Start-Sleep -Milliseconds 200
[System.Windows.Forms.SendKeys]::SendWait("^a^v")
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
for ($k = 0; $k -lt 20; $k++) { Start-Sleep -Milliseconds 300; $d2 = $root.FindFirst($C::Children, (P $A::ClassNameProperty '#32770')); if (-not $d2) { break } }
if ($d2) { "AVISO: sigue abierto un dialogo: '" + $d2.Current.Name + "'"; exit 1 }
$mtl = [IO.Path]::ChangeExtension($Ruta, ".mtl")
for ($k = 0; $k -lt 30 -and -not (Test-Path $mtl); $k++) { Start-Sleep -Milliseconds 500 }
Start-Sleep -Seconds 1
if (-not (Test-Path $Ruta)) { "ERROR: no se creo $Ruta"; exit 1 }
$g = (Select-String -Path $Ruta -Pattern "^g ").Count
"OK $Ruta  grupos=$g  png=$((Get-ChildItem $dir -Filter *.png).Count)"
