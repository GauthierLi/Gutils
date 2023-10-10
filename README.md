Gutils
===
各种工具库，如权重转换等

安装
---
```bash
pip install -v -e .
```


快速开始
---
 
#### 1. 权重转化使用例子
1. 观察源权重关键字以及目标权重关键字的区别
```python
from gutils.ckpt_tr import WeightTrans

wt = WeightTrans(r"/path/to/source/weight.pdparams",r"/path/to/source/target.pdparams")
```
初始化后会自动打印关于权重文件的信息，如前缀出现的top3概率分析、source权重的key在target中出现的比例、source权重的key在target中出现的比例、未出现在target中和未出现在source中不同前缀的关键字分别列出10个例子。以下是一个例子：
```bash
-----------------------------------------------------
PREFIX ANALYSE:
    source_most_like_prefix: {'noise_estimator': 0.6201780415430254, 'latent_embedder': 0.3442136498516315, 'noise_scheduler': 0.03560830860534124}
    target_most_like_prefix: {'noise_estimator': 0.6763754045307432, 'latent_embedder': 0.2847896440129448, 'noise_scheduler': 0.03883495145631069}
Key word 'noise_estimator' most like to be a prefix of the source. 
Key word 'noise_estimator' most like to be a prefix of the target.
-----------------------------------------------------
KEY_WORD MISSING ANALYSE:
    Source targe in 0.9940652818991098 %, Target target in 0.9967637540453075 %:
    IN SOURCE NOT IN TARGET: 
        noise_estimator.outc.conv.conv.weight
        noise_estimator.outc.conv.conv.bias
        latent_embedder.perceiver.loss_fn.scaling_layer.shift
        latent_embedder.perceiver.loss_fn.scaling_layer.scale
        latent_embedder.perceiver.loss_fn.net.slice1.0.weight
        latent_embedder.perceiver.loss_fn.net.slice1.0.bias
        latent_embedder.perceiver.loss_fn.net.slice1.2.weight
        latent_embedder.perceiver.loss_fn.net.slice1.2.bias
        latent_embedder.perceiver.loss_fn.net.slice2.5.weight
        latent_embedder.perceiver.loss_fn.net.slice2.5.bias
        latent_embedder.perceiver.loss_fn.net.slice2.7.weight
        latent_embedder.perceiver.loss_fn.net.slice2.7.bias
    IN TARGET NOT IN SOURCE: 
        noise_estimator.outc.weight
        noise_estimator.outc.bias
```
2. 根据关键字做出源关键字对目标关键字的映射方法，并重写 `self.source2target_rule` 方法 （该方法接收源key，返回一个新的key，用户在该方法中实现转换逻辑。），并执行 self.source2target 方法，第一次尝试进行权重转换。
```python
from gutils.ckpt_tr import WeightTrans

class WeightTrans(WeightTrans):
    def source2target_rule(self, key):
        if 'noise_estimator.outc' in key:
            key = key.replace('noise_estimator.outc.conv.conv', 'noise_estimator.outc')
        return key
wt = WeightTrans(r"/path/to/source/weight.pdparams",r"/path/to/source/target.pdparams")
wt.source2target(r"/path/to/save/, "paddle")
```

3. 若执行过程中出现权重的shape对应不正确，会产生一个警告，指出shape不同的权重对应的 新key以及源权重shape和目标权重shape，然后根据警告提示进行修改 `self.transfer_weight` 方法（该方法接收新key 以及写入该key 的权重，用户在该方法中实现权重转换的逻辑，注意一般权重的type是 flaot32），并执行 `self.source2target` 方法，再次尝试进行权重转换。
```python
class WeightTrans(WeightTrans):
    def source2target_rule(self, key):
        if 'noise_estimator.outc' in key:
            key = key.replace('noise_estimator.outc.conv.conv', 'noise_estimator.outc')
        return key

    def transfer_weight(self, key, source_weight):
        if key == 'noise_estimator.cond_embedder.embedding.weight':
            return source_weight.astype('float32')
        shape_len = len(source_weight.shape)
        trs_idx = [i for i in range(shape_len)]
        if shape_len == 2:
            trs_idx = trs_idx[::-1]
        if  shape_len > 2:
            trs_idx = trs_idx[:-2] + [trs_idx[-1], trs_idx[-2]]
        if 'weight' in key:
            return source_weight.transpose(*trs_idx).astype('float32')
        else:
            return source_weight.astype('float32')

wt = WeightTrans(r"/path/to/source/weight.pdparams",r"/path/to/source/target.pdparams")
wt.source2target(r"/path/to/save/", "paddle")
```
注意： `/path/to/save/` 不用写后缀 如 ` /root/dest`，程序会自动根据第二个位置参数进行判断，并补全为 `/root/dest.pdparams` 或者 `/root/dest.pth` 。

版本信息
---
本项目的各版本信息和变更历史可以在[这里][changelog]查看。

维护者
---
### owners
* GauthierLi(lwklxh@163.com)

### committers
* GauthierLi(lwklxh@163.com)
