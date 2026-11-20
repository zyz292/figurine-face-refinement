"""Run: python tests/test_eye_surface.py --blender <blender executable>."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile

SCRIPT = Path(__file__).resolve().parents[1] / "skills/figurine-face-refinement/scripts/eye_surface.py"


def check(blender):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        src, out, svg = [root/name for name in ("source.blend", "after.blend", "mask.svg")]
        def run(*args):
            subprocess.run([blender, "-b", "--factory-startup", "--python-exit-code", "1", *map(str,args)], check=True)
        setup = """
import bpy, math
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=41,y_subdivisions=41,size=2)
obj=bpy.context.object
obj.name='Face'
groups={n:obj.vertex_groups.new(name=n) for n in ('EyeEdit','EyeRing','Keep')}
for vert in obj.data.vertices:
    x,y,z=vert.co
    r=math.hypot(x,y)
    vert.co.z=.08*r*r + .18*math.exp(-70*r*r)
    if r < .49: groups['EyeEdit'].add([vert.index],1.,'REPLACE')
    if .51 < r < .68: groups['EyeRing'].add([vert.index],1.,'REPLACE')
    if .31 < x < .39 and abs(y)<.08: groups['Keep'].add([vert.index],1.,'REPLACE')
"""
        run("--python-expr",setup+f"\nbpy.ops.wm.save_as_mainfile(filepath={str(src)!r})")
        digest = hashlib.sha256(src.read_bytes()).digest()
        args=(src,"-P", SCRIPT,"--","--object","Face","--edit","EyeEdit","--reference","EyeRing","--protect","Keep")
        run(*args,"--preview",svg)
        assert '<circle' in svg.read_text()
        run(*args,"--output",out)
        run(out,"--python-expr",f"""
import bpy, math
def vertices(): return [tuple(v.co) for v in bpy.data.objects['Face'].data.vertices]
after=vertices()
bpy.ops.wm.open_mainfile(filepath={str(src)!r})
before=vertices()
assert len(before)==len(after)
assert max(abs(a[2]-b[2]) for a,b in zip(after,before))>.14
for (x,y,z),a in zip(before,after):
    r=math.hypot(x,y)
    if r>=.49 or (.31<x<.39 and abs(y)<.08): assert a==(x,y,z)
    if r<.1: assert abs(a[2]-.08*r*r)<.002
""")
        assert hashlib.sha256(src.read_bytes()).digest()==digest


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--blender",required=True)
    check(parser.parse_args().blender)
