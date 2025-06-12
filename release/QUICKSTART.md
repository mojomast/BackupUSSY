# BackupUSSY v0.2.0 - Quick Start Guide 🚀

**Standalone Command-Line Release** - No Python installation required!

## 🎯 **Instant Setup**

1. **Download**: Extract the `backupussy-v0.2.0.exe` from this release
2. **Run**: Double-click or run from command line
3. **Start**: Begin with the interactive menu system!

```cmd
# Interactive menu (recommended for beginners)
backupussy-v0.2.0.exe menu

# Direct command line usage
backupussy-v0.2.0.exe --help
```

---

## 🧙 **Wizard Mode** (Easiest Way to Start)

```cmd
backupussy-v0.2.0.exe menu --mode wizard
```

The wizard will guide you through:
- ✅ System setup and configuration
- ✅ Device detection and testing
- ✅ Your first archive creation
- ✅ Database management

---

## 📱 **Interactive Menu System**

```cmd
backupussy-v0.2.0.exe menu
```

**Available Menus:**
- 📦 **Archive Operations** - Create backups and estimates
- 🔄 **Recovery Operations** - Restore files and browse archives
- 🔍 **Search Operations** - Find files across all tapes
- ⚙️ **System Management** - Manage tapes and configuration
- 📊 **System Status** - Monitor drives and operations

---

## ⚡ **Quick Commands**

### System Status
```cmd
backupussy-v0.2.0.exe status
```

### Check Tape Devices
```cmd
backupussy-v0.2.0.exe status devices
```

### Create Your First Archive (Dry Run)
```cmd
backupussy-v0.2.0.exe archive create C:\MyData --dry-run
```

### Search for Files
```cmd
backupussy-v0.2.0.exe search "*.pdf"
```

---

## 🛡️ **Safety Features**

**Always test first with `--dry-run`:**
```cmd
backupussy-v0.2.0.exe archive create C:\MyData --dry-run
```

**Verbose output for troubleshooting:**
```cmd
backupussy-v0.2.0.exe -vv status
```

---

## 📋 **What's Included in This Release**

- ✅ **backupussy-v0.2.0.exe** - Standalone executable (31MB)
- ✅ **README.md** - Complete documentation
- ✅ **CLI_README.md** - Command-line reference
- ✅ **LICENSE** - GPL v3 license
- ✅ **backupussy.conf.example** - Configuration template
- ✅ **QUICKSTART.md** - This guide

---

## 🎯 **Common Use Cases**

### Desktop User (No Tape Drive)
```cmd
# Explore the interface safely
backupussy-v0.2.0.exe menu
# Choose "System Status" → "Device Status"
```

### Testing/Learning
```cmd
# Dry run everything
backupussy-v0.2.0.exe archive create C:\MyData --dry-run
backupussy-v0.2.0.exe --dry-run menu
```

### Production Use
```cmd
# Start with wizard mode
backupussy-v0.2.0.exe menu --mode wizard

# Create configuration
backupussy-v0.2.0.exe manage config create

# Verify hardware
backupussy-v0.2.0.exe status devices
```

---

## 🆘 **Need Help?**

- **Command Help**: `backupussy-v0.2.0.exe COMMAND --help`
- **Verbose Output**: Add `-vv` to any command
- **Safe Mode**: Add `--dry-run` to test without changes
- **Documentation**: Read `README.md` and `CLI_README.md`

---

## ⚡ **Pro Tips**

1. **Start with the menu system** - It's much easier than memorizing commands
2. **Use dry-run mode** until you're comfortable
3. **Check device status first** - Know your hardware before archiving
4. **Try wizard mode** - It guides you through complex workflows
5. **Read the full docs** - `README.md` has comprehensive examples

---

**🎉 Ready to backup like a pro! The terminal interface gives you enterprise-grade power with user-friendly guidance.**

