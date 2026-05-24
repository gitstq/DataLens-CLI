<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Version-0.1.0-orange.svg" alt="v0.1.0">
  <img src="https://img.shields.io/badge/Dependencies-Zero_Core-brightgreen.svg" alt="Zero Dependencies">
  <img src="https://img.shields.io/badge/Tests-37_Passing-success.svg" alt="37 Tests Passing">
</p>

<h1 align="center">DataLens CLI</h1>

<p align="center">
  <strong>轻量级终端 JSON / YAML / TOML 智能数据处理引擎</strong><br>
  <em>A lightweight terminal JSON/YAML/TOML intelligent data processing engine</em>
</p>

<p align="center">
  <a href="#简体中文">简体中文</a> &nbsp;|&nbsp;
  <a href="#繁體中文">繁體中文</a> &nbsp;|&nbsp;
  <a href="#english">English</a>
</p>

---

<a id="简体中文"></a>

## 简体中文

### 🎉 项目介绍

**DataLens CLI** 是一款专为开发者打造的轻量级终端数据处理工具，能够对 JSON、YAML、TOML、CSV 等结构化数据进行查询、转换、验证、比较和统计分析。

在日常开发工作中，我们经常需要快速查看、过滤或比较 JSON 配置文件和 API 响应数据。传统做法要么用文本编辑器手动翻找，要么依赖 `jq`、`yq` 等工具——但它们各自只擅长一种格式，学习曲线陡峭，组合使用时体验割裂。DataLens CLI 的诞生正是为了解决这些痛点：**一个工具，覆盖所有主流结构化数据格式，开箱即用。**

#### ✨ 与 jq / yq / jless 的差异化亮点

| 特性 | DataLens CLI | jq | yq | jless |
|------|:-----------:|:--:|:--:|:-----:|
| JSON 支持 | ✅ | ✅ | ✅ | ✅ |
| YAML 支持 | ✅ | ❌ | ✅ | ❌ |
| TOML 支持 | ✅ | ❌ | ✅ | ❌ |
| CSV 支持 | ✅ | ❌ | ✅ | ❌ |
| Schema 推断 | ✅ | ❌ | ❌ | ❌ |
| JSON Schema 验证 | ✅ | ❌ | ❌ | ❌ |
| 深度数据比较 (diff) | ✅ | ❌ | ❌ | ❌ |
| 数据统计与可视化 | ✅ | ❌ | ❌ | ❌ |
| 管道 (pipe) 支持 | ✅ | ✅ | ✅ | ❌ |
| 零外部依赖 (核心) | ✅ | ✅ | ❌ | ❌ |
| Python 原生 | ✅ | ❌ | ❌ | ❌ |

#### 💡 设计灵感

DataLens CLI 的灵感来源于日常开发中频繁遇到的小痛点：查看一个嵌套很深的 JSON 配置、对比两份 API 响应的差异、从 YAML 文件中提取特定字段……我们希望有一个**统一、轻量、无需安装一堆依赖**的命令行工具来搞定这些事情。它不需要成为下一个 `jq`，而是做 `jq` 不擅长的事——跨格式、一站式、开发者友好的数据处理体验。

---

### ✨ 核心特性

DataLens CLI 提供 **10 个核心命令**，覆盖数据处理全流程：

| 命令 | 说明 | 示例 |
|------|------|------|
| 🔍 **query** | 智能查询引擎，支持点表示法、通配符、递归下降、过滤表达式 | `datalens query data.json 'users[0].name'` |
| 🔄 **convert** | JSON / YAML / TOML / CSV 格式互转 | `datalens convert data.json --to yaml` |
| ✅ **validate** | 基于 JSON Schema 的数据验证（纯 stdlib 实现） | `datalens validate data.json --schema schema.json` |
| 📋 **schema** | 从样本数据自动推断 JSON Schema，智能识别 email/uri/uuid 等格式 | `datalens schema data.json` |
| 📊 **diff** | 深度数据比较，彩色终端输出，支持键值匹配 | `datalens diff old.json new.json` |
| 🎨 **pretty** | 语法高亮美化打印，ANSI 原生着色（无外部依赖） | `datalens pretty data.json` |
| 🔗 **merge** | 深度合并多个数据文件，5 种合并策略可选 | `datalens merge config1.json config2.json` |
| 🧹 **filter** | 15+ 运算符的数据过滤与排序，支持嵌套字段 | `datalens filter data.json --field age --op '>' --value 25` |
| 📈 **stats** | 数据结构统计分析，含可视化柱状图 | `datalens stats data.json` |
| 📦 **batch** | 批量文件处理，一次操作多个文件 | `datalens batch query *.json --expr '.version'` |

---

### 🚀 快速开始

#### 📋 环境要求

- **Python 3.8+**（核心功能零外部依赖，仅使用标准库）
- 可选依赖：`pyyaml`（YAML 支持）、`toml`（Python < 3.11 的 TOML 支持）

#### 📦 安装

```bash
# 从源码安装（核心功能，无额外依赖）
pip install .

# 安装并包含 YAML 和 TOML 支持
pip install ".[all]"

# 或分别安装可选依赖
pip install ".[yaml]"   # YAML 支持
pip install ".[toml]"   # TOML 支持（Python < 3.11）
```

#### ⚡ 快速体验

```bash
# 查看版本
datalens -v

# 查询数据
datalens query data.json 'users[0].name'
datalens query data.json 'users[*].email'
datalens query data.json '..version'

# 格式转换
datalens convert data.json --to yaml
datalens convert data.json --to csv

# Schema 推断
datalens schema data.json

# 数据比较
datalens diff old.json new.json

# 数据过滤
datalens filter data.json --field age --op '>' --value 25

# 数据统计
datalens stats data.json

# 深度合并
datalens merge config1.json config2.json

# 管道操作
cat data.json | datalens query '.users' | datalens filter --stdin --field active --op '==' --value true
```

---

### 📖 详细使用指南

#### 🔍 高级查询示例

```bash
# 点表示法访问嵌套字段
datalens query config.json 'database.host'

# 数组索引（支持负数索引）
datalens query data.json 'users[0].name'
datalens query data.json 'users[-1].name'

# 通配符展开所有数组元素
datalens query data.json 'users[*].name'
datalens query data.json 'users[*].email'

# 递归下降——在所有层级搜索指定字段
datalens query data.json '..version'
datalens query data.json '..id'

# 过滤表达式
datalens query data.json 'users[?age>30]'
datalens query data.json 'items[?name=~^Widget]'

# JSONPath 风格的根选择器
datalens query data.json '$.users[*].name'

# 原始输出（无格式化）
datalens query data.json 'users[0].name' --raw

# 输出到文件
datalens query data.json 'users' -o users_only.json
```

#### 🧹 过滤运算符一览

`filter` 命令支持 **15+ 种运算符**，满足各种数据筛选需求：

| 运算符 | 别名 | 说明 | 示例 |
|--------|------|------|------|
| `==` | `eq` | 等于 | `--op '==' --value 'Alice'` |
| `!=` | `ne` | 不等于 | `--op '!=' --value 0` |
| `>` | `gt` | 大于 | `--op '>' --value 25` |
| `<` | `lt` | 小于 | `--op '<' --value 100` |
| `>=` | `ge` | 大于等于 | `--op '>=' --value 18` |
| `<=` | `le` | 小于等于 | `--op '<=' --value 65` |
| `contains` | | 包含（字符串/数组） | `--op contains --value 'admin'` |
| `!contains` | | 不包含 | `--op '!contains' --value 'test'` |
| `starts` | `startswith` | 前缀匹配 | `--op starts --value 'https'` |
| `ends` | `endswith` | 后缀匹配 | `--op ends --value '.json'` |
| `in` | | 包含于列表 | `--op in --value '["a","b"]'` |
| `!in` | | 不包含于列表 | `--op '!in' --value '["x"]'` |
| `regex` | `=~` | 正则匹配 | `--op regex --value '^\d+$'` |
| `type` | | 类型检查 | `--op type --value 'string'` |
| `exists` | | 字段存在 | `--op exists` |
| `!exists` | | 字段不存在 | `--op '!exists'` |

```bash
# 组合使用：过滤 + 排序 + 分页 + 字段选择
datalens filter data.json \
  --field age --op '>' --value 25 \
  --sort age --desc \
  --limit 10 --offset 0 \
  --select name,email,age

# 嵌套字段过滤（点表示法）
datalens filter data.json --field address.city --op '==' --value 'Beijing'
```

#### 🔗 合并策略

`merge` 命令提供 **5 种合并策略**，灵活应对不同场景：

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `overwrite` | 覆盖（默认） | 后者覆盖前者，列表直接替换 |
| `append` | 追加 | 列表元素追加到末尾 |
| `prepend` | 前置 | 列表元素插入到开头 |
| `unique` | 去重合并 | 列表合并并去除重复项 |
| `deep` | 深度合并 | 按索引逐元素深度合并列表 |

```bash
# 默认覆盖合并
datalens merge default.json override.json

# 列表追加合并
datalens merge base.json extra.json --strategy append

# 去重合并
datalens merge tags1.json tags2.json --strategy unique

# 深度合并（按索引合并列表元素）
datalens merge config1.json config2.json --strategy deep

# 合并多个文件
datalens merge config1.json config2.json config3.json -o merged.json
```

#### 🔗 管道用法

DataLens CLI 完美支持 Unix 管道，可以与其他命令行工具无缝协作：

```bash
# 基本管道查询
cat data.json | datalens query '.users[*].name'

# 多级管道：查询 → 过滤 → 排序
cat data.json | datalens query '.users' | datalens filter --stdin --field active --op '==' --value true

# 与 curl 配合：直接查询 API 响应
curl -s https://api.example.com/users | datalens query '.data[*].email'

# 与 grep 配合：先查询再搜索
datalens query data.json '.users[*]' | grep -i 'alice'

# 管道输入 pretty 打印
cat data.json | datalens pretty --indent 4

# 批量查询多个文件的结果汇总
for f in configs/*.json; do datalens query "$f" '.version'; done
```

#### ✅ JSON Schema 验证

DataLens CLI 内置了完整的 JSON Schema 验证器（纯 Python 标准库实现，无需 `jsonschema` 第三方包），支持以下关键字：

- **类型约束**：`type`、`enum`、`const`
- **对象约束**：`required`、`properties`、`additionalProperties`、`patternProperties`、`minProperties`、`maxProperties`
- **数组约束**：`items`、`additionalItems`、`minItems`、`maxItems`、`uniqueItems`、`contains`
- **数值约束**：`minimum`、`maximum`、`exclusiveMinimum`、`exclusiveMaximum`、`multipleOf`
- **字符串约束**：`minLength`、`maxLength`、`pattern`、`format`（email / uri / date-time）
- **组合关键字**：`allOf`、`anyOf`、`oneOf`、`not`
- **引用**：`$ref`（同文档内引用解析）、`definitions` / `$defs`

```bash
# 验证数据文件
datalens validate data.json --schema schema.json

# 静默模式（仅输出错误）
datalens validate data.json --schema schema.json --quiet
```

---

### 💡 设计思路与迭代规划

#### 🎯 为什么坚持零依赖核心？

DataLens CLI 的核心功能（JSON 处理、查询、过滤、diff、merge、stats、pretty print、validate）全部基于 Python 标准库实现，不引入任何第三方依赖。这一设计决策出于以下考虑：

1. **安装即用**：`pip install` 后无需额外安装任何包，降低上手门槛
2. **环境兼容**：在受限环境（CI/CD、容器、嵌入式系统）中也能稳定运行
3. **依赖隔离**：不会与项目自身的依赖产生版本冲突
4. **安全可控**：减少供应链攻击面，所有代码均可审计

YAML 和 TOML 支持作为可选依赖，按需安装即可。

#### 🏗️ 关键设计决策

- **ANSI 原生着色**：终端彩色输出完全基于 `\033` 转义序列实现，无需 `rich`、`colorama` 等库
- **自动格式检测**：根据文件扩展名自动识别 JSON/YAML/TOML/CSV 格式
- **stdin 智能解析**：管道输入时自动尝试多种格式解析
- **深度比较算法**：diff 命令对字典列表自动查找匹配键（优先 `id`、`name` 等），而非简单的位置比较

#### 🗺️ 未来规划

- [ ] 交互式查询模式（REPL）
- [ ] `watch` 命令：监听文件变化自动执行操作
- [ ] `transform` 命令：基于表达式的数据转换
- [ ] 输出格式增强（表格、树形视图）
- [ ] Shell 自动补全（bash/zsh/fish）
- [ ] 性能优化：大文件流式处理
- [ ] 插件系统：支持自定义运算符和输出格式

---

### 📦 打包与部署

#### pip 安装

```bash
# 从源码安装
git clone https://github.com/your-org/datalens-cli.git
cd datalens-cli
pip install .

# 安装全部可选依赖
pip install ".[all]"

# 升级
pip install --upgrade .
```

#### 开发环境搭建

```bash
# 克隆仓库
git clone https://github.com/your-org/datalens-cli.git
cd datalens-cli

# 安装开发依赖
pip install -e ".[all]"
pip install pytest

# 运行测试
pytest tests/ -v

# 运行单个命令
datalens query data.json '.users[0].name'
```

---

### 🤝 贡献指南

我们欢迎并感谢所有形式的贡献！无论是提交 Bug 报告、功能建议，还是直接发起 Pull Request。

#### 📝 提交 Issue

- 使用清晰、描述性的标题
- 附上复现步骤和最小示例数据
- 说明运行环境（Python 版本、操作系统）

#### 🔀 提交 Pull Request

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 编写代码并添加对应的单元测试
4. 确保所有测试通过：`pytest tests/ -v`
5. 提交变更：`git commit -m 'feat: add your feature'`
6. 推送分支：`git push origin feature/your-feature`
7. 发起 Pull Request

#### 📋 代码规范

- 遵循 PEP 8 编码规范
- 所有公共函数需包含完整的 docstring
- 新功能必须附带单元测试
- 保持核心功能的零外部依赖原则

---

### 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。

```
MIT License

Copyright (c) 2024 DataLens CLI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<a id="繁體中文"></a>

## 繁體中文

### 🎉 專案介紹

**DataLens CLI** 是一款專為開發者打造的輕量級終端資料處理工具，能夠對 JSON、YAML、TOML、CSV 等結構化資料進行查詢、轉換、驗證、比較和統計分析。

在日常開發工作中，我們經常需要快速查看、過濾或比較 JSON 設定檔和 API 回應資料。傳統做法要麼用文字編輯器手動翻找，要麼依賴 `jq`、`yq` 等工具——但它們各自只擅長一種格式，學習曲線陡峭，組合使用時體驗割裂。DataLens CLI 的誕生正是為了解決這些痛點：**一個工具，涵蓋所有主流結構化資料格式，開箱即用。**

#### ✨ 與 jq / yq / jless 的差異化亮點

| 特性 | DataLens CLI | jq | yq | jless |
|------|:-----------:|:--:|:--:|:-----:|
| JSON 支援 | ✅ | ✅ | ✅ | ✅ |
| YAML 支援 | ✅ | ❌ | ✅ | ❌ |
| TOML 支援 | ✅ | ❌ | ✅ | ❌ |
| CSV 支援 | ✅ | ❌ | ✅ | ❌ |
| Schema 推斷 | ✅ | ❌ | ❌ | ❌ |
| JSON Schema 驗證 | ✅ | ❌ | ❌ | ❌ |
| 深度資料比較 (diff) | ✅ | ❌ | ❌ | ❌ |
| 資料統計與視覺化 | ✅ | ❌ | ❌ | ❌ |
| 管道 (pipe) 支援 | ✅ | ✅ | ✅ | ❌ |
| 零外部依賴（核心） | ✅ | ✅ | ❌ | ❌ |
| Python 原生 | ✅ | ❌ | ❌ | ❌ |

#### 💡 設計靈感

DataLens CLI 的靈感來源於日常開發中頻繁遇到的小痛點：查看一個巢狀很深的 JSON 設定、對比兩份 API 回應的差異、從 YAML 檔案中提取特定欄位……我們希望有一個**統一、輕量、無需安裝一堆依賴**的命令列工具來搞定這些事情。它不需要成為下一個 `jq`，而是做 `jq` 不擅長的事——跨格式、一站式的開發者友善資料處理體驗。

---

### ✨ 核心特性

DataLens CLI 提供 **10 個核心命令**，涵蓋資料處理全流程：

| 命令 | 說明 | 範例 |
|------|------|------|
| 🔍 **query** | 智慧查詢引擎，支援點表示法、萬用字元、遞迴下降、過濾運算式 | `datalens query data.json 'users[0].name'` |
| 🔄 **convert** | JSON / YAML / TOML / CSV 格式互轉 | `datalens convert data.json --to yaml` |
| ✅ **validate** | 基於 JSON Schema 的資料驗證（純 stdlib 實作） | `datalens validate data.json --schema schema.json` |
| 📋 **schema** | 從樣本資料自動推斷 JSON Schema，智慧識別 email/uri/uuid 等格式 | `datalens schema data.json` |
| 📊 **diff** | 深度資料比較，彩色終端輸出，支援鍵值匹配 | `datalens diff old.json new.json` |
| 🎨 **pretty** | 語法高亮美化列印，ANSI 原生著色（無外部依賴） | `datalens pretty data.json` |
| 🔗 **merge** | 深度合併多個資料檔案，5 種合併策略可選 | `datalens merge config1.json config2.json` |
| 🧹 **filter** | 15+ 運算子的資料過濾與排序，支援巢狀欄位 | `datalens filter data.json --field age --op '>' --value 25` |
| 📈 **stats** | 資料結構統計分析，含視覺化柱狀圖 | `datalens stats data.json` |
| 📦 **batch** | 批次檔案處理，一次操作多個檔案 | `datalens batch query *.json --expr '.version'` |

---

### 🚀 快速開始

#### 📋 環境需求

- **Python 3.8+**（核心功能零外部依賴，僅使用標準庫）
- 可選依賴：`pyyaml`（YAML 支援）、`toml`（Python < 3.11 的 TOML 支援）

#### 📦 安裝

```bash
# 從原始碼安裝（核心功能，無額外依賴）
pip install .

# 安裝並包含 YAML 和 TOML 支援
pip install ".[all]"

# 或分別安裝可選依賴
pip install ".[yaml]"   # YAML 支援
pip install ".[toml]"   # TOML 支援（Python < 3.11）
```

#### ⚡ 快速體驗

```bash
# 查看版本
datalens -v

# 查詢資料
datalens query data.json 'users[0].name'
datalens query data.json 'users[*].email'
datalens query data.json '..version'

# 格式轉換
datalens convert data.json --to yaml
datalens convert data.json --to csv

# Schema 推斷
datalens schema data.json

# 資料比較
datalens diff old.json new.json

# 資料過濾
datalens filter data.json --field age --op '>' --value 25

# 資料統計
datalens stats data.json

# 深度合併
datalens merge config1.json config2.json

# 管道操作
cat data.json | datalens query '.users' | datalens filter --stdin --field active --op '==' --value true
```

---

### 📖 詳細使用指南

#### 🔍 進階查詢範例

```bash
# 點表示法存取巢狀欄位
datalens query config.json 'database.host'

# 陣列索引（支援負數索引）
datalens query data.json 'users[0].name'
datalens query data.json 'users[-1].name'

# 萬用字元展開所有陣列元素
datalens query data.json 'users[*].name'
datalens query data.json 'users[*].email'

# 遞迴下降——在所有層級搜尋指定欄位
datalens query data.json '..version'
datalens query data.json '..id'

# 過濾運算式
datalens query data.json 'users[?age>30]'
datalens query data.json 'items[?name=~^Widget]'

# JSONPath 風格的根選擇器
datalens query data.json '$.users[*].name'

# 原始輸出（無格式化）
datalens query data.json 'users[0].name' --raw

# 輸出到檔案
datalens query data.json 'users' -o users_only.json
```

#### 🧹 過濾運算子一覽

`filter` 命令支援 **15+ 種運算子**，滿足各種資料篩選需求：

| 運算子 | 別名 | 說明 | 範例 |
|--------|------|------|------|
| `==` | `eq` | 等於 | `--op '==' --value 'Alice'` |
| `!=` | `ne` | 不等於 | `--op '!=' --value 0` |
| `>` | `gt` | 大於 | `--op '>' --value 25` |
| `<` | `lt` | 小於 | `--op '<' --value 100` |
| `>=` | `ge` | 大於等於 | `--op '>=' --value 18` |
| `<=` | `le` | 小於等於 | `--op '<=' --value 65` |
| `contains` | | 包含（字串/陣列） | `--op contains --value 'admin'` |
| `!contains` | | 不包含 | `--op '!contains' --value 'test'` |
| `starts` | `startswith` | 前綴匹配 | `--op starts --value 'https'` |
| `ends` | `endswith` | 後綴匹配 | `--op ends --value '.json'` |
| `in` | | 包含於列表 | `--op in --value '["a","b"]'` |
| `!in` | | 不包含於列表 | `--op '!in' --value '["x"]'` |
| `regex` | `=~` | 正則匹配 | `--op regex --value '^\d+$'` |
| `type` | | 類型檢查 | `--op type --value 'string'` |
| `exists` | | 欄位存在 | `--op exists` |
| `!exists` | | 欄位不存在 | `--op '!exists'` |

```bash
# 組合使用：過濾 + 排序 + 分頁 + 欄位選擇
datalens filter data.json \
  --field age --op '>' --value 25 \
  --sort age --desc \
  --limit 10 --offset 0 \
  --select name,email,age

# 巢狀欄位過濾（點表示法）
datalens filter data.json --field address.city --op '==' --value 'Taipei'
```

#### 🔗 合併策略

`merge` 命令提供 **5 種合併策略**，靈活應對不同場景：

| 策略 | 說明 | 適用場景 |
|------|------|----------|
| `overwrite` | 覆蓋（預設） | 後者覆蓋前者，列表直接替換 |
| `append` | 附加 | 列表元素附加到末尾 |
| `prepend` | 前置 | 列表元素插入到開頭 |
| `unique` | 去重合併 | 列表合併並去除重複項 |
| `deep` | 深度合併 | 按索引逐元素深度合併列表 |

```bash
# 預設覆蓋合併
datalens merge default.json override.json

# 列表附加合併
datalens merge base.json extra.json --strategy append

# 去重合併
datalens merge tags1.json tags2.json --strategy unique

# 深度合併（按索引合併列表元素）
datalens merge config1.json config2.json --strategy deep

# 合併多個檔案
datalens merge config1.json config2.json config3.json -o merged.json
```

#### 🔗 管道用法

DataLens CLI 完美支援 Unix 管道，可與其他命令列工具無縫協作：

```bash
# 基本管道查詢
cat data.json | datalens query '.users[*].name'

# 多級管道：查詢 → 過濾 → 排序
cat data.json | datalens query '.users' | datalens filter --stdin --field active --op '==' --value true

# 與 curl 配合：直接查詢 API 回應
curl -s https://api.example.com/users | datalens query '.data[*].email'

# 與 grep 配合：先查詢再搜尋
datalens query data.json '.users[*]' | grep -i 'alice'

# 管道輸入 pretty 列印
cat data.json | datalens pretty --indent 4

# 批次查詢多個檔案的結果彙總
for f in configs/*.json; do datalens query "$f" '.version'; done
```

#### ✅ JSON Schema 驗證

DataLens CLI 內建了完整的 JSON Schema 驗證器（純 Python 標準庫實作，無需 `jsonschema` 第三方套件），支援以下關鍵字：

- **類型約束**：`type`、`enum`、`const`
- **物件約束**：`required`、`properties`、`additionalProperties`、`patternProperties`、`minProperties`、`maxProperties`
- **陣列約束**：`items`、`additionalItems`、`minItems`、`maxItems`、`uniqueItems`、`contains`
- **數值約束**：`minimum`、`maximum`、`exclusiveMinimum`、`exclusiveMaximum`、`multipleOf`
- **字串約束**：`minLength`、`maxLength`、`pattern`、`format`（email / uri / date-time）
- **組合關鍵字**：`allOf`、`anyOf`、`oneOf`、`not`
- **參照**：`$ref`（同文件內參照解析）、`definitions` / `$defs`

```bash
# 驗證資料檔案
datalens validate data.json --schema schema.json

# 靜默模式（僅輸出錯誤）
datalens validate data.json --schema schema.json --quiet
```

---

### 💡 設計思路與迭代規劃

#### 🎯 為什麼堅持零依賴核心？

DataLens CLI 的核心功能（JSON 處理、查詢、過濾、diff、merge、stats、pretty print、validate）全部基於 Python 標準庫實作，不引入任何第三方依賴。這一設計決策出於以下考量：

1. **安裝即用**：`pip install` 後無需額外安裝任何套件，降低上手門檻
2. **環境相容**：在受限環境（CI/CD、容器、嵌入式系統）中也能穩定運作
3. **依賴隔離**：不會與專案自身的依賴產生版本衝突
4. **安全可控**：減少供應鏈攻擊面，所有程式碼均可審計

YAML 和 TOML 支援作為可選依賴，按需安裝即可。

#### 🏗️ 關鍵設計決策

- **ANSI 原生著色**：終端彩色輸出完全基於 `\033` 跳脫序列實作，無需 `rich`、`colorama` 等函式庫
- **自動格式偵測**：根據副檔名自動識別 JSON/YAML/TOML/CSV 格式
- **stdin 智慧解析**：管道輸入時自動嘗試多種格式解析
- **深度比較演算法**：diff 命令對字典列表自動尋找匹配鍵（優先 `id`、`name` 等），而非簡單的位置比較

#### 🗺️ 未來規劃

- [ ] 互動式查詢模式（REPL）
- [ ] `watch` 命令：監聽檔案變化自動執行操作
- [ ] `transform` 命令：基於運算式的資料轉換
- [ ] 輸出格式增強（表格、樹狀檢視）
- [ ] Shell 自動補全（bash/zsh/fish）
- [ ] 效能最佳化：大檔案串流處理
- [ ] 外掛系統：支援自訂運算子和輸出格式

---

### 📦 打包與部署

#### pip 安裝

```bash
# 從原始碼安裝
git clone https://github.com/your-org/datalens-cli.git
cd datalens-cli
pip install .

# 安裝全部可選依賴
pip install ".[all]"

# 升級
pip install --upgrade .
```

#### 開發環境建置

```bash
# 複製倉庫
git clone https://github.com/your-org/datalens-cli.git
cd datalens-cli

# 安裝開發依賴
pip install -e ".[all]"
pip install pytest

# 執行測試
pytest tests/ -v

# 執行單一命令
datalens query data.json '.users[0].name'
```

---

### 🤝 貢獻指南

我們歡迎並感謝所有形式的貢獻！無論是提交 Bug 回報、功能建議，還是直接發起 Pull Request。

#### 📝 提交 Issue

- 使用清晰、描述性的標題
- 附上重現步驟和最小範例資料
- 說明執行環境（Python 版本、作業系統）

#### 🔀 提交 Pull Request

1. Fork 本倉庫
2. 建立特性分支：`git checkout -b feature/your-feature`
3. 撰寫程式碼並新增對應的單元測試
4. 確保所有測試通過：`pytest tests/ -v`
5. 提交變更：`git commit -m 'feat: add your feature'`
6. 推送分支：`git push origin feature/your-feature`
7. 發起 Pull Request

#### 📋 程式碼規範

- 遵循 PEP 8 編碼規範
- 所有公共函式需包含完整的 docstring
- 新功能必須附帶單元測試
- 保持核心功能的零外部依賴原則

---

### 📄 開源授權

本專案基於 [MIT License](LICENSE) 開源。

```
MIT License

Copyright (c) 2024 DataLens CLI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<a id="english"></a>

## English

### 🎉 Project Introduction

**DataLens CLI** is a lightweight terminal data processing tool built for developers, capable of querying, converting, validating, comparing, and statistically analyzing structured data in JSON, YAML, TOML, and CSV formats.

In day-to-day development, we frequently need to quickly inspect, filter, or compare JSON configuration files and API response data. The traditional approach is either manually searching through a text editor or relying on tools like `jq` and `yq` -- but each only excels at one format, has a steep learning curve, and provides a fragmented experience when combined. DataLens CLI was born to solve exactly these pain points: **one tool that covers all mainstream structured data formats, ready to use out of the box.**

#### ✨ Differentiation Highlights vs jq / yq / jless

| Feature | DataLens CLI | jq | yq | jless |
|---------|:-----------:|:--:|:--:|:-----:|
| JSON support | ✅ | ✅ | ✅ | ✅ |
| YAML support | ✅ | ❌ | ✅ | ❌ |
| TOML support | ✅ | ❌ | ✅ | ❌ |
| CSV support | ✅ | ❌ | ✅ | ❌ |
| Schema inference | ✅ | ❌ | ❌ | ❌ |
| JSON Schema validation | ✅ | ❌ | ❌ | ❌ |
| Deep data comparison (diff) | ✅ | ❌ | ❌ | ❌ |
| Data statistics & visualization | ✅ | ❌ | ❌ | ❌ |
| Pipe support | ✅ | ✅ | ✅ | ❌ |
| Zero external dependencies (core) | ✅ | ✅ | ❌ | ❌ |
| Python native | ✅ | ❌ | ❌ | ❌ |

#### 💡 Inspiration

DataLens CLI was inspired by the small, recurring pain points we encounter every day as developers: inspecting a deeply nested JSON config, comparing two API responses, extracting a specific field from a YAML file... We wanted **one unified, lightweight tool that requires no pile of dependencies** to handle all of these. It doesn't aim to be the next `jq` -- rather, it does what `jq` doesn't: a cross-format, all-in-one, developer-friendly data processing experience.

---

### ✨ Core Features

DataLens CLI provides **10 core commands** covering the entire data processing workflow:

| Command | Description | Example |
|---------|-------------|---------|
| 🔍 **query** | Smart query engine with dot notation, wildcards, recursive descent, and filter expressions | `datalens query data.json 'users[0].name'` |
| 🔄 **convert** | Convert between JSON / YAML / TOML / CSV formats | `datalens convert data.json --to yaml` |
| ✅ **validate** | JSON Schema-based data validation (pure stdlib implementation) | `datalens validate data.json --schema schema.json` |
| 📋 **schema** | Auto-infer JSON Schema from sample data, with smart detection of email/uri/uuid formats | `datalens schema data.json` |
| 📊 **diff** | Deep data comparison with colorized terminal output and key-based matching | `datalens diff old.json new.json` |
| 🎨 **pretty** | Syntax-highlighted pretty printing with native ANSI coloring (no external deps) | `datalens pretty data.json` |
| 🔗 **merge** | Deep merge multiple data files with 5 strategies to choose from | `datalens merge config1.json config2.json` |
| 🧹 **filter** | Data filtering and sorting with 15+ operators, supporting nested field access | `datalens filter data.json --field age --op '>' --value 25` |
| 📈 **stats** | Data structure statistical analysis with visual bar charts | `datalens stats data.json` |
| 📦 **batch** | Batch file processing -- apply one operation across multiple files | `datalens batch query *.json --expr '.version'` |

---

### 🚀 Quick Start

#### 📋 Requirements

- **Python 3.8+** (core functionality has zero external dependencies, using only the standard library)
- Optional dependencies: `pyyaml` (YAML support), `toml` (TOML support for Python < 3.11)

#### 📦 Installation

```bash
# Install from source (core features, no extra dependencies)
pip install .

# Install with YAML and TOML support
pip install ".[all]"

# Or install optional dependencies separately
pip install ".[yaml]"   # YAML support
pip install ".[toml]"   # TOML support (Python < 3.11)
```

#### ⚡ Quick Examples

```bash
# Check version
datalens -v

# Query data
datalens query data.json 'users[0].name'
datalens query data.json 'users[*].email'
datalens query data.json '..version'

# Format conversion
datalens convert data.json --to yaml
datalens convert data.json --to csv

# Schema inference
datalens schema data.json

# Data comparison
datalens diff old.json new.json

# Data filtering
datalens filter data.json --field age --op '>' --value 25

# Data statistics
datalens stats data.json

# Deep merge
datalens merge config1.json config2.json

# Pipe operations
cat data.json | datalens query '.users' | datalens filter --stdin --field active --op '==' --value true
```

---

### 📖 Detailed Usage Guide

#### 🔍 Advanced Query Examples

```bash
# Dot notation for nested field access
datalens query config.json 'database.host'

# Array indexing (supports negative indices)
datalens query data.json 'users[0].name'
datalens query data.json 'users[-1].name'

# Wildcard to expand all array elements
datalens query data.json 'users[*].name'
datalens query data.json 'users[*].email'

# Recursive descent -- search for a field at all nesting levels
datalens query data.json '..version'
datalens query data.json '..id'

# Filter expressions
datalens query data.json 'users[?age>30]'
datalens query data.json 'items[?name=~^Widget]'

# JSONPath-style root selector
datalens query data.json '$.users[*].name'

# Raw output (no formatting)
datalens query data.json 'users[0].name' --raw

# Output to file
datalens query data.json 'users' -o users_only.json
```

#### 🧹 Filter Operators Reference

The `filter` command supports **15+ operators** for all kinds of data filtering needs:

| Operator | Alias | Description | Example |
|----------|-------|-------------|---------|
| `==` | `eq` | Equal to | `--op '==' --value 'Alice'` |
| `!=` | `ne` | Not equal to | `--op '!=' --value 0` |
| `>` | `gt` | Greater than | `--op '>' --value 25` |
| `<` | `lt` | Less than | `--op '<' --value 100` |
| `>=` | `ge` | Greater than or equal | `--op '>=' --value 18` |
| `<=` | `le` | Less than or equal | `--op '<=' --value 65` |
| `contains` | | Contains (string/array) | `--op contains --value 'admin'` |
| `!contains` | | Does not contain | `--op '!contains' --value 'test'` |
| `starts` | `startswith` | Starts with | `--op starts --value 'https'` |
| `ends` | `endswith` | Ends with | `--op ends --value '.json'` |
| `in` | | In list | `--op in --value '["a","b"]'` |
| `!in` | | Not in list | `--op '!in' --value '["x"]'` |
| `regex` | `=~` | Regex match | `--op regex --value '^\d+$'` |
| `type` | | Type check | `--op type --value 'string'` |
| `exists` | | Field exists | `--op exists` |
| `!exists` | | Field does not exist | `--op '!exists'` |

```bash
# Combine: filter + sort + pagination + field selection
datalens filter data.json \
  --field age --op '>' --value 25 \
  --sort age --desc \
  --limit 10 --offset 0 \
  --select name,email,age

# Nested field filtering (dot notation)
datalens filter data.json --field address.city --op '==' --value 'London'
```

#### 🔗 Merge Strategies

The `merge` command offers **5 merge strategies** for different scenarios:

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `overwrite` | Overwrite (default) | Later values replace earlier ones; lists are replaced entirely |
| `append` | Append | List items are appended to the end |
| `prepend` | Prepend | List items are inserted at the beginning |
| `unique` | Deduplicated merge | Lists are merged with duplicate items removed |
| `deep` | Deep merge | Lists are merged element-by-element by index |

```bash
# Default overwrite merge
datalens merge default.json override.json

# Append merge for lists
datalens merge base.json extra.json --strategy append

# Unique merge (deduplicate)
datalens merge tags1.json tags2.json --strategy unique

# Deep merge (merge list elements by index)
datalens merge config1.json config2.json --strategy deep

# Merge multiple files
datalens merge config1.json config2.json config3.json -o merged.json
```

#### 🔗 Pipe Usage

DataLens CLI has full Unix pipe support and integrates seamlessly with other command-line tools:

```bash
# Basic pipe query
cat data.json | datalens query '.users[*].name'

# Multi-stage pipeline: query -> filter -> sort
cat data.json | datalens query '.users' | datalens filter --stdin --field active --op '==' --value true

# Work with curl: query API responses directly
curl -s https://api.example.com/users | datalens query '.data[*].email'

# Work with grep: query then search
datalens query data.json '.users[*]' | grep -i 'alice'

# Pipe into pretty print
cat data.json | datalens pretty --indent 4

# Aggregate results across multiple files
for f in configs/*.json; do datalens query "$f" '.version'; done
```

#### ✅ JSON Schema Validation

DataLens CLI includes a complete JSON Schema validator implemented purely with the Python standard library (no `jsonschema` third-party package needed). It supports the following keywords:

- **Type constraints**: `type`, `enum`, `const`
- **Object constraints**: `required`, `properties`, `additionalProperties`, `patternProperties`, `minProperties`, `maxProperties`
- **Array constraints**: `items`, `additionalItems`, `minItems`, `maxItems`, `uniqueItems`, `contains`
- **Number constraints**: `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`, `multipleOf`
- **String constraints**: `minLength`, `maxLength`, `pattern`, `format` (email / uri / date-time)
- **Composition keywords**: `allOf`, `anyOf`, `oneOf`, `not`
- **References**: `$ref` (same-document reference resolution), `definitions` / `$defs`

```bash
# Validate a data file
datalens validate data.json --schema schema.json

# Quiet mode (errors only)
datalens validate data.json --schema schema.json --quiet
```

---

### 💡 Design Philosophy & Roadmap

#### 🎯 Why Zero-Dependency Core?

All core features of DataLens CLI (JSON processing, querying, filtering, diff, merge, stats, pretty printing, and validation) are built entirely on the Python standard library with no third-party dependencies. This design decision was driven by:

1. **Install and go**: After `pip install`, no additional packages are needed -- lowering the barrier to entry
2. **Environment compatibility**: Runs reliably in constrained environments (CI/CD pipelines, containers, embedded systems)
3. **Dependency isolation**: No version conflicts with your project's own dependencies
4. **Security and auditability**: Reduced supply chain attack surface; every line of code is auditable

YAML and TOML support are optional dependencies that can be installed on demand.

#### 🏗️ Key Design Decisions

- **Native ANSI coloring**: Terminal color output is implemented entirely with `\033` escape sequences -- no `rich`, `colorama`, or similar libraries
- **Automatic format detection**: File formats (JSON/YAML/TOML/CSV) are auto-detected by extension
- **Smart stdin parsing**: When receiving piped input, multiple formats are tried automatically
- **Deep comparison algorithm**: The diff command automatically finds matching keys (prioritizing `id`, `name`, etc.) for lists of dicts, rather than simple positional comparison

#### 🗺️ Roadmap

- [ ] Interactive query mode (REPL)
- [ ] `watch` command: monitor file changes and auto-execute operations
- [ ] `transform` command: expression-based data transformation
- [ ] Enhanced output formats (table view, tree view)
- [ ] Shell completions (bash/zsh/fish)
- [ ] Performance optimization: streaming for large files
- [ ] Plugin system: custom operators and output formatters

---

### 📦 Packaging & Deployment

#### pip Installation

```bash
# Install from source
git clone https://github.com/your-org/datalens-cli.git
cd datalens-cli
pip install .

# Install with all optional dependencies
pip install ".[all]"

# Upgrade
pip install --upgrade .
```

#### Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/datalens-cli.git
cd datalens-cli

# Install development dependencies
pip install -e ".[all]"
pip install pytest

# Run tests
pytest tests/ -v

# Run a single command
datalens query data.json '.users[0].name'
```

---

### 🤝 Contributing

We welcome and appreciate contributions of all forms -- whether it's filing a bug report, suggesting a feature, or submitting a Pull Request.

#### 📝 Filing an Issue

- Use a clear, descriptive title
- Include reproduction steps and minimal sample data
- Specify your environment (Python version, operating system)

#### 🔀 Submitting a Pull Request

1. Fork this repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Write your code and add corresponding unit tests
4. Make sure all tests pass: `pytest tests/ -v`
5. Commit your changes: `git commit -m 'feat: add your feature'`
6. Push the branch: `git push origin feature/your-feature`
7. Open a Pull Request

#### 📋 Code Style

- Follow PEP 8 conventions
- All public functions must include complete docstrings
- New features must come with unit tests
- Maintain the zero-external-dependency principle for core functionality

---

### 📄 License

This project is released under the [MIT License](LICENSE).

```
MIT License

Copyright (c) 2024 DataLens CLI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
