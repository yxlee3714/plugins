# os-nclink - NC-Link OPNsense Plugin

基于国家标准《智能工厂数控机床互联接口规范》的 Python 实现。

当前版本支持：
- 注册（Register）
- 模型侦测（Probe/Query）
- 数据查询（Query）
- 数据采样（Sample）
- 状态通知（Notify/State）

后续将逐步支持 Method、Event、动态采样等功能。

## 安装后使用
1. 在 OPNsense Web 界面安装 os-nclink
2. System → Services → NC-Link 启动服务
3. 配置监听端口和模型文件路径（后续版本支持 GUI 配置）
