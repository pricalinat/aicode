# 淘宝商品库算法团队研究成果汇总

> 研究方向：商品搜索、推荐系统、多目标优化、向量检索
> 更新时间：2026-02-28

---

## 📄 学术论文

### 1. Multi-Objective Personalized Product Retrieval in Taobao Search (KDD 2022)
- **作者**: Yukun Zheng, Zhixuan Zhang 等
- **arXiv**: https://arxiv.org/abs/2210.04170
- **摘要**: 提出MOPPR模型，在淘宝搜索中实现多目标个性化商品检索，离线实验和在线A/B测试显示GMV提升1.29%

### 2. Embedding-based Product Retrieval in Taobao Search (KDD 2021)
- **作者**: Sen Li, Fuyu Lv 等
- **arXiv**: https://arxiv.org/abs/2106.09297
- **ACM**: https://dl.acm.org/doi/10.1145/3447548.3467101
- **摘要**: 提出MGDSPR (Multi-Grained Deep Semantic Product Retrieval)模型，解决训练与推理阶段的不一致性问题

### 3. MAKE: Vision-Language Pre-training based Product Retrieval in Taobao Search (WWW 2023)
- **作者**: Alibaba团队
- **ACM**: https://dl.acm.org/doi/10.1145/3543873.3584627
- **摘要**: 基于视觉-语言预训练的淘宝搜索商品检索，已在线上部署并带来显著提升

### 4. Simple but Efficient: A Multi-Scenario Nearline Retrieval Framework for Recommendation on Taobao
- **arXiv**: https://arxiv.org/html/2408.00247v3
- **摘要**: 提出多场景近线检索框架，利用Flink从各场景 Ranking 日志获取精细排序结果

### 5. Virtual-Taobao: Virtualizing Real-world Online Retail Environment for Reinforcement Learning
- **来源**: 南京大学 + 淘宝
- **摘要**: 用强化学习优化淘宝商品搜索，总收入提升2%

---

## 🔧 技术博客

### 1. 淘系技术团队官方博客
- **CSDN**: https://blog.csdn.net/Taobaojishu
- **阿里102实验室**: https://102.alibaba.com/detail?id=189

### 2. 淘宝搜索算法技术演进
- **主题**: 电商搜索算法技术的演进
- **作者**: 青峰（搜索推荐算法技术负责人，阿里巴巴研究员）
- **链接**: https://102.alibaba.com/detail?id=189
- **核心内容**:
  - 几十亿商品，千千万级叶子类目
  - 个性化搜索、Query改写、检索粒度控制、用户引导

### 3. 淘宝推荐场景重排模型 (KDD 2023)
- **论文**: 《Controllable Multi-Objective Re-ranking with Policy Hypernetworks》
- **核心**: Hypernet + conditional training
- **链接**: https://hub.baai.ac.cn/view/32600

### 4. 淘宝详情页分发推荐算法
- **主题**: 用户即时兴趣强化
- **链接**: https://blog.csdn.net/Taobaojishu/article/details/118980712

### 5. CIKM论文解读 | 淘宝内容化推荐场景下多场景全域表征
- **链接**: https://blog.csdn.net/Taobaojishu/article/details/130437142

---

## 🏆 团队研究方向总结

| 方向 | 典型工作 | 会议 |
|------|----------|------|
| 商品检索 | MGDSPR, MOPPR | KDD |
| 多目标优化 | Policy Hypernetworks | KDD |
| 视觉-语言预训练 | MAKE | WWW |
| 强化学习 | Virtual-Taobao | - |
| 多场景检索 | Nearline Retrieval | - |

---

## 🔬 核心算法系列：DIN/DIEN/DSIN

阿里妈妈精准定向检索及基础算法团队的经典工作，主要用于淘宝CTR预估：

### 1. DIN (Deep Interest Network) - KDD 2017
- **论文**: Deep Interest Network for Click-Through Rate Prediction
- **核心**: 引入Attention机制，对用户历史行为加权pooling，捕获用户对候选商品的不同兴趣程度

### 2. DIEN (Deep Interest Evolution Network) - KDD 2018
- **论文**: Deep Interest Evolution Network for Click-Through Rate Prediction
- **核心**: 在DIN基础上引入GRU序列建模，捕捉用户兴趣的演化过程
- **AUGRU**: Attention门控循环单元

### 3. DSIN (Deep Session Interest Network) - KDD 2019
- **论文**: Deep Session Interest Network for Click-Through Rate Prediction
- **核心**: 将用户行为按Session划分，提取多兴趣表征

### 技术博客
- DIN/DIEN/DSIN 区别: https://zhuanlan.zhihu.com/p/365999532
- 序列建模总结: https://blog.csdn.net/whgyxy/article/details/131877120
- 源码解读: https://www.cnblogs.com/rossiXYZ/p/13796470.html

---

## 📚 相关资源

### 工业界推荐系统论文集
- https://github.com/Doragd/Algorithm-Practice-in-Industry
- https://github.com/guyulongcs/Awesome-Deep-Learning-Papers-for-Search-Recommendation-Advertising

### 阿里系论文导航
- https://daiwk.github.io/posts/links-navigation-recommender-system.html

---

*注：部分论文需要通过内网或学术机构访问*
