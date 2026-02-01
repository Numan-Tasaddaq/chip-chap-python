# How to Extract Teli SDK from Working System

## Step 1: Locate SDK Files on Working System

Run these PowerShell commands on the **camera system** (where old C++ app works):

```powershell
# Find Teli SDK installation
Get-ChildItem -Path "C:\Program Files" -Recurse -Filter "*Teli*" -Directory -ErrorAction SilentlyContinue
Get-ChildItem -Path "C:\Program Files (x86)" -Recurse -Filter "*Teli*" -Directory -ErrorAction SilentlyContinue

# Find USB3 Vision DLLs
Get-ChildItem -Path "C:\" -Recurse -Filter "TeliU3vApi.dll" -ErrorAction SilentlyContinue | Select-Object FullName
Get-ChildItem -Path "C:\" -Recurse -Filter "*USB3CT*.dll" -ErrorAction SilentlyContinue | Select-Object FullName
Get-ChildItem -Path "C:\" -Recurse -Filter "*USB4CT*.dll" -ErrorAction SilentlyContinue | Select-Object FullName

# Find iTrue frame grabber DLLs
Get-ChildItem -Path "C:\" -Recurse -Filter "iTrue_USB*.dll" -ErrorAction SilentlyContinue | Select-Object FullName
```

**Common locations:**
- `C:\Program Files\Teli\USB3Vision\`
- `C:\Program Files\Toshiba Teli\`
- `C:\Program Files (x86)\Teli\`
- Old app folder: `C:\iTrueVision\` or where ChipCapacitor.exe is located
- System folder: `C:\Windows\System32\` (driver DLLs)

---

## Step 2: Required Files to Copy

Create this folder structure on your development machine:

```
E:\Office Work\chip-chap-python\
├── sdk/
│   ├── teli/
│   │   ├── TeliU3vApi.dll           # Main SDK DLL
│   │   ├── TeliU3vApi.lib           # Import library (optional)
│   │   ├── TeliU3vApi.h             # Header file (for reference)
│   │   └── ...other support DLLs
│   └── itrue/
│       ├── iTrue_USB3CT.dll         # Frame grabber for USB3CT cameras
│       ├── iTrue_USB4CT.dll         # Frame grabber for USB4CT cameras
│       └── ...any other iTrue DLLs
```

### Minimum Required Files:

1. **Teli SDK Core:**
   - `TeliU3vApi.dll` (main API)
   - `TeliU3vApi.h` (header, for reference)
   - Any dependent DLLs (check DLL dependencies)

2. **Frame Grabber DLLs:**
   - `iTrue_USB3CT.dll` (for BU030 mono cameras)
   - `iTrue_USB4CT.dll` (for BU040 color cameras)

3. **Support Files:**
   - Any `.xml` or `.dat` files in the SDK folder
   - Camera driver files if needed

---

## Step 3: Copy Files from Working System

### Option A: Manual Copy (if you have physical access)

1. Insert USB drive into camera system
2. Copy entire folders:
   ```
   C:\Program Files\Teli\USB3Vision\  → USB:\teli-sdk\
   {Old App Folder}\iTrue_USB*.dll    → USB:\itrue-dlls\
   ```
3. Move USB to development machine
4. Copy to `E:\Office Work\chip-chap-python\sdk\`

### Option B: Network Copy (if both machines on same network)

On development machine:
```powershell
# Map network drive to camera system (replace CAMERA_PC with actual name)
net use Z: \\CAMERA_PC\C$

# Copy Teli SDK
Copy-Item "Z:\Program Files\Teli\USB3Vision" -Destination "E:\Office Work\chip-chap-python\sdk\teli" -Recurse

# Copy iTrue DLLs (adjust path to where old app is)
Copy-Item "Z:\iTrueVision\*.dll" -Destination "E:\Office Work\chip-chap-python\sdk\itrue" -Filter "iTrue_USB*.dll"

# Disconnect
net use Z: /delete
```

### Option C: Remote Desktop Copy

1. RDP to camera system
2. Copy files to shared folder or cloud drive
3. Download to development machine

---

## Step 4: Check DLL Dependencies

After copying, verify DLL dependencies on development machine:

```powershell
cd "E:\Office Work\chip-chap-python\sdk\teli"

# Install Dependency Walker or use dumpbin (if you have Visual Studio)
dumpbin /dependents TeliU3vApi.dll

# Or use PowerShell to list imports
$dll = [System.Reflection.Assembly]::LoadFile("$(pwd)\TeliU3vApi.dll")
```

**Common dependencies you might need:**
- `msvcp140.dll` (Visual C++ 2015-2019 Runtime)
- `vcruntime140.dll`
- `api-ms-win-*.dll` (Windows API sets)

If missing, install **Visual C++ Redistributable 2015-2019**:
```powershell
# Download and install from Microsoft
Start-Process "https://aka.ms/vs/17/release/vc_redist.x64.exe"
```

---

## Step 5: Install Camera Drivers

Copy and install camera drivers from working system:

1. **Device Manager method:**
   - On camera system: Open Device Manager
   - Find camera under "Imaging Devices" or "Universal Serial Bus devices"
   - Right-click → Properties → Driver → Driver Details
   - Note driver file locations
   - Copy `.sys`, `.inf`, `.cat` files

2. **Driver installer method:**
   - Look for installer: `C:\Program Files\Teli\Drivers\`
   - Copy installer to development machine
   - Run installer as Administrator

---

## Step 6: Verify Extraction (Run on Camera System)

Create a test script to verify what's on the camera system:

```powershell
# Save as: check_camera_sdk.ps1

Write-Host "=== Teli SDK Check ===" -ForegroundColor Cyan

# 1. Find Teli installations
Write-Host "`n1. Teli SDK Directories:" -ForegroundColor Yellow
Get-ChildItem -Path "C:\Program Files" -Filter "*Teli*" -Directory -Recurse -ErrorAction SilentlyContinue | 
    Select-Object FullName, CreationTime

# 2. Find DLL files
Write-Host "`n2. Teli DLL Files:" -ForegroundColor Yellow
Get-ChildItem -Path "C:\" -Filter "TeliU3vApi.dll" -Recurse -ErrorAction SilentlyContinue | 
    Select-Object FullName, Length, LastWriteTime

# 3. Find iTrue frame grabber DLLs
Write-Host "`n3. iTrue Frame Grabber DLLs:" -ForegroundColor Yellow
Get-ChildItem -Path "C:\" -Filter "iTrue_USB*.dll" -Recurse -ErrorAction SilentlyContinue | 
    Select-Object FullName, Length

# 4. Check camera devices
Write-Host "`n4. Connected Camera Devices:" -ForegroundColor Yellow
Get-PnpDevice -Class "Image" | Where-Object {$_.Status -eq "OK"} | 
    Select-Object FriendlyName, InstanceId

# 5. Check old C++ app location
Write-Host "`n5. Old C++ Application:" -ForegroundColor Yellow
$possiblePaths = @(
    "C:\iTrueVision",
    "C:\Program Files\iTrue",
    "C:\Program Files (x86)\iTrue",
    "C:\ChipCapacitor",
    "C:\ChipResistor"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        Write-Host "  Found: $path" -ForegroundColor Green
        Get-ChildItem $path -Filter "*.dll" | Select-Object Name, Length
    }
}

# 6. Registry check
Write-Host "`n6. Registry Configuration:" -ForegroundColor Yellow
$regPath = "HKCU:\Software\iTrue\hardware"
if (Test-Path $regPath) {
    Write-Host "  Registry path exists: $regPath" -ForegroundColor Green
    Get-ItemProperty -Path $regPath | Format-List
} else {
    Write-Host "  Registry path NOT found: $regPath" -ForegroundColor Red
}

Write-Host "`n=== Check Complete ===" -ForegroundColor Cyan
Write-Host "Copy the files listed above to your development machine." -ForegroundColor Yellow
```

---

## Step 7: What to Do After Copying

Once you have the files on your development machine:

1. **Test DLL loading:**
   ```python
   import ctypes
   dll_path = r"E:\Office Work\chip-chap-python\sdk\teli\TeliU3vApi.dll"
   try:
       dll = ctypes.CDLL(dll_path)
       print("✓ DLL loaded successfully")
   except Exception as e:
       print(f"✗ Failed to load DLL: {e}")
   ```

2. **I will create Python wrapper** to interface with the DLL
3. **I will integrate** with the existing camera system
4. **I will add serial number matching** like the old C++ code

---

## Quick Checklist

- [ ] Located Teli SDK installation on camera system
- [ ] Found `TeliU3vApi.dll` location
- [ ] Found `iTrue_USB3CT.dll` and `iTrue_USB4CT.dll` locations  
- [ ] Copied all DLLs to development machine
- [ ] Copied any `.h` header files (for reference)
- [ ] Installed Visual C++ Redistributable on dev machine
- [ ] Verified DLL loads with ctypes test
- [ ] Ready for Python integration

---

## Common Issues & Solutions

**Issue 1: "DLL not found" error**
- Copy to `sdk/teli/` folder
- Add folder to system PATH
- Check dependencies with Dependency Walker

**Issue 2: "The specified module could not be found"**
- Missing Visual C++ Runtime
- Install VC++ Redistributable 2015-2019 x64

**Issue 3: "DLL load failed while importing"**  
- DLL is 32-bit but Python is 64-bit (or vice versa)
- Check with: `dumpbin /headers TeliU3vApi.dll | findstr machine`
- Use matching architecture

**Issue 4: Camera not detected**
- Drivers not installed on dev machine
- Copy and install driver from camera system
- Check Device Manager for camera device

---

## Next Steps

Once you have the files copied, let me know and I will:
1. ✅ Create Python wrapper for Teli SDK
2. ✅ Integrate with existing camera system
3. ✅ Add serial number matching
4. ✅ Apply camera settings to hardware
5. ✅ Test GRAB and LIVE with real cameras

**Run the PowerShell commands above on your camera system and share what you find!**
