#!/usr/bin/env python3
"""
Test script to generate diff reports manually
"""
import os
from scheduler.diff_analyzer import DiffAnalyzer

def main():
    print("🧪 Testing Diff Report Generation")
    print("=" * 35)
    
    # Create analyzer with reports going to Docker directory
    output_dir = "deployment/docker/diff_reports"
    os.makedirs(output_dir, exist_ok=True)
    
    analyzer = DiffAnalyzer(output_dir=output_dir)
    
    print(f"📁 Reports will be saved to: {output_dir}")
    
    # Generate reports
    results = analyzer.analyze_differences()
    
    if results:
        print("✅ Reports generated successfully!")
        print(f"📊 Summary: {results['summary']}")
        
        # List generated files
        print(f"\n📄 Generated files:")
        for file in os.listdir(output_dir):
            if file.endswith(('.json', '.txt', '.csv')):
                file_path = os.path.join(output_dir, file)
                size = os.path.getsize(file_path)
                print(f"   - {file} ({size} bytes)")
    else:
        print("❌ No reports generated - might not have enough data for comparison")

if __name__ == "__main__":
    main()