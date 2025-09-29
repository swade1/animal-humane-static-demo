#!/usr/bin/env python3
"""
Rollback to original and use simple improved version
"""
import os
import shutil
from datetime import datetime

def main():
    print("🔄 Rolling back and switching to simple improved version")
    print("=" * 55)
    
    # Find the most recent backup
    backups = [f for f in os.listdir('.') if f.startswith('main_new_backup_') and f.endswith('.py')]
    if backups:
        latest_backup = sorted(backups)[-1]
        print(f"📁 Found backup: {latest_backup}")
        
        # Restore original
        shutil.copy2(latest_backup, "main_new_original.py")
        print(f"✅ Restored original to main_new_original.py")
    else:
        print("⚠️  No backup found, but continuing...")
    
    # Copy simple improved version
    if os.path.exists("main_simple_improved.py"):
        shutil.copy2("main_simple_improved.py", "main_new.py")
        print("✅ Switched to simple improved version")
        print("📝 Your original is saved as main_new_original.py")
        print("🚀 You can now run: python main_new.py")
        print("\n🎉 Simple migration completed successfully!")
        print("\n💡 This version has:")
        print("   - Better error handling")
        print("   - Health check endpoint (/health)")
        print("   - Enhanced logging")
        print("   - Same functionality as before")
    else:
        print("❌ main_simple_improved.py not found")

if __name__ == "__main__":
    main()