# 心语后端设计文档

> 创建日期：2026-01-15

## 概述

心语是一个心理健康类社区应用，提供内容分享、咨询师服务、实时消息等功能。本文档描述后端系统的技术架构与实现方案。

## 技术选型

| 项目 | 选择 | 理由 |
|------|------|------|
| 框架 | Python FastAPI | 异步支持、自动API文档、类型安全 |
| 数据库 | MySQL | 成熟稳定、社区支持好 |
| ORM | SQLAlchemy 2.0 | Python首选ORM |
| 认证 | JWT | 无状态、易扩展 |
| 实时通信 | WebSocket | 原生支持 |
| 缓存 | Redis | 验证码、会话缓存 |

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (index.html)                      │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI 后端服务                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │  用户    │ │  内容   │ │  咨询   │ │  消息   │ │  支付   │ │
│  │  模块    │ │  模块   │ │  模块   │ │  模块   │ │  模块   │ │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └───┬────┘ │
└───────┼──────────┼──────────┼──────────┼──────────┼────────┘
        │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────┐
│                        MySQL 数据库                          │
│   users | posts | counselors | messages | orders | ...      │
└─────────────────────────────────────────────────────────────┘
```

## 目录结构

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── models/              # 数据模型 (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── counselor.py
│   │   ├── message.py
│   │   └── order.py
│   ├── schemas/             # Pydantic 验证
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── post.py
│   │   └── ...
│   ├── routers/             # API 路由
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── posts.py
│   │   ├── counselors.py
│   │   ├── messages.py
│   │   └── payments.py
│   ├── services/            # 业务逻辑
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── sms_service.py
│   │   └── ...
│   └── utils/               # 工具函数
│       ├── __init__.py
│       ├── security.py
│       └── dependencies.py
├── alembic/                 # 数据库迁移
├── uploads/                 # 本地文件存储
├── requirements.txt
├── .env.example
└── .env
```

## 数据库模型

### users - 用户表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| phone | VARCHAR(20) | 手机号，唯一，可空 |
| email | VARCHAR(100) | 邮箱，唯一，可空 |
| password_hash | VARCHAR(255) | 密码哈希，可空 |
| wechat_openid | VARCHAR(100) | 微信openid，唯一，可空 |
| nickname | VARCHAR(50) | 昵称 |
| avatar | VARCHAR(255) | 头像URL |
| role | ENUM | user/counselor/admin |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### posts - 帖子表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| user_id | INT | 外键 → users |
| title | VARCHAR(100) | 标题 |
| content | TEXT | 正文 |
| cover_image | VARCHAR(255) | 封面图URL |
| category | VARCHAR(20) | 分类 |
| like_count | INT | 点赞数 |
| collect_count | INT | 收藏数 |
| comment_count | INT | 评论数 |
| status | ENUM | draft/published/hidden |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### likes - 点赞表
| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | INT | 外键 → users |
| post_id | INT | 外键 → posts |
| created_at | DATETIME | 创建时间 |

### collections - 收藏表
| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | INT | 外键 → users |
| post_id | INT | 外键 → posts |
| created_at | DATETIME | 创建时间 |

### comments - 评论表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| post_id | INT | 外键 → posts |
| user_id | INT | 外键 → users |
| parent_id | INT | 父评论ID，可空 |
| content | TEXT | 评论内容 |
| created_at | DATETIME | 创建时间 |

### counselor_profiles - 咨询师资料表
| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | INT | 外键 → users，主键 |
| title | VARCHAR(50) | 职称 |
| introduction | TEXT | 简介 |
| price | DECIMAL(10,2) | 咨询单价 |
| rating | DECIMAL(2,1) | 评分 |
| consult_count | INT | 咨询次数 |
| is_verified | BOOLEAN | 是否认证 |

### appointments - 预约表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| user_id | INT | 外键 → users |
| counselor_id | INT | 外键 → users |
| scheduled_time | DATETIME | 预约时间 |
| duration | INT | 时长（分钟） |
| status | ENUM | pending/confirmed/completed/cancelled |
| amount | DECIMAL(10,2) | 金额 |
| created_at | DATETIME | 创建时间 |

### messages - 消息表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| sender_id | INT | 外键 → users |
| receiver_id | INT | 外键 → users |
| content | TEXT | 消息内容 |
| msg_type | ENUM | text/image/system |
| is_read | BOOLEAN | 是否已读 |
| created_at | DATETIME | 创建时间 |

### orders - 订单表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| user_id | INT | 外键 → users |
| appointment_id | INT | 外键 → appointments |
| amount | DECIMAL(10,2) | 金额 |
| payment_method | ENUM | wechat/alipay |
| status | ENUM | pending/paid/refunded |
| paid_at | DATETIME | 支付时间 |
| created_at | DATETIME | 创建时间 |

## API接口设计

### 用户模块 `/api/v1/auth`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /register/phone | 手机号注册 |
| POST | /register/email | 邮箱注册 |
| POST | /login/phone | 手机号+验证码登录 |
| POST | /login/email | 邮箱+密码登录 |
| POST | /login/wechat | 微信登录 |
| POST | /send-code | 发送验证码 |
| GET | /me | 获取当前用户信息 |
| PUT | /me | 更新用户资料 |

### 内容模块 `/api/v1/posts`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / | 获取帖子列表 |
| GET | /{id} | 获取帖子详情 |
| POST | / | 发布帖子 |
| PUT | /{id} | 编辑帖子 |
| DELETE | /{id} | 删除帖子 |
| POST | /{id}/like | 点赞 |
| DELETE | /{id}/like | 取消点赞 |
| POST | /{id}/collect | 收藏 |
| DELETE | /{id}/collect | 取消收藏 |
| GET | /{id}/comments | 获取评论列表 |
| POST | /{id}/comments | 发表评论 |

### 咨询模块 `/api/v1/counselors`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / | 咨询师列表 |
| GET | /{id} | 咨询师详情 |
| POST | /apply | 申请成为咨询师 |
| GET | /{id}/schedule | 获取可预约时间 |

### 预约模块 `/api/v1/appointments`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | / | 创建预约 |
| GET | /my | 我的预约列表 |
| PUT | /{id}/confirm | 确认预约 |
| PUT | /{id}/cancel | 取消预约 |

### 消息模块 `/api/v1/messages`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /conversations | 会话列表 |
| GET | /{user_id} | 消息记录 |
| POST | / | 发送消息 |
| WS | /ws/{user_id} | 实时消息 |

### 支付模块 `/api/v1/payments`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /create | 创建支付订单 |
| POST | /callback/wechat | 微信支付回调 |
| GET | /orders | 订单列表 |

### 文件上传 `/api/v1/upload`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /image | 上传图片 |

## 认证机制

### JWT Token
- 算法：HS256
- 有效期：7天
- 载荷：user_id, role, exp, iat

### Token结构
```json
{
    "sub": "user_id",
    "role": "user/counselor/admin",
    "exp": 1234567890,
    "iat": 1234567890
}
```

### 安全措施
- 密码：bcrypt哈希
- 验证码：6位数字，5分钟有效
- 限流：登录接口5次/分钟
- SQL注入：ORM参数化查询
- CORS：配置允许域名

## 第三方服务

### 短信服务
- 推荐：阿里云短信 / 腾讯云短信
- 开发模式：验证码固定为123456

### 微信登录
- 需要：APP_ID, APP_SECRET
- 开发模式：模拟openid

### 支付服务
- 推荐：微信支付 / 支付宝
- 开发模式：直接标记成功

## 开发计划

### Phase 1: 基础框架
- 项目初始化、目录结构
- 数据库连接、模型定义
- 配置管理、环境变量

### Phase 2: 用户系统
- 注册/登录接口
- JWT认证中间件
- 用户信息接口

### Phase 3: 内容系统
- 帖子CRUD
- 点赞/收藏/评论
- 分页与筛选

### Phase 4: 咨询系统
- 咨询师列表与详情
- 预约功能

### Phase 5: 消息系统
- WebSocket实时消息
- 消息记录存储

### Phase 6: 支付与完善
- 支付接口（模拟）
- 文件上传
- 接口测试

## 依赖清单

```
fastapi==0.109.0
uvicorn==0.27.0
python-multipart==0.0.6
sqlalchemy==2.0.25
pymysql==1.1.0
alembic==1.13.1
python-jose==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
redis==5.0.1
httpx==0.26.0
websockets==12.0
```
