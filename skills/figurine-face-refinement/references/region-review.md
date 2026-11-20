# 局部同机位对照

在装有 Pillow 的外部 Python 中执行。先依照[固定机位灰模检视](clay-review.md)建立角色的 frame.json，两个版本使用相同世界坐标与头部姿态。用当前认可版作 baseline，将重新保存的修改版作为 current。角色记录可以引用这两个模型和机位文件。

```sh
python scripts/compare_region.py --blender blender --baseline approved.blend --current working.blend --frame frame.json --region eye --output eye-check.png
```

每一列的相机和裁切固定，上排为基线，下排为本轮。eye 看双眼下缘和脸颊，lash 看睫根与外眼角，二者都取正面与左右 35°。nose 取正面、35° 和 70° 检查前伸和转折。预设裁切针对默认头部取景；若当前角色有较宽眼距或头发遮挡，使用 `--crop 0.12 0.10 0.88 0.72` 指定整帧中的左、上、右、下比例。核对圈注位置和眼角实际入镜后再判断。完整灰模验收仍可直接使用 clay_views.py。

基线原始视图按模型内容与路径、机位、角度、Blender 版本和渲染脚本缓存，变更裁切可复用同一组视图。默认缓存位于输出目录下的 .clay-cache，可用 `--cache` 指向该角色共用的目录。修改版每次重新渲染。包含外链网格、模拟缓存或其他可能独立变化的依赖时加 `--no-cache`。重新定位、头部姿态变化时先更新机位和基线。
