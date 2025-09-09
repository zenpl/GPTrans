# GPTrans - 智能文档翻译排版系统

GPTrans 是一个完整的 OCR 到中文翻译和排版解决方案，专门设计用于将德语、瑞典语文档智能转换为高质量的中文排版文档。

## 🌟 核心特性

### 📄 智能 OCR 识别
- 自动识别文档版面结构（标题、段落、脚注、图注等）
- 支持多栏排版检测和阅读顺序重构
- 兼容图片格式：JPG、PNG、TIFF、PDF

### 🌐 专业翻译
- 支持德语（de）、瑞典语（sv）到简体中文（zh-CN）翻译
- 可配置术语表确保专业术语准确性
- 智能长度控制，支持压缩翻译模式

### 🎨 中文智能排版
- **Mode B 容器内重排**：在原文检测容器内重新排版中文
- 中文断行规则：`line-break: strict` + 禁则处理
- 自动拟合循环（Fit Loop）：自动调整字间距、行高等参数适应文本长度
- 孤寡行控制：`orphans`/`widows` 规则防止不美观的断行

### 📦 多格式导出
- **PDF**：嵌入中文字体（Noto Serif/Sans CJK SC）
- **ePub3**：语义化 HTML，支持导航和字体嵌入
- 脚注/图注锚定：确保引用关系正确

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js UI    │    │  FastAPI Backend│    │  Redis Workers  │
│   (前端界面)     │◄───┤   (API 服务)    │◄───┤   (后台处理)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│   PostgreSQL   │◄─────────────┘
                         │    (数据库)     │
                         └─────────────────┘
```

### 技术栈
- **前端**：Next.js 14 + TypeScript + Tailwind CSS
- **后端**：FastAPI + SQLAlchemy + Pydantic
- **队列**：Redis + RQ (Redis Queue)
- **数据库**：PostgreSQL
- **排版引擎**：WeasyPrint (HTML/CSS Paged Media)
- **中文处理**：PyICU (断行) + 自定义禁则规则

## 🚀 快速开始

### 前置要求
- Docker & Docker Compose
- 8GB+ 可用内存
- 2GB+ 磁盘空间

### 一键启动
```bash
git clone <repository-url>
cd GPTrans

# 复制环境配置
cp .env.example .env

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

服务地址：
- 前端界面：http://localhost:3000
- API 文档：http://localhost:8000/docs
- 数据库：localhost:5432
- Redis：localhost:6379

### 手动安装（开发模式）

#### 后端依赖
```bash
cd app
pip install -r infra/requirements.txt

# 安装中文字体支持
sudo apt-get install fonts-noto-cjk  # Ubuntu/Debian
# 或
brew install font-noto-serif-cjk-sc   # macOS
```

#### 前端依赖
```bash
cd app/frontend
npm install
```

#### 启动服务
```bash
# 启动数据库和 Redis
docker-compose up postgres redis -d

# 启动后端
cd app
uvicorn backend.main:app --reload --port 8000

# 启动工作进程
python workers/main.py

# 启动前端
cd frontend
npm run dev
```

## 📖 使用指南

### 基本工作流程

1. **上传文档**
   - 拖拽或选择文件（JPG/PNG/TIFF/PDF）
   - 系统自动创建项目

2. **OCR 识别**
   - 自动或手动触发 OCR 处理
   - 识别文本块和版面结构

3. **翻译处理**
   - 配置术语表（可选）
   - 批量翻译文本块
   - 支持手动编辑译文

4. **排版预览**
   - 实时预览中文排版效果
   - 查看容器框和文本布局
   - 调整有问题的译文

5. **导出文档**
   - 选择 PDF/ePub 格式
   - 下载最终成果

### 高级功能

#### 术语表管理
```csv
src,tgt,case_sensitive,notes
Typografie,字体排印学,false,Typography as a field
Renaissance,文艺复兴,true,Historical period
```

#### 压缩翻译
当译文过长无法适应原文容器时，系统会：
1. 调整字间距（-0.02em 到 +0.01em）
2. 调整行高（1.45 到 1.6）
3. 尝试压缩字体（condensed）
4. 触发压缩翻译（目标长度 ≤ 90%）

#### 环境变量配置
```bash
# 翻译服务商
TRANSLATION_PROVIDER=mock          # mock | openai | claude
OPENAI_API_KEY=your_key_here       # OpenAI API 密钥
ANTHROPIC_API_KEY=your_key_here    # Claude API 密钥

# OCR 服务商  
OCR_PROVIDER=mock                  # mock | google_vision
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# 文件限制
MAX_FILE_SIZE=104857600            # 100MB
MAX_PAGES_PER_BOOK=500             # 最大页数
```

## 🧪 测试

### 运行测试套件
```bash
cd app
pytest tests/ -v

# 特定测试
pytest tests/test_fit_loop.py -v
pytest tests/test_chinese_typography.py -v
pytest tests/test_translation.py -v
```

### 测试覆盖
- ✅ 拟合循环算法
- ✅ 中文排版规则
- ✅ 翻译服务
- ✅ OCR 规范化
- ✅ API 端点（集成测试）

## 🎯 中文排版规则详解

### 断行规则
- **严格断行**：`line-break: strict`
- **词语保持**：`word-break: keep-all`
- **两端对齐**：`text-justify: inter-ideograph`

### 禁则字符
- **不能行首**：`!%),.:;?]}¢°·ˇˉ―‖'"…‰′″›℃∶、。〉》」』】〕〗〞︰︱︳﹐﹑﹒﹕﹖﹗﹚﹜﹞！），．：；？｜｝︶`
- **不能行尾**：`([{·'"〈《「『【〔〖〝﹙﹛﹝（｛｟｠￠￡￥`

### 字体配置
- **正文**：Noto Serif CJK SC（衬线）
- **标题**：Noto Sans CJK SC（无衬线）
- **嵌入**：PDF 和 ePub 中完整嵌入字体

## 📁 项目结构

```
GPTrans/
├── app/
│   ├── frontend/          # Next.js 前端
│   │   ├── src/
│   │   │   ├── app/       # App Router 页面
│   │   │   ├── components/# React 组件
│   │   │   ├── lib/       # API 客户端
│   │   │   └── types/     # TypeScript 类型
│   │   └── package.json
│   ├── backend/           # FastAPI 后端
│   │   ├── api/           # API 路由
│   │   ├── models.py      # 数据库模型
│   │   ├── services/      # 业务逻辑
│   │   └── ocr_providers/ # OCR 服务提供商
│   ├── workers/           # RQ 工作进程
│   ├── shared/            # 共享代码
│   │   ├── schemas.py     # Pydantic 模型
│   │   ├── constants.py   # 常量配置
│   │   └── utils/         # 工具函数
│   ├── infra/             # 基础设施
│   │   ├── docker/        # Dockerfile
│   │   └── requirements.txt
│   ├── samples/           # 示例数据
│   └── tests/             # 测试用例
├── data/                  # 数据存储
├── docker-compose.yml
└── README.md
```

## 🔧 自动拟合循环（Fit Loop）

核心算法用于处理中文译文长度与原文容器不匹配的问题：

### 压缩策略（文本过长）
1. **字间距收紧**：`0em → -0.02em`
2. **行高减小**：`1.5 → 1.45`  
3. **字体变窄**：`normal → condensed`
4. **字重减轻**：`normal → 300`
5. **压缩翻译**：调用 `translate_concise()` 生成更短译文

### 扩展策略（文本过短）
1. **行高增加**：`1.5 → 1.6`
2. **字间距放宽**：`0em → +0.01em`
3. **段间距调整**：增加 `margin-top/bottom`

### 收敛条件
- 无溢出且密度合理（40%+ 填充率）
- 达到最大迭代次数（10次）
- 允许最多 2% 溢出作为最终回退

## 🚦 限制与注意事项

### 功能限制
- **仅支持 Mode B**：容器内重排，不支持图像叠加模式
- **语言支持**：德语、瑞典语 → 中文（可扩展其他语言）
- **文件格式**：图片和 PDF，不支持 Word/PowerPoint

### 系统要求
- **内存**：推荐 8GB+（处理大型 PDF 时）
- **存储**：每本书约需 50-200MB 空间
- **字体**：需要 Noto CJK 字体包（约 100MB）

### 隐私保护
- **本地部署**：支持完全离线运行
- **数据隔离**：项目数据存储在独立目录
- **可选云服务**：翻译 API 可选，默认使用 mock 模拟

## 🤝 贡献指南

### 开发环境设置
```bash
# 安装开发工具
pip install black isort flake8
npm install -g prettier eslint

# 代码格式化
black app/
isort app/
prettier --write app/frontend/src/

# 类型检查
mypy app/backend/
npm run type-check --prefix app/frontend/
```

### 提交规范
- 功能：`feat: 添加新功能描述`
- 修复：`fix: 修复问题描述`  
- 文档：`docs: 更新文档`
- 测试：`test: 添加测试用例`

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🆘 常见问题

### Q: 为什么选择 WeasyPrint 而不是 LaTeX？
A: WeasyPrint 基于 HTML/CSS，更容易与 Web 技术栈集成，同时支持复杂的中文排版需求。未来可能会增加 LaTeX 后端选项。

### Q: 可以处理扫描质量较差的文档吗？
A: 当前使用 mock OCR，生产环境建议配置 Google Vision API 或其他高质量 OCR 服务。

### Q: 如何添加新的语言对？
A: 扩展 `LanguageCode` 枚举和 `MockTranslationProvider`，添加对应的翻译规则即可。

### Q: 支持批量处理多个文档吗？
A: 当前版本需要逐个上传处理，批量处理功能在开发计划中。

### Q: 可以自定义中文字体吗？
A: 修改 `shared/constants.py` 中的 `CHINESE_FONTS` 配置，并确保容器内安装了相应字体。

---

**🎉 开始使用 GPTrans，让文档翻译和排版变得简单高效！**

如有问题或建议，请提交 [Issues](issues) 或参与 [Discussions](discussions)。