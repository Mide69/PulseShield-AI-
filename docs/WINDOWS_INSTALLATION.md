# Quick Installation Guide - Windows

## Install All Tools (30 minutes)

### Step 1: Install Docker Desktop (5 minutes)

1. **Download:**
   - Go to: https://www.docker.com/products/docker-desktop
   - Click "Download for Windows"

2. **Install:**
   - Run the installer
   - Check "Use WSL 2 instead of Hyper-V"
   - Click "Ok"
   - Restart computer when prompted

3. **Verify:**
   ```powershell
   docker --version
   # Should show: Docker version 24.x.x
   ```

---

### Step 2: Install AWS CLI (3 minutes)

1. **Download and Install:**
   ```powershell
   # Download installer
   msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
   ```
   
   Or manually:
   - Go to: https://aws.amazon.com/cli/
   - Download Windows installer
   - Run and install

2. **Verify:**
   ```powershell
   aws --version
   # Should show: aws-cli/2.x.x
   ```

---

### Step 3: Install kubectl (2 minutes)

1. **Download:**
   ```powershell
   curl.exe -LO "https://dl.k8s.io/release/v1.28.0/bin/windows/amd64/kubectl.exe"
   ```

2. **Move to System Path:**
   ```powershell
   # Move to Windows directory
   move kubectl.exe C:\Windows\System32\
   ```

3. **Verify:**
   ```powershell
   kubectl version --client
   # Should show: Client Version: v1.28.x
   ```

---

### Step 4: Install Helm (2 minutes)

⚠️ **IMPORTANT: Run PowerShell as Administrator** - Right-click PowerShell and select "Run as Administrator"

**Option A: Using Chocolatey (Recommended)**
```powershell
# Install Chocolatey first (if not installed)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install Helm
choco install kubernetes-helm -y
```

**If Chocolatey Installation Fails:**

If you get an error like "Unable to obtain lock file access", follow these steps:

1. **Backup existing Chocolatey (if any):**
   ```powershell
   # Create backup
   $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
   Copy-Item -Path "C:\ProgramData\chocolatey" -Destination "C:\Backup\chocolatey_backup_$timestamp" -Recurse -Force
   ```

2. **Remove broken Chocolatey installation:**
   ```powershell
   Remove-Item -Path "C:\ProgramData\chocolatey" -Recurse -Force
   ```

3. **Reinstall Chocolatey:**
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

4. **Reinstall packages:**
   ```powershell
   choco install kubernetes-helm -y
   ```

5. **Clean up backup (optional):**
   ```powershell
   # Only delete backup after confirming everything works
   Remove-Item -Path "C:\Backup\chocolatey_backup_*" -Recurse -Force
   ```

**Upgrading Chocolatey:**
```powershell
# To upgrade Chocolatey itself to the latest version
choco upgrade chocolatey -y
```

**Option B: Manual Download**
1. Go to: https://github.com/helm/helm/releases
2. Download `helm-v3.x.x-windows-amd64.zip`
3. Extract and move `helm.exe` to `C:\Windows\System32\`

**Verify:**
```powershell
helm version
# Should show: version.BuildInfo{Version:"v3.x.x"}
```

---

### Step 5: Install Terraform (2 minutes)

**Option A: Using Chocolatey**
```powershell
choco install terraform -y
```

**Option B: Manual Download**
1. Go to: https://www.terraform.io/downloads
2. Download Windows 64-bit
3. Extract and move `terraform.exe` to `C:\Windows\System32\`

**Verify:**
```powershell
terraform --version
# Should show: Terraform v1.x.x
```

---

### Step 6: Install Git (3 minutes)

1. **Download:**
   - Go to: https://git-scm.com/download/win
   - Download installer

2. **Install:**
   - Run installer
   - Use default settings
   - Click "Next" through all options

3. **Verify:**
   ```powershell
   git --version
   # Should show: git version 2.x.x
   ```

---

### Step 7: Install VSCode (Optional - 3 minutes)

1. **Download:**
   - Go to: https://code.visualstudio.com/
   - Click "Download for Windows"

2. **Install:**
   - Run installer
   - Check "Add to PATH"
   - Install

3. **Verify:**
   ```powershell
   code --version
   ```

---

## Verification Checklist

Run all these commands in PowerShell:

```powershell
# Check all installations
docker --version
aws --version
kubectl version --client
helm version
terraform --version
git --version
code --version  # If installed
```

**Expected Output:**
```
Docker version 24.x.x
aws-cli/2.x.x
Client Version: v1.28.x
version.BuildInfo{Version:"v3.x.x"}
Terraform v1.x.x
git version 2.x.x
1.x.x
```

---

## Troubleshooting

### Docker Desktop won't start
- Enable WSL2: `wsl --install`
- Restart computer
- Enable virtualization in BIOS

### "Command not found" errors
- Close and reopen PowerShell
- Check if tool is in PATH: `$env:Path`
- Restart computer

### Permission errors
- Run PowerShell as Administrator
- Right-click PowerShell → "Run as Administrator"

### Chocolatey Lock File Errors
**Error:** "Unable to obtain lock file access on 'C:\ProgramData\chocolatey\lib\...'"

**Solution:**
1. Run PowerShell **as Administrator** (right-click → "Run as Administrator")
2. Follow the steps in Step 4 under "If Chocolatey Installation Fails"
3. Delete lock file manually if needed:
   ```powershell
   Remove-Item -Path "C:\ProgramData\chocolatey\lib-bad" -Recurse -Force -ErrorAction SilentlyContinue
   ```
4. Close any open PowerShell windows and try installation again

### Helm Not Found After Installation
- Make sure you ran PowerShell as Administrator
- Close ALL PowerShell windows and open a new one
- Verify installation: `helm version`
- If still not found, use manual installation (Option B)

---

## Next Steps

After installing all tools:

1. **Clone the repository:**
   ```powershell
   cd C:\Users\YourName\Documents
   git clone https://github.com/your-username/pulseshield-ai.git
   cd pulseshield-ai
   ```

2. **Open in VSCode:**
   ```powershell
   code .
   ```

3. **Follow the deployment guide:**
   - Open `docs/COMPLETE_DEPLOYMENT_GUIDE.md`
   - Start from "Local Development" section

---

## Quick Reference

| Tool | Purpose | Command to Check |
|------|---------|------------------|
| Docker Desktop | Run containers locally | `docker --version` |
| AWS CLI | Talk to AWS | `aws --version` |
| kubectl | Manage Kubernetes | `kubectl version --client` |
| Helm | Deploy apps to K8s | `helm version` |
| Terraform | Create infrastructure | `terraform --version` |
| Git | Clone repository | `git --version` |
| VSCode | Edit code | `code --version` |

---

## All Done! ✅

You're ready to deploy PulseShield AI!

**Next:** Open `docs/COMPLETE_DEPLOYMENT_GUIDE.md` and start from "Local Development" section.
