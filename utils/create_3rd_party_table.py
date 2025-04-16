"""
File: create_3rd_party_table.py

Author: Jon Richards
Date: April 16, 2025

Description: This script generates a table of 3rd party components 
             used in the KiCad project. This table is formatted for 
             GitHub markdown. The output is to be copied and pasted into
             the README.md for the project
             It parses the schematic files to extract component information 
             such as reference, name, manufacturer, part number, distributor, 
             and distributor part number.
"""
import os
from typing import List
from kiutils.schematic import Schematic
import pandas as pd

# --- CONFIGURATION ---
#project_root = "../Simple_Dish_Controller"  # Folder containing the top-level .kicad_sch
#top_schematic = os.path.join(project_root, "simple_dish_manual_controller.kicad_sch")  # Top-level schematic

# Recursive function to parse schematic sheets
def parse_schematic(project_root: str, sch_path: str, visited: set=None) -> List:
    """
    Recursively parse schematic sheets to extract component information.
    Args:
        project_root (str): The root directory of the KiCad project.
        sch_path (str): The path to the schematic file.
        visited (set): A set to keep track of visited files to avoid infinite loops.
    Returns:
        List: A list of component information extracted from the schematic.
    """
    if visited is None:
        visited = set()

    full_path = os.path.normpath(os.path.join(project_root, sch_path))

    if full_path in visited:
        return []
    visited.add(full_path)

    #print(f"Parsing {full_path}")

    try:
        schematic = Schematic.from_file(full_path)
    except Exception as e:
        print(f"Error reading {sch_path}: {e}")
        return []
    
    #print(schematic.schematicSymbols[0])
    rows = []
    for sym in schematic.schematicSymbols:
        #print("\t" + sym.entryName)
        props = {prop.key: prop.value for prop in sym.properties}
        if 'Footprint' in props and props['Footprint'].startswith("DishFootprints:"):

            #print("\t" + sym.entryName)
            #print(sym.properties)

            rows.append([
                props.get("Reference"),
                sym.entryName,
                props.get("MANUFACTURER"),
                props.get("MPN"),
                props.get("DIS"),
                props.get("DPN"),
                props.get("FILES")
                
            ])

    # Recurse into subsheets
    for sheet in schematic.sheets:
        rows.extend(parse_schematic(project_root, sheet.fileName.value, visited))

    return rows


def main(project_root: str, top_schematic: str):
    
    top_schematic = os.path.join(project_root, top_schematic)

    # --- Run the parser ---
    results = parse_schematic(project_root, top_schematic)

    headers = ["Reference", "Name", "Manufacturer", "Man PN", "Distributor", "Dist PN", "Files"]

    # Using pandas create a dataframe from the results list
    # The column names are "Reference", "Name", "Manufacturer", "Man PN", "Distributor", "Dist PN", "Files"
    df = pd.DataFrame(results, columns=headers, index=None)

    # Combine any row with the same Reference
    combined_df = df.groupby('Man PN', as_index=False).agg(
        lambda x: ','.join(x) if x.name == 'Reference' else x.iloc[0]
    )
    combined_df = combined_df[headers]


    # Generate a github markdown equivalent of combined_df
    df = combined_df.to_markdown(index=False, tablefmt="github", colalign=("left", "left", "left", "left", "left", "left", "left"))
    print(df)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python create_3rd_party_table.py <project root dir> <symbol_library.kicad_sym>")
        print("Example:")
        print("python create_3rd_party_table.py ../Simple_Dish_Controller simple_dish_manual_controller.kicad_sch")
    else:
        main(sys.argv[1], sys.argv[2])

