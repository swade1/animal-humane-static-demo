#!/usr/bin/env python3
"""
Migration script to help transition from main_new.py to main_improved.py
"""
import os
import shutil
from datetime import datetime

def backup_current_main():
    """Backup the current main_new.py file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"main_new_backup_{timestamp}.py"
    
    if os.path.exists("main_new.py"):
        shutil.copy2("main_new.py", backup_name)
        print(f"✅ Backed up main_new.py to {backup_name}")
    else:
        print("⚠️  main_new.py not found")

def switch_to_improved():
    """Switch to using the improved main file"""
    if os.path.exists("main_improved.py"):
        # Backup current main_new.py
        backup_current_main()
        
        # Copy improved version
        shutil.copy2("main_improved.py", "main_new.py")
        print("✅ Switched to improved architecture")
        print("📝 Your original main_new.py has been backed up")
        print("🚀 You can now run: python main_new.py")
        return True
    else:
        print("❌ main_improved.py not found")
        return False

def rollback():
    """Rollback to the most recent backup"""
    # Find the most recent backup
    backups = [f for f in os.listdir('.') if f.startswith('main_new_backup_') and f.endswith('.py')]
    if backups:
        latest_backup = sorted(backups)[-1]
        shutil.copy2(latest_backup, "main_new.py")
        print(f"✅ Rolled back to {latest_backup}")
        return True
    else:
        print("❌ No backup files found")
        return False

def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = [
        'fastapi',
        'uvicorn',
        'elasticsearch',
        'pydantic',
        'requests'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("📦 Install with: pip install " + " ".join(missing))
        return False
    else:
        print("✅ All dependencies are available")
        return True

def main():
    print("🔄 Animal Humane API Migration Tool")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Check dependencies")
        print("2. Switch to improved architecture")
        print("3. Rollback to backup")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            check_dependencies()
        elif choice == '2':
            if check_dependencies():
                if switch_to_improved():
                    print("\n🎉 Migration completed successfully!")
                    print("You can now start your API with: python main_new.py")
                    break
            else:
                print("⚠️  Please install missing dependencies first")
        elif choice == '3':
            if rollback():
                print("\n🔄 Rollback completed successfully!")
                break
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main()
