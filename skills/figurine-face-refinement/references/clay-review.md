# 固定机位灰模检视

可选工具 [clay_views.py](../scripts/clay_views.py) 由 Blender 在后台运行，只输出灰度 PNG。比较两个版本时用同一个场景坐标系、同一份取景文件、同一 Blender 版本和色彩管理。先对齐发生过整体移动、旋转或缩放的模型。如果使用别的建模软件，照下面的方法固定正交相机即可。

## 取点与出图

1. 正对角色，取画面左眼中心、画面右眼中心和下巴中央三个**世界坐标**。眼睛微闭或待修时，在眼眶位置取稳定的对应点。前两点的顺序决定相机朝向。下巴负责确定上下方向；侧头角色仍使用自身的脸部基准。已有模型的实际中心不必在世界原点。
2. 把点写入 UTF-8 的 JSON。以下是脸朝世界负 Y、头顶朝正 Z 的示意，需要用当前模型的坐标替换。宽度以两个眼中心之间的距离计量。

```json
{
  "screen_left_eye": [-1, 0, 0.5],
  "screen_right_eye": [1, 0, 0.5],
  "chin": [0, 0, -1],
  "width_in_eye_spans": 3.15,
  "angles": [0, -35, 35, -70, 70]
}
```

3. 从技能目录执行。将可执行文件名和模型、取景文件路径换成实际值。为各版指定独立的输出目录，同名视图会被重写。

```sh
blender -b "character-v1.blend" --python-exit-code 1 -P "scripts/clay_views.py" -- --frame "frame.json" --output "review/v1"
blender -b "character-v2.blend" --python-exit-code 1 -P "scripts/clay_views.py" -- --frame "frame.json" --output "review/v2"
```

输出 920 × 720 的正交灰模图。例如 view_+00.png 为正面，view_-35.png 和 view_+35.png 分别从画面左、右侧观察。鼻尖可加 ±90 度查准确剪影；睫毛可补一张外眼角近景。此脚本使用当前场景中可渲染的物体，不改写 .blend。正常发型与去遮挡图分别从展示版、临时检视副本生成。若正面看到后脑，先核对左右点顺序；若目标过小、裁掉下巴或还有别的模型挡着，检查构图宽度、点位和可渲染物体。
