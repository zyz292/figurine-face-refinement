import argparse
import hashlib
import json
import re
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "figurine-face-refinement"
BLENDER = None


class ProjectChecks(unittest.TestCase):
    def test_distribution(self):
        entry = (SKILL / "SKILL.md").read_text("utf-8-sig")
        self.assertTrue(entry.startswith("---\nname: figurine-face-refinement\n"))
        self.assertTrue((SKILL / "agents/openai.yaml").is_file())
        self.assertTrue((SKILL / "scripts/clay_views.py").is_file())
        for doc in [ROOT / "README.md", *SKILL.rglob("*.md")]:
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", doc.read_text("utf-8-sig")):
                if "://" not in target:
                    self.assertTrue((doc.parent / target.split("#")[0]).is_file(), target)

    def test_blender_views(self):
        if not BLENDER:
            self.skipTest("pass --blender to render a temporary scene")
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            model = folder / "fixture.blend"
            frame = folder / "frame.json"
            out = folder / "views"
            create = ("import bpy; bpy.ops.wm.read_factory_settings(use_empty=True); "
                      "bpy.ops.mesh.primitive_monkey_add(); "
                      f"bpy.ops.wm.save_as_mainfile(filepath={str(model)!r})")
            subprocess.run([BLENDER, "-b", "--factory-startup", "--python-exit-code", "1",
                            "--python-expr", create], check=True)
            frame.write_text(json.dumps({"screen_left_eye": [-0.4, -0.6, 0.3],
                                         "screen_right_eye": [0.4, -0.6, 0.3],
                                         "chin": [0, -0.6, -0.7]}), encoding="utf-8")
            digest = hashlib.sha256(model.read_bytes()).digest()
            subprocess.run([BLENDER, "-b", str(model), "--python-exit-code", "1", "-P",
                            str(SKILL / "scripts/clay_views.py"), "--", "--frame", str(frame),
                            "--output", str(out)], check=True)
            self.assertEqual(hashlib.sha256(model.read_bytes()).digest(), digest)
            actual = {f.name for f in out.glob("*.png")}
            self.assertEqual(actual, {f"view_{a:+03d}.png" for a in (0, -35, 35, -70, 70)})
            pixels = []
            for f in sorted(out.glob("*.png")):
                contents = f.read_bytes()
                self.assertEqual(contents[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack(">II", contents[16:24]), (920, 720))
                self.assertEqual(contents[25], 0, "PNG uses grayscale color type")
                offset = 8
                parts = []
                while offset < len(contents):
                    size = int.from_bytes(contents[offset:offset + 4], "big")
                    if contents[offset + 4:offset + 8] == b"IDAT":
                        parts.append(contents[offset + 8:offset + 8 + size])
                    offset += 12 + size
                self.assertTrue(parts)
                pixels.append(b"".join(parts))
            self.assertEqual(len(set(pixels)), 5, "Camera views should differ")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--blender", help="Blender executable name or path")
    BLENDER = parser.parse_args().blender
    unittest.main(argv=["check_project"], verbosity=2)
