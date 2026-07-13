# skill-optimizer

Skill 治理统一主入口。先对齐工作方式、目标和验收口径，再评分、锐评、优化、回滚。

`setup-daily-work-skills` 现在只是兼容入口，不再维护第二套方法论。

## 一眼验收

先看两件事：

1. 常见问法会不会命中对的 skill
```bash
cd /Users/sure/Daily\ Work
python3 skills/skill-recommend-regression.py
```

2. 当前治理快照是不是能正常生成
```bash
cd /Users/sure/Daily\ Work
python3 skills/skill-governance.py --query "先对齐一下工作方式"
```

如果第一条返回 `OK`，说明这轮最核心的入口路由还稳。
如果第二条能正常生成 `skills/skill-governance.snapshot.json`，说明治理展示层也还通。
