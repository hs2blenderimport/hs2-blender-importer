# hs2-blender-importer

Instructions:
1. Export from HS2 using Grey's Mesh Exporter
2. Import in blender using Better FBX Importer (Don't need Better FBX Importer if you are going to rig yourself)
3. Add texture directory from exported hs2 model
4. Assign Basic Materials
5. Create hair and clothes materials
6. (Optional) Use Auto Rig Pro to map exported bones to rig
7. (Optional) Configure bones (this just rotates fingers correctly, adds constraints, and adds a look at bone)

Notes:
- Works best with Next gen skin
  - Somethings off with default skins, so you need to adjust to fix
- Not very polished, so you'll probably hit bugs or see testing things
- Only added constraints for the leg deform bones. They aren't correct, but work good enough.
