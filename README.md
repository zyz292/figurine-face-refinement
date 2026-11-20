# 动漫手办面雕精修

简体中文 · [English](README.en.md)

一套给 3D 建模 agent 使用的中文面雕工作流，附 Blender 多角度灰模检视工具。适合从 Hi3D 等工具生成的手办底模开始，处理鼻尖、眼周、素眼、睫毛浮雕和被刘海挡住的眼角。技能把角色还原、局部网格修整和同机位验收串起来。实际修模需要能读写三维模型的工具。

## v1.1 更新

新角色先复制[角色记录模板](skills/figurine-face-refinement/templates/face-record.json)，已有角色从[上次认可的模型和固定机位](skills/figurine-face-refinement/references/character-record.md)续修。眼内有多余的纹样或凸边时，可用[局部眼面修整工具](skills/figurine-face-refinement/references/eye-surface.md)按编辑、参照、保护三个顶点组处理。通过[局部对照图工具](skills/figurine-face-refinement/references/region-review.md)比较同机位的原模和候选版。工具要求先在当前角色上定位皮肤与周边健康曲面。

新角色试用时，可记录首次定位用时、到认可版的总用时、总 token、作者纠正次数，以及已认可区域被误改的次数。沿用同一任务描述与验收质量，区分首次定位成本和后续单次修改成本。

## 使用

1. 准备可编辑模型、角色参考和最近认可的版本。如果有成品面雕参考，说明想借鉴的是哪个局部特征。
2. 在 Codex 中调用 `$figurine-face-refinement`。其他支持 Agent Skills 的工具可导入整个技能目录；普通 agent 可直接从 [SKILL.md](skills/figurine-face-refinement/SKILL.md) 开始，按文中链接读相应的操作说明。
3. 描述这轮要改的可见形态及要保留的部分。例如「把上睫毛外侧向太阳穴展开，保留已经认可的睫根厚度和眼下留白。用修改前后的同角度灰模对照。」使用者也可以只指定鼻尖或单侧眼角。

## 安装到 Codex

用有仓库读取权限的账号取得代码。以下命令复制仓库里的技能目录，包含入口、相对链接、界面描述和可执行检视工具。已有同名本地定制时，先比较两者再更新。

```sh
git clone https://github.com/zyz292/figurine-face-refinement.git
cd figurine-face-refinement
```

Windows PowerShell，在仓库根目录执行：

```powershell
$skillRoot = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $HOME '.codex/skills' }
New-Item -ItemType Directory -Path $skillRoot -Force | Out-Null
$target = Join-Path $skillRoot 'figurine-face-refinement'
if (Test-Path $target) { throw "已存在同名技能，请先比较版本：$target" }
Copy-Item -LiteralPath 'skills/figurine-face-refinement' -Destination $target -Recurse
```

macOS 或 Linux，在仓库根目录执行：

```sh
root="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$root"
test ! -e "$root/figurine-face-refinement" && cp -R skills/figurine-face-refinement "$root/"
```

在新会话中用技能名调用。要使用独立灰模工具，先记录角色眼中心和下巴的世界坐标；对同一角色的前后版本复用这一份坐标。示例 JSON、运行命令和机位含义见[灰模检视指南](skills/figurine-face-refinement/references/clay-review.md)。

## 项目内容

| 入口 | 用途 |
| --- | --- |
| [面雕工作流](skills/figurine-face-refinement/SKILL.md) | 选底模、区分造型与贴图、判断编辑范围、修模和验收 |
| [局部网格做法](skills/figurine-face-refinement/references/mesh-repair.md) | 隔离皮肤与头发、补平眼角、保护面部数据和塑造连续浮雕 |
| [大肥鱼迭代实例](skills/figurine-face-refinement/references/case-study.md) | 从三种底模到 v15 面部验收，理解“加粗、上翘、外展”的区别 |
| [Blender 检视工具](skills/figurine-face-refinement/scripts/clay_views.py) | 用三个角色参照点生成相同尺度的正交灰模图 |
| [项目自检](tests/check_project.py) | 检查分发结构、文档链接，并可用临时场景实际测试 Blender 出图 |

## 验证

运行命令需要 Python 3.9 或以上。以下第一项只用 Python 标准库；第二项还需本机 Blender，可执行文件名也可替换成完整路径。

```sh
python tests/check_project.py
python tests/check_project.py --blender blender
python tests/test_eye_surface.py --blender blender
python tests/test_compare_region.py
```

v1.1 新增的眼面拟合已用带凸纹和保护区的合成曲面实测，局部对照图已用贝丽尔原模与既有修整版验证。外部拼图与缓存测试使用 Pillow。跨新角色的质量、耗时和 token 开销待测。

真实模型验证使用 Blender 5.2.1，在大肥鱼 v14 与 v15 上以相同取景生成了两组各五张灰模图。仓库内的可重复测试用 Blender 自带网格建立临时场景，检查输出尺寸、灰度、多角度差异以及源文件完整性。项目仅附文字案例和工具，使用者自行提供模型与角色参考图。

项目按 [Agent Skills](https://github.com/agentskills/agentskills) 目录规范组织。

## 贡献者

- [@zyz292](https://github.com/zyz292) — 项目发起与维护
