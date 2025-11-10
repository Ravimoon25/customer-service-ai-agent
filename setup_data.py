"""
Script to generate synthetic data and prepare the system
Run this first before starting the Streamlit app
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from scripts.generate_data import generate_synthetic_data
from config.config import Config

def main():
    print("="*70)
    print("SETTING UP CUSTOMER SERVICE AI AGENT SYSTEM")
    print("="*70)
    
    # Create data directory if it doesn't exist
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    print(f"✓ Created data directory: {Config.DATA_DIR}")
    
    # Generate synthetic data
    print("\nGenerating synthetic customer service data...")
    df = generate_synthetic_data()
    
    # Save to CSV
    df.to_csv(Config.SYNTHETIC_DATA_PATH, index=False)
    print(f"✓ Generated {len(df)} customer service cases")
    print(f"✓ Saved to: {Config.SYNTHETIC_DATA_PATH}")
    
    # Show category breakdown
    print("\n" + "="*70)
    print("CATEGORY BREAKDOWN")
    print("="*70)
    category_counts = df['category'].value_counts()
    for category, count in category_counts.items():
        print(f"  {category.replace('_', ' ').title()}: {count}")
    
    print("\n" + "="*70)
    print("SETUP COMPLETE!")
    print("="*70)
    print("\nYou can now run the Streamlit app with:")
    print("  streamlit run app.py")
    print()

if __name__ == "__main__":
    main()
