# BackupUSSY v0.2.0 - Installation Guide

## 🚀 **Standalone Release - Zero Installation Required!**

This is a **standalone executable release** - no Python installation or dependency management needed!

---

## 📦 **Download and Setup**

### **Step 1: Download Release**
1. Download the `backupussy-v0.2.0-standalone.zip` from GitHub releases
2. Extract to your desired location (e.g., `C:\Tools\BackupUSSY\`)
3. That's it! No installation required.

### **Step 2: Verify Contents**
Extracted folder should contain:
```
backupussy-v0.2.0/
├── backupussy-v0.2.0.exe     # Main executable (31MB)
├── README.md                  # Complete documentation 
├── CLI_README.md             # Command-line reference
├── QUICKSTART.md             # Quick start guide
├── RELEASE_NOTES.md          # This release information
├── INSTALL.md                # Installation guide (this file)
├── LICENSE                   # GPL v3 license
└── backupussy.conf.example   # Configuration template
```

### **Step 3: Test Installation**
```cmd
# Open Command Prompt or PowerShell
cd C:\Tools\BackupUSSY\backupussy-v0.2.0

# Test the executable
backupussy-v0.2.0.exe --help

# Start interactive menu
backupussy-v0.2.0.exe menu
```

---

## ⚡ **Quick Start Options**

### **Option 1: Interactive Menu (Recommended)**
```cmd
backupussy-v0.2.0.exe menu
```
- Perfect for beginners
- Visual navigation with menus
- Guided workflows
- Built-in help and examples

### **Option 2: Wizard Mode (Best for First Time)**
```cmd
backupussy-v0.2.0.exe menu --mode wizard
```
- Step-by-step setup assistance
- Automated configuration generation
- Hardware detection and testing
- Complete guided first archive

### **Option 3: Direct CLI (Advanced Users)**
```cmd
# Check system status
backupussy-v0.2.0.exe status

# Create test archive (dry run)
backupussy-v0.2.0.exe archive create C:\MyData --dry-run
```

---

## 🛡️ **Security and Permissions**

### **Windows Permissions**
- **Standard User**: Works for most operations
- **Administrator**: Required for tape device access
- **Windows Defender**: May flag executable initially (normal for bundled Python apps)

### **Tape Device Access**
```cmd
# Test device access (safe)
backupussy-v0.2.0.exe status devices

# If no devices found, may need administrator rights
# Right-click Command Prompt → "Run as administrator"
```

### **Firewall and Antivirus**
- **No network access required** - BackupUSSY works offline
- **No registry modifications** - completely portable
- **No installation footprint** - runs from any location

---

## 📁 **Configuration Setup**

### **Auto Configuration (Recommended)**
```cmd
# Generate default configuration
backupussy-v0.2.0.exe manage config create

# Edit configuration if needed
notepad backupussy.conf
```

### **Manual Configuration**
```cmd
# Copy example configuration
copy backupussy.conf.example backupussy.conf

# Edit with your preferred editor
```

### **Configuration Locations**
BackupUSSY looks for config files in this order:
1. `./backupussy.conf` (same directory as executable)
2. `%APPDATA%\BackupUSSY\backupussy.conf`
3. `%USERPROFILE%\.backupussy\config`

---

## 🔧 **Hardware Setup**

### **LTO Tape Drive Requirements**
- **Supported**: LTO-4, LTO-5, LTO-6, LTO-7, LTO-8, LTO-9
- **Interface**: SAS, FC, USB (with proper drivers)
- **Drivers**: Windows-compatible LTO drivers required

### **Device Detection**
```cmd
# Check for tape drives
backupussy-v0.2.0.exe status devices

# Detailed hardware information
backupussy-v0.2.0.exe -vv status devices
```

### **No Tape Drive? No Problem!**
- **Dry-run mode**: Test all functionality without hardware
- **Simulation mode**: Practice with the interface
- **Educational use**: Learn backup strategies and workflows

---

## 🎯 **Usage Patterns**

### **For Desktop Users**
```cmd
# Always start with the menu
backupussy-v0.2.0.exe menu

# Use wizard for complex operations
backupussy-v0.2.0.exe menu --mode wizard
```

### **For IT Professionals**
```cmd
# Direct command line usage
backupussy-v0.2.0.exe archive create C:\CriticalData

# Automated scripting
backupussy-v0.2.0.exe --quiet --log-file backup.log archive create C:\Data
```

### **For System Administrators**
```cmd
# Batch operations
for /d %%i in (C:\Departments\*) do (
    backupussy-v0.2.0.exe archive create "%%i" --tape-name "DEPT-%%~ni"
)
```

---

## 📊 **Verification and Testing**

### **System Health Check**
```cmd
# Complete system status
backupussy-v0.2.0.exe status

# Dependency verification
backupussy-v0.2.0.exe status dependencies

# Database status
backupussy-v0.2.0.exe status database
```

### **Test Archive Creation**
```cmd
# Safe test with dry-run
backupussy-v0.2.0.exe archive create C:\TestData --dry-run

# Estimate archive size
backupussy-v0.2.0.exe archive estimate C:\TestData
```

---

## 🆘 **Troubleshooting**

### **Common Issues**

**Issue**: "Access denied" when accessing tape devices
```cmd
# Solution: Run as administrator
# Right-click Command Prompt → "Run as administrator"
backupussy-v0.2.0.exe status devices
```

**Issue**: "No tape devices found"
```cmd
# Check with verbose output
backupussy-v0.2.0.exe -vv status devices

# Verify Windows recognizes the device
devmgmt.msc  # Look under "Tape drives"
```

**Issue**: Executable won't run
```cmd
# Check Windows version (requires Windows 10/11)
ver

# Try running with verbose output
backupussy-v0.2.0.exe -vv --help
```

### **Getting Help**
```cmd
# Command-specific help
backupussy-v0.2.0.exe COMMAND --help

# Verbose output for debugging
backupussy-v0.2.0.exe -vv status

# Generate diagnostic information
backupussy-v0.2.0.exe status > system-info.txt
```

---

## 🚀 **Ready to Go!**

You're now ready to use BackupUSSY v0.2.0! Start with:

```cmd
backupussy-v0.2.0.exe menu --mode wizard
```

The wizard will guide you through everything else! 🎉

---

## 📚 **Next Steps**

1. **Read the documentation**: `README.md` has comprehensive examples
2. **Try the CLI commands**: `CLI_README.md` lists all available commands
3. **Configure your system**: Set up tapes, devices, and backup policies
4. **Create your first archive**: Start with a small test directory
5. **Explore advanced features**: Search, recovery, and management tools

**Welcome to professional LTO tape backup with BackupUSSY!** 🏆

