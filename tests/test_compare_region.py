import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/figurine-face-refinement/scripts"))
import compare_region as cr


class CompareTest(unittest.TestCase):
    def test_baseline_reuse_and_invalidation(self):
        calls = []

        def fake_render(blender, model, frame, folder):
            calls.append(model)
            folder.mkdir()
            for i in json.loads(frame.read_text())["angles"]:
                cr.Image.new("L", (400, 300), int(model.read_text())).save(cr.view(folder, i))

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = SimpleNamespace(baseline=root/"old.blend", current=root/"new.blend",
                                   output=root/"view.png", cache=None, no_cache=False,
                                   region="eye", frame=root/"frame.json", crop=None, blender="blender")
            args.baseline.write_text("10")
            args.current.write_text("190")
            args.frame.write_text("{}")
            with patch.object(cr, "render", fake_render), patch.object(cr.subprocess, "check_output", return_value=b"5.2"):
                cr.compare(args)
                args.crop = [.1,.1,.9,.9]
                cr.compare(args)
                self.assertEqual(calls, [args.baseline,args.current,args.current])
                with cr.Image.open(args.output) as img:
                    self.assertEqual(img.getpixel((20,40)), (10,10,10))
                    self.assertEqual(img.getpixel((20,310)), (190,190,190))
                cached = next(root.glob(".clay-cache/*/*.png"))
                cached.write_bytes(b"broken")
                cr.compare(args)
                args.baseline.write_text("15")
                cr.compare(args)
                self.assertEqual(calls.count(args.baseline), 3)
                args.no_cache = True
                cr.compare(args)
                self.assertEqual(calls.count(args.baseline), 4)


if __name__ == "__main__":
    unittest.main()
