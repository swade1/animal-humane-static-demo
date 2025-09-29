#!/usr/bin/env python3
"""
Quick migration script - just run it to migrate to improved architecture
"""
import os
import shutil
from datetime import datetime

def main():
    print("🔄 Quick Migration to Improved Architecture")
    print("=" * 45)
    
    # Check if main_improved.py exists
    if not os.path.exists("main_improved.py"):
        print("❌ main_improved.py not found")
        print("💡 Make sure you're in the animal-humane directory")
        return
    
    # Backup current main_new.py if it exists
    if os.path.exists("main_new.py"):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"main_new_backup_{timestamp}.py"
        shutil.copy2("main_new.py", backup_name)
        print(f"✅ Backed up main_new.py to {backup_name}")
    
    # Copy improved version
    shutil.copy2("main_improved.py", "main_new.py")
    print("✅ Switched to improved architecture")
    print("📝 Your original main_new.py has been backed up")
    print("🚀 You can now run: python main_new.py")
    print("\n🎉 Migration completed successfully!")

if __name__ == "__main__":
    main()