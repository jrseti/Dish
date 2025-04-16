"""
File: fix_kicad_symbols.py

Author: Jon Richards
Date: April 16, 2025

Description: For each symbol in a library make sure it has the required properties.
             This script will add the properties if they are missing.
"""

import os
import shutil
from pathlib import Path

from kiutils.symbol import SymbolLib
from kiutils.items.common import Property, Effects


# Define required properties and their default values
REQUIRED_PROPERTIES = {
    "Reference": {"value": "U", "hide": False},
    "Value": {"value": "", "hide": False},
    "Footprint": {"value": "", "hide": True},
    "Datasheet": {"value": "", "hide": True},
    "Description": {"value": "", "hide": True},
    "Package": {"value": "", "hide": True},
    "MF": {"value": "", "hide": True},
    "MPN": {"value": "", "hide": True},
    "DIS": {"value": "", "hide": True},
    "DPN": {"value": "", "hide": True},
    "Purchase_URL": {"value": "", "hide": True},
    "Price": {"value": "0.00", "hide": True},
    "Note": {"value": "", "hide": True},
}

def backup_file(filepath):
    """Backup the specified file by creating a copy with a new name.
    The new name will include a counter to avoid overwriting existing backups.  
    Args:
        filepath (str): The path to the file to be backed up.
    Returns:
        str: The path to the backup file.
    Raises:
        FileNotFoundError: If the specified file does not exist.
    """
    # Ensure we are working with a full Path object
    original = Path(filepath)
    if not original.is_file():
        raise FileNotFoundError(f"File not found: {filepath}")

    # Define backup directory
    backup_dir = original.parent / "backup"
    backup_dir.mkdir(exist_ok=True)

    # Get base filename and extension
    stem = original.stem  # filename without extension
    suffix = original.suffix  # .kicad_sym, .txt, etc.

    # Find next available backup number
    count = 1
    while True:
        backup_name = f"{stem}_{count:03d}{suffix}"
        backup_path = backup_dir / backup_name
        if not backup_path.exists():
            break
        count += 1

    # Copy file to backup directory with new name
    shutil.copy2(original, backup_path)
    print(f"🔁 Backed up '{original.name}' to '{backup_path}'")

    return str(backup_path)

def process_symbol(symbol):
    """Process a symbol to ensure it has the required properties.
    Args:
        symbol (Symbol): The symbol to process.
    Returns:
        bool: True if the symbol was modified, False otherwise.
    """


    existing_properties = {prop.key: prop for prop in symbol.properties}
    #print(f"\n🔹 Symbol: {symbol.libraryIdentifier}")

    # List existing properties
    for key, prop in existing_properties.items():
        print(f"   - {key}: {prop.value}")

    # Add missing properties
    modified = False

    existing = {p.key for p in symbol.properties}
    for key, info in REQUIRED_PROPERTIES.items():
        if key not in existing:
            #prop = Property(key, info["value"], hide=info["hide"])
            prop = Property(key, info["value"])
            prop.effects = Effects(hide=True)
            symbol.properties.append(prop)
            modified = True
        else:
            prop = existing_properties[key]
            if prop.effects.hide != info["hide"]:
                print(f"   ➕ Updating property: {key}")
                #prop.value = info["value"]
                prop.effects.hide = info["hide"]
                modified = True
    return modified

def main(filename):
    """Main function to process the KiCad symbol library.
    Args:
        filename (str): The path to the KiCad symbol library file.
    """

    # Check if the file exists
    if not os.path.isfile(filename):
        print(f"❌ File not found: {filename}")
        return
    
    # Backup the file
    backup_file(filename)

    # Load the symbol library
    sym_lib = SymbolLib.from_file(filename)
    modified = False

    # Process each symbol in the library
    for symbol in sym_lib.symbols:
        if process_symbol(symbol):
            modified = True

    # Save the updated library if modifications were made
    if modified:
        #output_file = filename.replace(".kicad_sym", "_updated.kicad_sym")
        output_file = filename
        sym_lib.to_file(output_file)
        print(f"\n✅ Updated library saved to: {output_file}")
    else:
        print("\n✅ All symbols already contain the required properties. No changes made.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python update_kicad_symbols.py <symbol_library.kicad_sym>")
    else:
        main(sys.argv[1])
