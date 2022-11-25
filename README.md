# hs2-blender-importer

## Prereqs
- Grey Mesh Exporter
*These prereqs are if you want to rig using the exported bones*
- Auto Rig Pro
- Better FBX Importer

## Instructions
```
1. Add __init__ file to C:\Users\<user>\AppData\Roaming\Blender Foundation\Blender\3.2\scripts\hs2_importer
  - Or wherever your blender scripts directory is located
2. Enable the addon in blender
3. Export from HS2 using Grey's Mesh Exporter
4. Import in blender using Better FBX Importer (Don't need Better FBX Importer if you are going to rig yourself)
5. Add texture directory from exported hs2 model
6. Assign Basic Materials
7. Create hair and clothes materials
8. (Optional) Use Auto Rig Pro to map exported bones to rig
  - Use the "Quick Rig" feature with the provided bone_mapping.py file (or you can do the mapping yourself)
  - When quick rigging, use the "Preserve" option to keep accessories rigged
    - You'll need to parent the new rig to the old one so they move together
  - Best to adjust the layer to 2 so that all extra bones aren't in the same layer
9. (Optional) Configure bones (this just rotates fingers correctly, adds constraints, and adds a look at bone)
```

## Notes
- Works best with Next gen skin
  - Somethings off with default skins, so you need to adjust to fix
- Shading probably has mistakes and is missing some things. Feel free to adjust the script
- Not very polished, so you'll probably hit bugs or see testing things
- Only added constraints for the leg deform bones. They aren't correct, but work good enough.
- bone_mapping.py is probably missing some things
