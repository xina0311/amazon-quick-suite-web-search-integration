# Implementation Plan: Zhipu Web Search Provider

## Overview

本实现计划将智谱 Web Search API 集成到 Amazon Quick Suite AI Search Integration 项目中。实现遵循现有 provider（博查、秘塔）的模式，确保一致性和可维护性。

## Tasks

- [x] 1. 创建 Zhipu Provider 目录结构
  - 在 `providers/` 下创建 `zhipu/` 目录
  - 创建必要的文件占位符
  - _Requirements: 1.1_

- [x] 2. 实现 Lambda 函数核心逻辑
  - [x] 2.1 创建 zhipu_lambda_function.py 基础结构
    - 定义 PROVIDER_NAME, API_KEY, API_ENDPOINT 常量
    - 实现环境变量读取和验证
    - _Requirements: 1.2, 1.3_
  
  - [x] 2.2 实现 lambda_handler 主函数
    - 解析输入参数（query, max_results, search_engine, recency_filter, domain_filter, content_size）
    - 实现参数验证和默认值处理
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  
  - [x] 2.3 实现 call_zhipu_api 函数
    - 构建请求头（Authorization, Content-Type）
    - 构建请求体（参数名称映射）
    - 发送 POST 请求到智谱 API
    - 处理超时和异常
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  
  - [x] 2.4 实现 format_results 函数
    - 格式化搜索结果为 Markdown
    - 处理 search_intent 字段
    - 处理空结果情况
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  
  - [x] 2.5 实现辅助函数
    - success_response: MCP 格式成功响应
    - error_response: 错误响应
    - _Requirements: 4.5_

- [x] 3. Checkpoint - 验证 Lambda 函数逻辑
  - 确保代码无语法错误
  - 本地测试基本功能
  - 如有问题请询问用户

- [x] 4. 创建部署脚本
  - [x] 4.1 创建 deploy.sh 脚本
    - 检查 ZHIPU_API_KEY 环境变量
    - 创建 IAM 角色 ZhipuLambdaExecutionRole
    - 打包 Lambda 代码和依赖
    - 创建/更新 Lambda 函数
    - 保存 ZHIPU_LAMBDA_ARN 到 config.txt
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [x] 4.2 创建 add_target.py 脚本
    - 读取 config.txt 配置
    - 定义 MCP Tool Schema
    - 创建/更新 Gateway Target
    - 保存 ZHIPU_TARGET_ID 到 config.txt
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.6, 6.7, 6.8, 6.9_

- [x] 5. 创建测试脚本
  - [x] 5.1 创建 test_lambda.sh
    - 使用 aws lambda invoke 测试函数
    - 显示格式化的响应结果
    - _Requirements: 7.1, 7.2_
  
  - [x] 5.2 创建 test_target.sh
    - 端到端测试 Gateway Target
    - _Requirements: 7.3, 7.4_

- [x] 6. Checkpoint - 验证部署脚本
  - 确保脚本可执行
  - 检查脚本逻辑正确性
  - 如有问题请询问用户

- [x] 7. 创建文档
  - [x] 7.1 创建 README.md
    - 功能概述和特点
    - API Key 获取说明
    - 部署步骤
    - 参数说明
    - 使用示例
    - 故障排除
    - 与其他 Provider 对比
    - 成本估算
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_

- [x] 8. 更新项目主文档
  - [x] 8.1 更新根目录 README.md
    - 添加智谱 Provider 到 Provider 列表
    - 添加部署说明
    - 更新架构图

- [x] 9. Final Checkpoint - 完整性验证
  - 确保所有文件创建完成
  - 确保代码风格与现有 Provider 一致
  - 如有问题请询问用户

- [ ]* 10. 属性测试（可选）
  - [ ]* 10.1 创建测试目录和配置
    - 创建 tests/ 目录
    - 创建 conftest.py
  
  - [ ]* 10.2 实现属性测试
    - **Property 1: Valid query triggers API call**
    - **Validates: Requirements 2.1**
  
  - [ ]* 10.3 实现属性测试
    - **Property 2: Empty query rejection**
    - **Validates: Requirements 2.2**
  
  - [ ]* 10.4 实现属性测试
    - **Property 3: Invalid parameter fallback to defaults**
    - **Validates: Requirements 2.4, 2.5, 2.6, 2.7**
  
  - [ ]* 10.5 实现属性测试
    - **Property 4: Result formatting completeness**
    - **Validates: Requirements 4.1, 4.2, 4.5, 4.6**
  
  - [ ]* 10.6 实现属性测试
    - **Property 5: Empty results handling**
    - **Validates: Requirements 4.4**

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
