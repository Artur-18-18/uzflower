#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix mojibake encoding in handlers.py

The file was double-encoded: original UTF-8 bytes were interpreted as CP1252/ISO-8859-1
and then saved as UTF-8 again. We need to reverse this process.
"""

import codecs

# Read the file as raw bytes
with open(r'app\telegram_bot\handlers.py', 'rb') as f:
    data = f.read()

# First decode as UTF-8 to get the mojibake string
mojibake = data.decode('utf-8')

# The mojibake pattern suggests UTF-8 bytes were interpreted as CP1252
# Let's try to reverse it
print("Trying to decode mojibake...")

# Method: encode as CP1252 to get original bytes, then decode as UTF-8
try:
    # Encode the mojibake as latin-1 (ISO-8859-1) to get bytes back
    # This works because latin-1 maps code points 0-255 directly to bytes
    original_bytes = mojibake.encode('latin-1')
    
    # Now decode those bytes as UTF-8
    correct_text = original_bytes.decode('utf-8')
    
    print("SUCCESS with latin-1!")
    print("\nFirst 800 characters:")
    print(correct_text[:800])
    
    # Save with proper UTF-8 encoding
    with open(r'app\telegram_bot\handlers.py', 'w', encoding='utf-8') as f:
        f.write(correct_text)
    print("\n✓ File saved successfully with proper UTF-8 encoding!")
    
except UnicodeEncodeError as e:
    print(f"latin-1 failed: {e}")
    
    # Try CP1252 (Windows Western European)
    try:
        original_bytes = mojibake.encode('cp1252')
        correct_text = original_bytes.decode('utf-8')
        print("SUCCESS with cp1252!")
        print(correct_text[:800])
        with open(r'app\telegram_bot\handlers.py', 'w', encoding='utf-8') as f:
            f.write(correct_text)
        print("\n✓ File saved successfully!")
    except Exception as e2:
        print(f"cp1252 also failed: {e2}")
        
        # Try the raw bytes approach - maybe it's just UTF-8 that needs proper handling
        print("\nTrying direct UTF-8 with error handling...")
        try:
            correct_text = data.decode('utf-8')
            # Use codecs to decode the mojibake
            fixed = codecs.decode(correct_text, 'cp1252')
            print(f"Codecs approach result: {fixed[:200]}")
        except Exception as e3:
            print(f"All methods failed: {e3}")
