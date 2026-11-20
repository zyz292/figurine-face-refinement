# 角色修模记录

把[空白记录](../templates/face-record.json)复制到角色工程，命名为 face-record.json。路径按记录所在目录解析。已有记录就更新当前字段。工具的命令行参数从记录取值，首次只填本轮需要的字段。

- working_baseline 是本轮起点，可为原模。candidate_model 是待检视的输出。accepted_model 仅在用户认可后填写。下一轮沿用认可版；若用户指向另一份模型，记录实际起点。
- character_reference 决定角色相似度；technique_reference 可选，用来参考材料厚度、贴脸方式等做法。geometry 和 texture 分别记已经确定的分工。preserve 只记已认可或本轮要求保护的部位。
- frame_file 指向[机位 JSON](clay-review.md)。保留真实世界坐标，模型变换或头姿改变后先核对。head_mesh 存对象名。
- eye_regions 中每项分别记录一只眼的画面侧别、对应模型及三个顶点组名。例如 `{"screen_side":"left","model":"work/face_v1.blend","edit":"EyeL_Edit","reference":"EyeL_Ring","protect":"Face_Keep"}`。只有定位和组成员关系仍有效时才复用。新角色、重拓扑或拆件后重新标定，尤其注意皮肤与刘海的边界。
- current_change 用一句话记录本轮目标，例如「睫根厚度已认可，只向太阳穴延伸主尖」。remaining_visual_issue 写同机位可见的残留问题，解决后清空。

## 如何减少往返

开新会话先读这一张记录与当前目标。已有决定直接沿用；只打开这轮对应的操作说明和一张局部对照图。选区不确定时先看选区投影，再用带发灰模核对。能从侧面看出的球状突起、眼角暗坑和误动刘海应先自行修正。只有「更翘」等要求存在两种会明显改变神态的解释，且参考仍不能区分时，再用同一机位的两个局部备选请作者判断。
