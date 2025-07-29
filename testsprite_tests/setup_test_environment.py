#!/usr/bin/env python3
"""
Test Environment Setup Script for Legal Document Extractor
Creates test files and validates environment for TestSprite testing
"""

import os
import shutil
import json
from pathlib import Path

def setup_test_environment():
    """Setup test environment with actual PDF files"""
    
    # Define paths
    project_root = Path(__file__).parent.parent
    uploads_dir = project_root / "uploads"
    test_dir = project_root / "testsprite_tests" / "test_files"
    
    # Create test files directory
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Available PDF files in uploads directory
    pdf_files = [
        "anita_yuvraj_test.pdf",
        "Tej Karan - Jodhpur.pdf", 
        "Ravinder Kaur - UK.pdf",
        "file-1752733837504-630102423.pdf",
        "pdf-1752741187792-923217221.pdf",
        "pdf-1752741702340-847242573.pdf",
        "pdf-1752742087328-358145638.pdf",
        "pdf-1752742145103-849438816.pdf",
        "pdf-1752742323608-796495399.pdf"
    ]
    
    # Copy PDF files to test directory
    test_files = []
    for pdf_file in pdf_files:
        source_path = uploads_dir / pdf_file
        if source_path.exists():
            dest_path = test_dir / pdf_file
            shutil.copy2(source_path, dest_path)
            test_files.append(str(dest_path))
            print(f"✓ Copied {pdf_file} to test directory")
        else:
            print(f"✗ File not found: {pdf_file}")
    
    # Create test configuration
    test_config = {
        "test_files": test_files,
        "valid_pdf": test_files[0] if test_files else None,
        "large_pdf": test_files[1] if len(test_files) > 1 else None,
        "scanned_pdf": test_files[2] if len(test_files) > 2 else None,
        "uploads_directory": str(uploads_dir),
        "test_directory": str(test_dir)
    }
    
    # Save test configuration
    config_path = project_root / "testsprite_tests" / "test_config.json"
    with open(config_path, 'w') as f:
        json.dump(test_config, f, indent=2)
    
    print(f"\n✓ Test environment setup complete!")
    print(f"✓ Test configuration saved to: {config_path}")
    print(f"✓ Available test files: {len(test_files)}")
    
    return test_config

if __name__ == "__main__":
    setup_test_environment() 