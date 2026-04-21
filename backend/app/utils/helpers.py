import re
import math
import hashlib
import httpx
import asyncio
from typing import List, Optional, Dict
from functools import lru_cache
from pypinyin import lazy_pinyin, Style


TECH_GLOSSARY: Dict[str, str] = {
    '正则表达式': 'regular-expression',
    '正则': 'regex',
    '编程': 'programming',
    '教程': 'tutorial',
    '入门': 'introduction',
    '进阶': 'advanced',
    '基础': 'basics',
    '高级': 'advanced',
    '数据库': 'database',
    '设计': 'design',
    '优化': 'optimization',
    '性能': 'performance',
    '安全': 'security',
    '网络': 'network',
    '算法': 'algorithm',
    '数据结构': 'data-structure',
    '前端': 'frontend',
    '后端': 'backend',
    '全栈': 'fullstack',
    '框架': 'framework',
    '库': 'library',
    '接口': 'api',
    'API': 'api',
    'RESTful': 'restful',
    'GraphQL': 'graphql',
    '微服务': 'microservice',
    '容器': 'container',
    'Docker': 'docker',
    'Kubernetes': 'kubernetes',
    '云原生': 'cloud-native',
    'DevOps': 'devops',
    'CI/CD': 'ci-cd',
    '测试': 'testing',
    '单元测试': 'unit-testing',
    '集成测试': 'integration-testing',
    '部署': 'deployment',
    '监控': 'monitoring',
    '日志': 'logging',
    '缓存': 'caching',
    'Redis': 'redis',
    'MySQL': 'mysql',
    'PostgreSQL': 'postgresql',
    'MongoDB': 'mongodb',
    'NoSQL': 'nosql',
    'SQL': 'sql',
    '索引': 'index',
    '事务': 'transaction',
    '并发': 'concurrency',
    '异步': 'async',
    '同步': 'sync',
    '线程': 'thread',
    '进程': 'process',
    '内存': 'memory',
    'CPU': 'cpu',
    'GPU': 'gpu',
    '机器学习': 'machine-learning',
    '深度学习': 'deep-learning',
    '人工智能': 'artificial-intelligence',
    'AI': 'ai',
    '神经网络': 'neural-network',
    '自然语言处理': 'nlp',
    '计算机视觉': 'computer-vision',
    '大数据': 'big-data',
    '数据分析': 'data-analysis',
    '可视化': 'visualization',
    '爬虫': 'web-scraping',
    '自动化': 'automation',
    '脚本': 'script',
    '命令行': 'command-line',
    '终端': 'terminal',
    '编辑器': 'editor',
    'IDE': 'ide',
    '调试': 'debugging',
    '重构': 'refactoring',
    '代码审查': 'code-review',
    '版本控制': 'version-control',
    'Git': 'git',
    'GitHub': 'github',
    '分支': 'branch',
    '合并': 'merge',
    '冲突': 'conflict',
    '提交': 'commit',
    '推送': 'push',
    '拉取': 'pull',
    '克隆': 'clone',
    '仓库': 'repository',
    '开源': 'open-source',
    '许可证': 'license',
    '文档': 'documentation',
    '注释': 'comment',
    '变量': 'variable',
    '函数': 'function',
    '类': 'class',
    '对象': 'object',
    '继承': 'inheritance',
    '多态': 'polymorphism',
    '封装': 'encapsulation',
    '抽象': 'abstraction',
    '接口': 'interface',
    '模块': 'module',
    '包': 'package',
    '依赖': 'dependency',
    '配置': 'configuration',
    '环境': 'environment',
    '变量': 'variable',
    '常量': 'constant',
    '类型': 'type',
    '数组': 'array',
    '列表': 'list',
    '字典': 'dictionary',
    '集合': 'set',
    '元组': 'tuple',
    '字符串': 'string',
    '数字': 'number',
    '布尔': 'boolean',
    '空值': 'null',
    '异常': 'exception',
    '错误': 'error',
    '警告': 'warning',
    '调试': 'debug',
    '日志': 'log',
    '请求': 'request',
    '响应': 'response',
    '状态码': 'status-code',
    '头部': 'header',
    '主体': 'body',
    '参数': 'parameter',
    '返回值': 'return-value',
    '回调': 'callback',
    '事件': 'event',
    '监听': 'listener',
    '触发': 'trigger',
    '绑定': 'bind',
    '解绑': 'unbind',
    '渲染': 'render',
    '组件': 'component',
    '页面': 'page',
    '路由': 'route',
    '导航': 'navigation',
    '菜单': 'menu',
    '按钮': 'button',
    '表单': 'form',
    '输入': 'input',
    '输出': 'output',
    '验证': 'validation',
    '校验': 'validation',
    '加密': 'encryption',
    '解密': 'decryption',
    '哈希': 'hash',
    '签名': 'signature',
    '证书': 'certificate',
    '认证': 'authentication',
    '授权': 'authorization',
    '登录': 'login',
    '注册': 'register',
    '注销': 'logout',
    '用户': 'user',
    '角色': 'role',
    '权限': 'permission',
    '会话': 'session',
    'Cookie': 'cookie',
    'Token': 'token',
    'JWT': 'jwt',
    'OAuth': 'oauth',
    '跨域': 'cors',
    '代理': 'proxy',
    '负载均衡': 'load-balancing',
    '高可用': 'high-availability',
    '容灾': 'disaster-recovery',
    '备份': 'backup',
    '恢复': 'recovery',
    '迁移': 'migration',
    '升级': 'upgrade',
    '降级': 'downgrade',
    '回滚': 'rollback',
    '发布': 'release',
    '版本': 'version',
    '更新': 'update',
    '补丁': 'patch',
    '修复': 'fix',
    '漏洞': 'vulnerability',
    '攻击': 'attack',
    '防御': 'defense',
    '防火墙': 'firewall',
    '入侵检测': 'intrusion-detection',
    '渗透测试': 'penetration-testing',
    '安全审计': 'security-audit',
    '合规': 'compliance',
    '隐私': 'privacy',
    '加密货币': 'cryptocurrency',
    '区块链': 'blockchain',
    '智能合约': 'smart-contract',
    '去中心化': 'decentralization',
    '物联网': 'iot',
    '嵌入式': 'embedded',
    '驱动': 'driver',
    '内核': 'kernel',
    '操作系统': 'operating-system',
    'Linux': 'linux',
    'Windows': 'windows',
    'macOS': 'macos',
    '移动端': 'mobile',
    'iOS': 'ios',
    'Android': 'android',
    '小程序': 'mini-program',
    '公众号': 'official-account',
    '微信': 'wechat',
    '支付': 'payment',
    '订单': 'order',
    '商品': 'product',
    '购物车': 'shopping-cart',
    '用户中心': 'user-center',
    '消息': 'message',
    '通知': 'notification',
    '推送': 'push-notification',
    '邮件': 'email',
    '短信': 'sms',
    '验证码': 'verification-code',
    '二维码': 'qr-code',
    '扫码': 'scan',
    '分享': 'share',
    '评论': 'comment',
    '点赞': 'like',
    '收藏': 'favorite',
    '关注': 'follow',
    '粉丝': 'follower',
    '动态': 'feed',
    '朋友圈': 'moments',
    '直播': 'live-streaming',
    '视频': 'video',
    '音频': 'audio',
    '图片': 'image',
    '文件': 'file',
    '上传': 'upload',
    '下载': 'download',
    '导入': 'import',
    '导出': 'export',
    '打印': 'print',
    '预览': 'preview',
    '搜索': 'search',
    '筛选': 'filter',
    '排序': 'sort',
    '分页': 'pagination',
    '懒加载': 'lazy-loading',
    '无限滚动': 'infinite-scroll',
    '骨架屏': 'skeleton-screen',
    '加载': 'loading',
    '刷新': 'refresh',
    '重试': 'retry',
    '超时': 'timeout',
    '断网': 'offline',
    '弱网': 'weak-network',
    '兼容性': 'compatibility',
    '响应式': 'responsive',
    '自适应': 'adaptive',
    '移动优先': 'mobile-first',
    '渐进增强': 'progressive-enhancement',
    '优雅降级': 'graceful-degradation',
    '用户体验': 'user-experience',
    '交互设计': 'interaction-design',
    '界面设计': 'interface-design',
    '原型': 'prototype',
    '线框图': 'wireframe',
    '设计稿': 'design-mockup',
    '切图': 'slicing',
    '标注': 'annotation',
    '规范': 'specification',
    '标准': 'standard',
    '最佳实践': 'best-practice',
    '设计模式': 'design-pattern',
    '架构': 'architecture',
    '系统设计': 'system-design',
    '技术选型': 'technology-selection',
    '技术栈': 'tech-stack',
    '解决方案': 'solution',
    '案例': 'case-study',
    '实战': 'practical',
    '项目': 'project',
    '工程': 'engineering',
    '构建': 'build',
    '打包': 'bundle',
    '压缩': 'compression',
    '混淆': 'obfuscation',
    '优化': 'optimization',
    '性能优化': 'performance-optimization',
    '首屏加载': 'first-paint',
    '白屏时间': 'white-screen-time',
    '可交互时间': 'time-to-interactive',
    '核心指标': 'core-metrics',
    '监控告警': 'monitoring-alerting',
    '故障排查': 'troubleshooting',
    '性能分析': 'performance-analysis',
    '内存泄漏': 'memory-leak',
    'CPU占用': 'cpu-usage',
    '磁盘': 'disk',
    '带宽': 'bandwidth',
    '流量': 'traffic',
    '并发量': 'concurrency',
    '吞吐量': 'throughput',
    '延迟': 'latency',
    '响应时间': 'response-time',
    '可用性': 'availability',
    '可靠性': 'reliability',
    '扩展性': 'scalability',
    '可维护性': 'maintainability',
    '可测试性': 'testability',
    '代码质量': 'code-quality',
    '技术债务': 'technical-debt',
    '重构': 'refactoring',
    '遗留系统': 'legacy-system',
    '迁移': 'migration',
    '技术升级': 'technology-upgrade',
    '团队协作': 'team-collaboration',
    '敏捷开发': 'agile',
    'Scrum': 'scrum',
    '看板': 'kanban',
    '迭代': 'iteration',
    '冲刺': 'sprint',
    '需求': 'requirement',
    '需求分析': 'requirement-analysis',
    '产品': 'product',
    '产品经理': 'product-manager',
    '开发': 'development',
    '测试': 'testing',
    '运维': 'operations',
    '运营': 'operations',
    '市场': 'marketing',
    '销售': 'sales',
    '客服': 'customer-service',
    '反馈': 'feedback',
    '建议': 'suggestion',
    '问题': 'issue',
    '解决方案': 'solution',
    '总结': 'summary',
    '心得': 'insights',
    '经验': 'experience',
    '技巧': 'tips',
    '陷阱': 'pitfalls',
    '常见问题': 'faq',
    '面试': 'interview',
    '简历': 'resume',
    '职业发展': 'career',
    '学习': 'learning',
    '成长': 'growth',
    '实践': 'practice',
    '理论': 'theory',
    '原理': 'principle',
    '源码': 'source-code',
    '解析': 'analysis',
    '深入': 'deep-dive',
    '浅析': 'overview',
    '详解': 'detailed-explanation',
    '指南': 'guide',
    '手册': 'manual',
    '参考': 'reference',
    '资源': 'resource',
    '工具': 'tool',
    '插件': 'plugin',
    '扩展': 'extension',
    '模板': 'template',
    '脚手架': 'scaffold',
    '生成器': 'generator',
    '脚手架': 'boilerplate',
    '示例': 'example',
    '演示': 'demo',
    '代码片段': 'snippet',
    '快捷键': 'shortcut',
    '效率': 'efficiency',
    '自动化': 'automation',
    '批处理': 'batch-processing',
    '脚本': 'scripting',
    '命令': 'command',
    '快捷方式': 'shortcut',
    '工作流': 'workflow',
    '流程': 'process',
    '规范': 'standard',
    '约定': 'convention',
    '风格': 'style',
    '格式': 'format',
    '编码': 'encoding',
    '字符集': 'charset',
    'Unicode': 'unicode',
    'UTF-8': 'utf-8',
    'ASCII': 'ascii',
    '转义': 'escape',
    '序列化': 'serialization',
    '反序列化': 'deserialization',
    'JSON': 'json',
    'XML': 'xml',
    'YAML': 'yaml',
    'TOML': 'toml',
    'CSV': 'csv',
    'Excel': 'excel',
    'Word': 'word',
    'PDF': 'pdf',
    'Markdown': 'markdown',
    'LaTeX': 'latex',
    '富文本': 'rich-text',
    '编辑器': 'editor',
    '语法高亮': 'syntax-highlighting',
    '代码格式化': 'code-formatting',
    '代码检查': 'linting',
    '静态分析': 'static-analysis',
    '动态分析': 'dynamic-analysis',
    '代码覆盖率': 'code-coverage',
    '测试驱动开发': 'tdd',
    '行为驱动开发': 'bdd',
    '领域驱动设计': 'ddd',
    '测试金字塔': 'test-pyramid',
    '冒烟测试': 'smoke-testing',
    '回归测试': 'regression-testing',
    '压力测试': 'stress-testing',
    '性能测试': 'performance-testing',
    '安全测试': 'security-testing',
    '兼容性测试': 'compatibility-testing',
    '端到端测试': 'e2e-testing',
    '快照测试': 'snapshot-testing',
    'Mock': 'mock',
    'Stub': 'stub',
    'Spy': 'spy',
    'Fake': 'fake',
    '测试替身': 'test-double',
    '测试夹具': 'test-fixture',
    '测试数据': 'test-data',
    '测试环境': 'test-environment',
    '预发布': 'staging',
    '生产环境': 'production',
    '灰度发布': 'canary-release',
    '蓝绿部署': 'blue-green-deployment',
    '金丝雀发布': 'canary-deployment',
    'A/B测试': 'ab-testing',
    '功能开关': 'feature-toggle',
    '实验': 'experiment',
    '数据分析': 'data-analytics',
    '用户行为': 'user-behavior',
    '埋点': 'tracking',
    '上报': 'reporting',
    '统计': 'statistics',
    '报表': 'report',
    '仪表盘': 'dashboard',
    '可视化': 'visualization',
    '图表': 'chart',
    '折线图': 'line-chart',
    '柱状图': 'bar-chart',
    '饼图': 'pie-chart',
    '散点图': 'scatter-plot',
    '热力图': 'heatmap',
    '地图': 'map',
    '地理信息': 'gis',
    '定位': 'location',
    '导航': 'navigation',
    '地图服务': 'map-service',
    '位置服务': 'lbs',
    '周边': 'nearby',
    '推荐': 'recommendation',
    '个性化': 'personalization',
    '智能推荐': 'smart-recommendation',
    '协同过滤': 'collaborative-filtering',
    '内容推荐': 'content-based-recommendation',
    '搜索引擎': 'search-engine',
    '全文检索': 'full-text-search',
    '倒排索引': 'inverted-index',
    '分词': 'word-segmentation',
    '词云': 'word-cloud',
    '关键词': 'keyword',
    '标签': 'tag',
    '分类': 'category',
    '归档': 'archive',
    '时间线': 'timeline',
    '历史记录': 'history',
    '版本历史': 'version-history',
    '操作日志': 'operation-log',
    '审计日志': 'audit-log',
    '访问日志': 'access-log',
    '错误日志': 'error-log',
    '慢查询': 'slow-query',
    '性能日志': 'performance-log',
    '业务日志': 'business-log',
    '系统日志': 'system-log',
    '应用日志': 'application-log',
    '日志收集': 'log-collection',
    '日志分析': 'log-analysis',
    '日志存储': 'log-storage',
    '日志查询': 'log-query',
    '日志告警': 'log-alerting',
    '日志可视化': 'log-visualization',
    'ELK': 'elk-stack',
    'Elasticsearch': 'elasticsearch',
    'Logstash': 'logstash',
    'Kibana': 'kibana',
    'Fluentd': 'fluentd',
    'Filebeat': 'filebeat',
    'Prometheus': 'prometheus',
    'Grafana': 'grafana',
    'Zabbix': 'zabbix',
    'Nagios': 'nagios',
    '监控指标': 'metrics',
    '告警规则': 'alerting-rules',
    '通知渠道': 'notification-channel',
    '值班': 'on-call',
    '故障响应': 'incident-response',
    '故障恢复': 'incident-recovery',
    '故障复盘': 'postmortem',
    '根因分析': 'root-cause-analysis',
    '持续改进': 'continuous-improvement',
    '知识库': 'knowledge-base',
    '文档中心': 'documentation-center',
    'Wiki': 'wiki',
    '协作平台': 'collaboration-platform',
    '项目管理': 'project-management',
    '任务跟踪': 'task-tracking',
    '缺陷跟踪': 'bug-tracking',
    '需求管理': 'requirement-management',
    '版本管理': 'version-management',
    '发布管理': 'release-management',
    '变更管理': 'change-management',
    '配置管理': 'configuration-management',
    '知识管理': 'knowledge-management',
    '团队管理': 'team-management',
    '人员管理': 'people-management',
    '绩效管理': 'performance-management',
    '目标管理': 'okr',
    'OKR': 'okr',
    'KPI': 'kpi',
    '敏捷教练': 'agile-coach',
    'Scrum Master': 'scrum-master',
    '技术负责人': 'tech-lead',
    '架构师': 'architect',
    '技术总监': 'cto',
    'CTO': 'cto',
    '技术经理': 'engineering-manager',
    '项目经理': 'project-manager',
    '产品负责人': 'product-owner',
    '业务分析师': 'business-analyst',
    '用户体验设计师': 'ux-designer',
    '用户界面设计师': 'ui-designer',
    '全栈工程师': 'fullstack-engineer',
    '前端工程师': 'frontend-engineer',
    '后端工程师': 'backend-engineer',
    '测试工程师': 'qa-engineer',
    '运维工程师': 'devops-engineer',
    '数据工程师': 'data-engineer',
    '算法工程师': 'algorithm-engineer',
    '机器学习工程师': 'ml-engineer',
    '安全工程师': 'security-engineer',
    '技术写作': 'technical-writing',
    '技术博客': 'tech-blog',
    '开源项目': 'open-source-project',
    '技术社区': 'tech-community',
    '技术分享': 'tech-talk',
    '技术会议': 'tech-conference',
    '技术演讲': 'tech-presentation',
    '技术文章': 'tech-article',
    '技术书籍': 'tech-book',
    '在线课程': 'online-course',
    '视频教程': 'video-tutorial',
    '互动教程': 'interactive-tutorial',
    '编程练习': 'coding-exercise',
    '编程挑战': 'coding-challenge',
    '算法竞赛': 'algorithm-competition',
    '黑客马拉松': 'hackathon',
    '编程语言': 'programming-language',
    'Python': 'python',
    'JavaScript': 'javascript',
    'TypeScript': 'typescript',
    'Java': 'java',
    'C++': 'cpp',
    'C#': 'csharp',
    'Go': 'golang',
    'Rust': 'rust',
    'Ruby': 'ruby',
    'PHP': 'php',
    'Swift': 'swift',
    'Kotlin': 'kotlin',
    'Scala': 'scala',
    'R': 'r-language',
    'MATLAB': 'matlab',
    'Julia': 'julia',
    'Perl': 'perl',
    'Lua': 'lua',
    'Shell': 'shell',
    'PowerShell': 'powershell',
    'Batch': 'batch',
    'Vim': 'vim',
    'Emacs': 'emacs',
    'VS Code': 'vscode',
    'Visual Studio': 'visual-studio',
    'IntelliJ IDEA': 'intellij-idea',
    'PyCharm': 'pycharm',
    'WebStorm': 'webstorm',
    'Sublime Text': 'sublime-text',
    'Atom': 'atom',
    'Notepad++': 'notepad-plus',
    'Eclipse': 'eclipse',
    'NetBeans': 'netbeans',
    'Xcode': 'xcode',
    'Android Studio': 'android-studio',
}

_translation_cache: Dict[str, str] = {}


def apply_glossary(text: str) -> str:
    for cn, en in sorted(TECH_GLOSSARY.items(), key=lambda x: -len(x[0])):
        if cn in text:
            text = text.replace(cn, f' {en} ')
    return text.strip()


async def translate_with_google(text: str, client: httpx.AsyncClient) -> Optional[str]:
    try:
        response = await client.get(
            'https://translate.googleapis.com/translate_a/single',
            params={
                'client': 'gtx',
                'sl': 'zh-CN',
                'tl': 'en',
                'dt': 't',
                'q': text
            },
            timeout=3.0
        )
        
        if response.status_code == 200:
            data = response.json()
            if data and data[0]:
                translated = ''.join([part[0] for part in data[0] if part[0]])
                if translated and translated.lower() != text.lower():
                    return translated
    except Exception:
        pass
    return None


async def translate_with_mymemory(text: str, client: httpx.AsyncClient) -> Optional[str]:
    try:
        response = await client.get(
            'https://api.mymemory.translated.net/get',
            params={'q': text, 'langpair': 'zh|en'},
            timeout=3.0
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('responseStatus') == 200:
                translated = data.get('responseData', {}).get('translatedText', '')
                if translated and translated.lower() != text.lower():
                    return translated
    except Exception:
        pass
    return None


async def translate_to_english(text: str) -> str:
    if not text or not text.strip():
        return ''
    
    text = text.strip()
    
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
    
    if not has_chinese:
        return text
    
    cache_key = text.lower()
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]
    
    glossary_text = apply_glossary(text)
    if glossary_text != text and not re.search(r'[\u4e00-\u9fff]', glossary_text):
        result = glossary_text
        _translation_cache[cache_key] = result
        return result
    
    translated = None
    
    async with httpx.AsyncClient() as client:
        google_task = asyncio.create_task(translate_with_google(text, client))
        mymemory_task = asyncio.create_task(translate_with_mymemory(text, client))
        
        done, pending = await asyncio.wait(
            [google_task, mymemory_task],
            timeout=2.0,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        for task in done:
            result = task.result()
            if result:
                translated = result
                break
        
        for task in pending:
            task.cancel()
    
    if translated:
        result = translated
    else:
        pinyin_parts = lazy_pinyin(text, style=Style.NORMAL)
        result = ' '.join(pinyin_parts)
    
    if glossary_text != text:
        for cn, en in TECH_GLOSSARY.items():
            if cn in text:
                result = result.replace(lazy_pinyin(cn, style=Style.NORMAL)[0] if not any(c.isascii() for c in cn) else cn, en)
    
    _translation_cache[cache_key] = result
    return result


def generate_slug_from_text(text: str, max_length: int = 100) -> str:
    if not text or not text.strip():
        return ''
    
    text = text.strip()
    
    slug = text.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit('-', 1)[0]
    
    return slug.lower()


def generate_slug(text: str, max_length: int = 100) -> str:
    if not text or not text.strip():
        return ''
    
    text = text.strip()
    
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
    
    if has_chinese:
        pinyin_parts = lazy_pinyin(text, style=Style.NORMAL)
        slug = '-'.join(pinyin_parts)
    else:
        slug = text.lower()
    
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit('-', 1)[0]
    
    return slug.lower()


def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def calculate_similarity_score(input_text: str, target_text: str) -> float:
    if not input_text or not target_text:
        return 0.0
    
    input_lower = input_text.lower().strip()
    target_lower = target_text.lower().strip()
    
    if input_lower == target_lower:
        return 1.0
    
    if input_lower in target_lower:
        return 0.8 + (len(input_lower) / len(target_lower)) * 0.2
    
    if target_lower in input_lower:
        return 0.7 + (len(target_lower) / len(input_lower)) * 0.2
    
    distance = levenshtein_distance(input_lower, target_lower)
    max_len = max(len(input_lower), len(target_lower))
    similarity = 1.0 - (distance / max_len)
    
    input_words = set(input_lower.split('-'))
    target_words = set(target_lower.split('-'))
    
    if input_words and target_words:
        common_words = input_words & target_words
        word_overlap = len(common_words) / max(len(input_words), len(target_words))
        similarity = similarity * 0.6 + word_overlap * 0.4
    
    return max(0.0, min(1.0, similarity))


def find_similar_slug(
    input_slug: str,
    existing_slugs: List[str],
    threshold: float = 0.6
) -> Optional[str]:
    if not input_slug or not existing_slugs:
        return None
    
    input_lower = input_slug.lower().strip()
    
    exact_prefix_matches = [
        slug for slug in existing_slugs
        if slug.lower().startswith(input_lower)
    ]
    if exact_prefix_matches:
        return sorted(exact_prefix_matches, key=len)[0]
    
    best_match = None
    best_score = 0.0
    
    for slug in existing_slugs:
        score = calculate_similarity_score(input_lower, slug.lower())
        if score > best_score:
            best_score = score
            best_match = slug
    
    if best_score >= threshold:
        return best_match
    
    return None


def generate_slug_with_fallback(
    text: str,
    existing_slugs: List[str],
    similarity_threshold: float = 0.6,
    max_length: int = 100
) -> dict:
    if not text or not text.strip():
        return {
            'slug': 'untitled',
            'source': 'default',
            'similarity_score': 0.0,
            'matched_slug': None
        }
    
    text = text.strip()
    generated_slug = generate_slug(text, max_length)
    
    if not generated_slug:
        generated_slug = 'untitled'
    
    if generated_slug in [s.lower() for s in existing_slugs]:
        return {
            'slug': generated_slug,
            'source': 'exact_match',
            'similarity_score': 1.0,
            'matched_slug': generated_slug
        }
    
    similar_slug = find_similar_slug(generated_slug, existing_slugs, similarity_threshold)
    
    if similar_slug:
        similarity = calculate_similarity_score(generated_slug, similar_slug)
        return {
            'slug': similar_slug,
            'source': 'similar_match',
            'similarity_score': similarity,
            'matched_slug': similar_slug
        }
    
    unique_slug = generate_unique_slug(generated_slug, existing_slugs)
    return {
        'slug': unique_slug,
        'source': 'generated',
        'similarity_score': 0.0,
        'matched_slug': None
    }


def generate_unique_slug(base_slug: str, existing_slugs: List[str], max_attempts: int = 100) -> str:
    if not base_slug:
        base_slug = 'untitled'
    
    if base_slug not in existing_slugs:
        return base_slug
    
    for i in range(1, max_attempts + 1):
        new_slug = f"{base_slug}-{i}"
        if new_slug not in existing_slugs:
            return new_slug
    
    hash_suffix = hashlib.md5(str(hash(base_slug)).encode()).hexdigest()[:6]
    return f"{base_slug}-{hash_suffix}"


def calculate_reading_time(content: str, words_per_minute: int = 200) -> int:
    words = len(content.split())
    minutes = math.ceil(words / words_per_minute)
    return max(1, minutes)


def truncate_text(text: str, max_length: int = 200) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + '...'
