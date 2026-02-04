from __future__ import annotations
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import re
from typing import Any, List, Dict

# Export Directory
EXPORT_DIR = (Path(__file__).resolve().parent.parent.parent / "exports" / "mvr").resolve()

def _safe_filename(name: str) -> str:
    name = (name or "show").strip()
    name = re.sub(r"[^\w\-. ]+", "_", name, flags=re.UNICODE)
    return name[:80] or "show"

def _get_attr(obj: Any, *names: str, default: Any = "") -> Any:
    for n in names:
        if isinstance(obj, dict):
            if n in obj:
                return obj[n]
        elif hasattr(obj, n):
            v = getattr(obj, n)
            if v is not None:
                return v
    return default

def export_mvr_to_file(show: Dict | Any, export_dir: str | Path | None = None) -> Path:
    """
    Generates an MVR file (ZIP containing GeneralSceneDescription.xml) from the show data.
    """
    out_dir = Path(export_dir).resolve() if export_dir else EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    show_name = _get_attr(show, "name", default="Show")
    safe_name = _safe_filename(show_name)
    zip_filename = f"{safe_name}.mvr"
    zip_path = (out_dir / zip_filename).resolve()

    # Create XML Structure
    root = ET.Element("GeneralSceneDescription")
    root.set("xmlns", "https://github.com/mvr-development/mvr/wiki/General-Scene-Description-1.6")
    root.set("verMajor", "1")
    root.set("verMinor", "6")

    # UserData
    user_data = ET.SubElement(root, "UserData")
    provider = ET.SubElement(user_data, "Data")
    provider.set("provider", "CueX Lichtassistent")
    provider.set("ver", "4.0.1")

    # Scene
    scene = ET.SubElement(root, "Scene")
    layers = ET.SubElement(scene, "Layers")
    
    # Create a default Layer for the Rig
    layer = ET.SubElement(layers, "Layer")
    layer.set("name", "Rig")
    layer.set("uuid", "00000000-0000-0000-0000-000000000001") # Static UUID for now, should be unique ideally
    
    child_list = ET.SubElement(layer, "ChildList")

    # Collect fixtures from Rig data
    # We support keys from the standard structure: spots_items, washes_items, etc.
    rig = show.get("rig_setup", {}) if isinstance(show, dict) else getattr(show, "rig_setup", {})
    if not rig:
        rig = {}

    fixture_id_counter = 1
    
    all_items = []
    
    prefixes = ("spots", "washes", "beams", "blinders", "strobes")
    for p in prefixes:
        items = rig.get(f"{p}_items", [])
        for it in items:
            count = 0
            try:
                count = int(it.get("count", 0))
            except: pass
            
            man = it.get("manufacturer", "")
            mod = it.get("model", "")
            mode = it.get("mode", "")
            uni = it.get("universe", "")
            addr = it.get("address", "")
            
            for i in range(count):
                item_data = {
                    "name": f"{p.capitalize()} {i+1}" if not mod else f"{mod} {i+1}",
                    "id": fixture_id_counter,
                    "fixture_id": fixture_id_counter, # Use same for now
                    "manufacturer": man,
                    "model": mod,
                    "mode": mode,
                    "universe": uni,
                    "address": addr,
                    # Simple automated positioning (line up on X axis)
                    "x": (fixture_id_counter - 1) * 1000, # mm
                    "y": 0,
                    "z": 0
                }
                all_items.append(item_data)
                fixture_id_counter += 1

    # Add Custom Devices
    custom_devs = rig.get("custom_devices", [])
    for cd in custom_devs:
         count = 0
         try:
             count = int(cd.get("count", 0))
         except: pass
         for i in range(count):
             item_data = {
                 "name": cd.get("name") or f"Custom {fixture_id_counter}",
                 "id": fixture_id_counter,
                 "fixture_id": fixture_id_counter,
                 "manufacturer": cd.get("manufacturer", ""),
                 "model": cd.get("model", ""),
                 "mode": cd.get("mode", ""),
                 "universe": cd.get("universe", ""),
                 "address": cd.get("address", ""),
                 "x": (fixture_id_counter - 1) * 1000,
                 "y": 2000, # Offset custom devices slightly
                 "z": 0
             }
             all_items.append(item_data)
             fixture_id_counter += 1

    # Write items to XML
    for it in all_items:
        fix = ET.SubElement(child_list, "Fixture")
        fix.set("name", str(it["name"]))
        fix.set("uuid", f"00000000-0000-0000-0000-{it['id']:012d}") # Fake UUIDs
        fix.set("fixtureId", str(it["fixture_id"]))
        
        # GDTF Spec / Mode usually requires a GDTF file application, 
        # but for MVR we can provide basic info in the GDTFSpec attribute or leave it empty if unknown.
        # We will put Manufacturer + Model as placeholders
        gdtf_name = f"{it['manufacturer']} {it['model']}".strip()
        if not gdtf_name:
            gdtf_name = "Generic Fixture"
        fix.set("gdtfSpec", f"{gdtf_name}.gdtf")
        fix.set("gdtfMode", str(it["mode"]))

        # Matrix (Position/Rotation)
        # Matrix 4x4 flattened: 
        # 1 0 0 0
        # 0 1 0 0 
        # 0 0 1 0
        # x y z 1
        # MVR expects "1,0,0,0}{0,1,0,0}{0,0,1,0}{x,y,z,1" format usually? 
        # Actually GDTF uses space separated values usually or braces?
        # Checked MVR spec: It uses a child element <Matrix>1 0 0 0 0 1 0 0 0 0 1 0 x y z 1</Matrix> (in mm usually)
        
        matrix = ET.SubElement(fix, "Matrix")
        # Ensure mm (CueX uses usually internal units? Assuming user input is generic, we just verify relative spacing)
        # Using basic identity matrix with translation
        x = it["x"]
        y = it["y"]
        z = it["z"]
        matrix.text = f"1.000000 0.000000 0.000000 0.000000 0.000000 1.000000 0.000000 0.000000 0.000000 0.000000 1.000000 0.000000 {x}.000000 {y}.000000 {z}.000000 1.000000"

        # Addresses
        # <Addresses><Address break="1" universe="1" address="1" /></Addresses>
        uni_str = str(it["universe"]).strip()
        addr_str = str(it["address"]).strip()
        
        if uni_str and addr_str:
            try:
                # MVR/GDTF spec uses 'Addresses' container
                addresses = ET.SubElement(fix, "Addresses")
                address_node = ET.SubElement(addresses, "Address")
                address_node.set("break", "1")
                address_node.set("universe", uni_str)
                address_node.set("address", addr_str)
            except:
                pass


    # Format XML
    ET.indent(root, space="  ", level=0)
    xml_str = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    # Wrap in ZIP
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("GeneralSceneDescription.xml", xml_str)

    return zip_path
