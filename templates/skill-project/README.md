# Skill Project Template

复制本目录为 `projects/<skill-name>`，用于沉淀某个 Skill 的开发资料。正式可安装内容放在 `skills/<skill-name>`。

## 推荐文件

- `PROJECT.md`：项目目标、范围、资源索引、验证方式。
- `notes/`：调研记录、踩坑记录、会议记录。
- `examples/`：真实输入/输出样例，避免放敏感数据。
- `todo.md`：后续迭代清单。

## 与 `skills/` 的关系

- `projects/<skill-name>` 是“研发工作台”。
- `skills/<skill-name>` 是“发布包”。
- 多个 Skill 共用的内容放在 `shared/`，再从各自 `SKILL.md` 中说明何时读取。
