# 心语 (Xinyu) - 心理健康社区应用

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Tailwind CSS](https://img.shields.io/badge/Frontend-Tailwind_CSS-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)



**心语 (Xinyu)** 是一款专为心理健康设计的社区应用，旨在提供一个温暖、私密且专业的倾诉空间。通过 AI 陪伴、专业咨询和社区互助，帮助用户缓解焦虑、管理情绪并实现自我成长。
## 效果展示
<img width="436" height="837" alt="example_1" src="https://github.com/user-attachments/assets/401a3f6b-4602-4be9-8ac1-9e0d1e1e72a6" />
<img width="434" height="839" alt="example_7" src="https://github.com/user-attachments/assets/9c3fc391-287b-4343-b297-ba09fc45cacd" />
<img width="435" height="837" alt="example_6" src="https://github.com/user-attachments/assets/a074a69d-f056-4bbb-9bc5-9f4bfd4f09d6" />
<img width="434" height="837" alt="example_5" src="https://github.com/user-attachments/assets/39009b9e-5a8a-44d0-aaf2-b85d0e87f35c" />
<img width="435" height="838" alt="example_4" src="https://github.com/user-attachments/assets/bf5a8977-0e50-4c24-a89c-203d154e1cf9" />
<img width="436" height="835" alt="example_3" src="https://github.com/user-attachments/assets/baa25e7f-0ad7-4ea2-986d-2ce26137c215" />
<img width="434" height="839" alt="example_2" src="https://github.com/user-attachments/assets/41c6e32c-c8ae-4bf6-b479-06dcc35a7f30" />

## 🌟 核心功能

-   **AI 倾诉助手**：24/7 在线陪伴，提供即时的情感支持与引导。
-   **温暖社区**：瀑布流式的内容展示，分享心情动态，寻求社区互助。
-   **预先测评**：多维度的心理测评工具，全方位了解自己的心理状态。
-   **专业咨询**：对接实名认证的专业心理咨询师，提供一对一深度咨询。
-   **冥想放松**：内置多种冥想音频与练习，助你快速进入放松状态。
-   **即时通讯**：安全的私信系统，与好友或咨询师保持沟通。
-   **完善的后台管理**：基于 FastAPI 的高性能后端，支持用户权限、内容审核、支付系统等。

## 🚀 技术架构

### 前端 (Frontend)

-   **核心**：HTML5, JavaScript (ES6+)
-   **框架**：Tailwind CSS (响应式设计)
-   **字体**：Google Fonts (Nunito Sans)
-   **图标**：SVG Icons

### 后端 (Backend)

-   **引擎**：Python 3.10+
-   **框架**：FastAPI
-   **数据库**：SQLAlchemy (ORM), SQLite (默认) / MySQL
-   **迁移**：Alembic
-   **缓存**：Redis (用于验证码及高频数据缓存)
-   **认证**：JWT (PyJWT/python-jose), Passlib (BCrypt 密码哈希)
-   **验证**：Pydantic V2

## 🛠️ 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/xinyu-app.git
cd xinyu-app
```

### 2. 后端配置

1. 进入后端目录：

   ```bash
   cd backend
   ```

2. 创建并激活虚拟环境：

   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

4. 配置环境变量：
   复制 `.env.example` 为 `.env` 并根据实际情况修改配置。

5. 启动后端服务器：

   ```bash
   python main.py
   # 或者使用 uvicorn
   uvicorn app.main:app --reload
   ```

### 3. 前端访问

前端采用纯 HTML + CDN 模式，无需复杂的构建过程。

- 直接在浏览器中打开根目录下的 `index.html`。
- 或者使用 Live Server 插件（VS Code）进行预览。

*注意：确保后端服务已启动（默认端口 8000），否则前端 API 请求将失败。*

## 📁 项目结构

```text
.
├── backend/                # 后端源码
│   ├── app/                # 核心逻辑
│   │   ├── models/         # 数据库模型
│   │   ├── routers/        # API 路由
│   │   ├── schemas/        # 数据验证(Pydantic)
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具类
│   ├── alembic/            # 数据库迁移脚本
│   ├── requirements.txt    # 依赖列表
│   └── main.py             # 入口文件
├── index.html              # 首页
├── ai-chat.html            # AI 聊天页
├── assessment.html         # 心理测评页
├── counselor-detail.html   # 咨询师详情页
├── discover.html           # 发现/社区页
├── meditation.html         # 冥想页
├── messages.html           # 消息中心
├── profile.html            # 个人中心
└── README.md               # 项目说明
```

## 📜 许可协议

本项目采用 [MIT License](LICENSE) 许可协议。

## 📬 联系方式

如有任何疑问或建议，欢迎提交 Issues 或 Pull Requests。
