# Utilities

A small set of Python utilitoes to aid in KiCad project management.

These scripts should commonly be run from the utils directory.

## Installation

Create a Python virtual environment if desired:
- python -m venv venv
- pip install -r requirements.txt

## create_3rd_party_table.py

Used to create a list of all the parts not contained in the standard KiCad. The distribution of these files is restricted due to license requirements. So a list of them is provided to the user for reference.

This script will:
- Read and parse a schematic file
- Any symbols from a library named DishFootprints will be recognized
- A list of the parts and symbol/footprint file URLs is created. This list is in the form of a GitHub markdown table for insertion into a README.md file.

Script invocation example:

```
python create_3rd_party_table.py ../Simple_Dish_Controller simple_dish_manual_controller.kicad_sch
```

Example output:

| Reference   | Name                                   | Manufacturer         | Man PN             | Distributor   | Dist PN               | Files                                     |
|-------------|----------------------------------------|----------------------|--------------------|---------------|-----------------------|-------------------------------------------|
| J3          | Screw Terminal Ground Chassis Vertical | Keystone Electronics | 7690               | Digikey       | 36-7690-ND            | https://www.digikey.com/en/models/151547  |
| J7,J5       | DE-15_VGA_FEMALE_CONN                  | Amphenol             | L77HDE15SD1CH4FVGA | Digikey       | L77HDE15SD1CH4FVGA-ND | https://www.digikey.com/en/models/4888525 |


## fix_kicad_symbols.py

For each symbol in a library make sure it has the required properties. This is useful information to fill in sybbols in a custom library.

The list is the following properties:

    - Value
    - Footprint
    - Datasheet
    - Description
    - Package
    - MF
    - MPN
    - DIS
    - DPN
    - Purchase_URL
    - Price
    - Note

Script invocation example:

```
python update_kicad_symbols.py ../third_party_symbols_and_footprints/DishSymbols.kicad_sym
```

The file DishSymbols.kicad_sym will be modified.