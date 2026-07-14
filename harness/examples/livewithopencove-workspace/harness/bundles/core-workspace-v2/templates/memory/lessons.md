# Lessons

> 复盘记录。用户复盘时追加。
> 经验教训是"下次怎么做"，不是"这次做了什么"。
>
> **写成条件句**：`当 X → 做 Y`，不写绝对句（绝对句会过拟合这一个案例，下次场景一变就误导）。
>
> **每条带一行机读 meta**（给 `.claude/scripts/lessons_gc.py` 体检用）：
> - `scope`：这条经验适用的 skill / 场景标签（召回时按它过滤，逗号分隔）。
> - `applied`：被读回应用过几次；`helpful`/`harmful`：帮到 / 帮倒几次（收尾时按实情 +1）。
> - `last`：最近一次应用日期。`harmful>helpful` 或长期 `applied=0` 会被脚本建议退役。
>
> 格式（复制下面这块去掉前导 `> ` 即可）：
>
> ```markdown
> ## YYYY-MM-DD: 当 X → 做 Y
> <!-- meta: id=Lxxx | scope=skill名,场景标签 | applied=0 | helpful=0 | harmful=0 | last=YYYY-MM-DD -->
> **场景：** [什么情况下]
> **观察：** [发生了什么]
> **做法：** [怎么处理的]
> **效果：** [结果如何]
> **置信度：** 高 / 中 / 低
> **建议：** [下次怎么做]
> ```
