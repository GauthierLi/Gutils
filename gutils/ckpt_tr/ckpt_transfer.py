try:
    import torch
    import paddle
except Exception as e:
    print(e)
    print('if you want to use WeightTrans, you have to install pytorch and paddle')
import warnings
from typing import List, Any
from functools import reduce
from collections import defaultdict, OrderedDict

class WeightTrans(object):
    """
    Usage
    --------
        1. 加载源权重文件和目标权重文件；
        2. 根据源权重文件和目标权重文件的关键字分析，找出模型权重转换的解决方案；
        3. 将关键子转换规则写入 `source2target_rule` 方法；
        4. 必要时通过重写 `transfer_weight` 方法， 对权重shape或者是type进行转换；
        5. 调用 `source2target` 方法，完成权重转换。

    Parameters
    ----------
        source_weight: str 需要转换的源权重文件

        targe_weight: str 一个用于对齐的权重文件，一般直接由目标模型生成，仅用于对齐key 和权重的shape
        
        source_keys_prefix: List[str] 列表，用于指定源权重文件中的key，如权重文件为字典，参数保存在key为 'state_dict' 的值中，则对应的 prefix为 ['state_dict']
        
        target_keys_prefix: List[str] 同上

    Examples
    --------
>>>        class WeightTrans(WeightTrans):
>>>            def source2target_rule(self, key):
>>>                if 'noise_estimator.outc' in key:
>>>                    key = key.replace('noise_estimator.outc.conv.conv', \
    'noise_estimator.outc')
>>>                return key
>>>            
>>>            def transfer_weight(self, key, source_weight):
>>>                if key == 'noise_estimator.cond_embedder.embedding.weight':
>>>                    return source_weight.astype('float32')
>>>                
>>>                shape_len = len(source_weight.shape)
>>>                trs_idx = [i for i in range(shape_len)]
>>>                if shape_len == 2:
>>>                    trs_idx = trs_idx[::-1]
>>>                if  shape_len > 2:
>>>                    trs_idx = trs_idx[:-2] + [trs_idx[-1], trs_idx[-2]]
>>>                if 'weight' in key:
>>>                    return source_weight.transpose(*trs_idx).astype('float32')
>>>                else:
>>>                    return source_weight.astype('float32')
>>>        
>>>        wt = WeightTrans(r"/path/to/source/weight.pdparams", 
>>>                     r"/path/to/source/target.pdparams")
>>>        wt.source2target(r"/path/to/save/", "paddle")

    """
    def __init__(self, 
                 source_weight: str, 
                 target_weight: str,
                 source_keys_prefix: List[str]=None,
                 target_keys_prefix: List[str]=None) -> None:
        self.source_weight, self.source_type = (paddle.load(source_weight), "paddle") if \
            source_weight.endswith('.pdparams') else (torch.load(source_weight), "torch")
            
        self.target_weight, self.target_type = (paddle.load(target_weight), "paddle") if \
            target_weight.endswith('.pdparams') else (torch.load(target_weight), "torch")
        self.source_keys, self.target_keys = self._get_params(source_keys_prefix, target_keys_prefix)  
        print(self)
        
    def _get_params(self, 
                    source_keys_prefix: List[str]=None,
                    target_keys_prefix: List[str]=None):
        source_weight = self.source_weight
        target_weight = self.target_weight
        if source_keys_prefix is not None:
            for key in source_keys_prefix:
                source_weight = source_weight[key]
                
        if target_keys_prefix is not None:
            for key in target_keys_prefix:
                target_weight = target_weight[key]
                
        source_keys = [key for key in source_weight.keys()]
        target_keys = [key for key in target_weight.keys()]
        return source_keys, target_keys

    def _prefix_analyse(self):
        """
        对源数据和目标数据的key进行前缀分析，并返回前三个最流行的prefix。
        
        Args:
            无
        
        Returns:
            Tuple[Dict[str, float], Dict[str, float]]: 返回一个元组，包含两个字典。
                第一个字典source_result包含前三个最流行的源数据prefix及其对应的频率；
                第二个字典target_result包含前三个最流行目标数据prefix及其对应的频率。
        """
        source_prefix_dict = defaultdict(lambda: 0)
        taget_prefix_dict = defaultdict(lambda: 0)
        for key in self.source_keys:
            source_prefix_dict[key.split('.')[0]] += 1. / len(self.source_keys)
        for key in self.target_keys:
            taget_prefix_dict[key.split('.')[0]] += 1. / len(self.target_keys)
        source_prefix_dict = dict(sorted(source_prefix_dict.items(), key=lambda x:x[1], reverse=True))
        taget_prefix_dict = dict(sorted(taget_prefix_dict.items(), key=lambda x:x[1], reverse=True))
        top3_source_key = [key for key in source_prefix_dict.keys()][:3]
        top3_target_key = [key for key in taget_prefix_dict.keys()][:3]
        source_result = dict([(key, source_prefix_dict[key]) for key in top3_source_key])
        target_result = dict([(key, taget_prefix_dict[key]) for key in top3_target_key])
        return source_result, target_result
    
    def _missing_analyse(self, 
                         source_top3_prefix: List[str], 
                         target_top3_prefix: List[str], 
                         show_number: int=10):
        """
        分析 source_top3_prefix 和 target_top3_prefix 中缺失的键，将缺失的键添加到对应的字典中。
        
        Args:
            source_top3_prefix (List[str]): 源语言前缀列表
            target_top3_prefix (List[str]): 目标语言前缀列表
            show_number (int, optional): 展示的缺失键的最大数量, 默认值为10.
        
        Returns:
            Tuple[Dict[str, List[str]], Dict[str, List[str]], source_missing_rate: float, target_missing_rate: float]: 两个字典分别表示源语言和目标语言中缺失的键及其对应的前缀, 
            字典的键为前缀，值为该前缀下缺失的键的列表。
        
        """
        source_missing = defaultdict(lambda: [])
        target_missing = defaultdict(lambda: [])
        for key in self.source_keys:
            if key not in self.target_keys:
                for prefix in source_top3_prefix:
                    if key.startswith(prefix) and len(source_missing[prefix]) < show_number:
                        source_missing[prefix].append(key)
            else:
                continue
        for key in self.target_keys:
            if key not in self.source_keys:
                for prefix in target_top3_prefix:
                    if key.startswith(prefix) and len(target_missing[prefix]) < show_number:
                        target_missing[prefix].append(key)
            else:
                continue
        source_missing_rate = len(source_missing) / len(self.source_keys)
        target_missing_rate = len(target_missing) / len(self.target_keys)
        return source_missing, target_missing, source_missing_rate, target_missing_rate
    
    def source2target(self, 
                      save_dir,
                      save_type: str=None, *args, **kwargs):
        """
        将source模型中的参数按照source2target_rule转换后，保存到target模型中。
        
        Args:
            save_dir (str): 保存转换后的参数路径，不包括后缀。
            save_type (str, optional): 保存参数的文件类型，支持'paddle'或'torch'，默认为None时，保持源checkout的backend。
            *args (tuple, optional): 未被使用的附加参数将被传递给函数self.source2target_rule。 
            **kwargs (dict, optional): 未被使用的附加参数将被传递给函数self.source2target_rule。
        
        Returns:
            Union[None, dict]: 若save_type不为空，并且不为“paddle", "torch"关键字，则返回转换后的参数字典，否则为None。
        
        """
        new_state_dict = {}
        if self.source_type != self.target_type:
            warnings.warn("Alert target type is not equal to source type, \
                if it is nesserary, please reimplement self.transfer_weight method!")
        for key in self.source_keys:
            if key in self.target_keys:
                new_state_dict[key] = self.transfer_weight(key, self.source_weight[key].numpy())
                if (source_shape := list(new_state_dict[key].shape)) != \
                        (target_shape := list(self.target_weight[key].shape)):
                    error = f"Source shape of {key} {source_shape} != target shape {target_shape} , \
if you want to repaire it ,please reimplement self.transfer_weight method!"
                    warnings.warn(error)
                continue
            try:
                new_key = self.source2target_rule(key)
                if new_key not in self.target_keys:
                    print("new key {} not in target".format(new_key))
                else:
                    transfer_weight = self.transfer_weight(new_key, self.source_weight[key].numpy())
                    if (source_shape := list(transfer_weight.shape)) != \
                            (target_shape := list(self.target_weight[new_key].shape)):
                            
                        error = f"Source shape of {new_key} {source_shape} != target shape {target_shape} , \
if you want to repaire it ,please reimplement self.transfer_weight method!"
                        warnings.warn(error)
                    new_state_dict[new_key] = transfer_weight
            except Exception as e:
                print(key, e)
        print("=> Transfer Done!")
        if save_type:
            if save_type == 'paddle':
                save_dir = save_dir+'.pdparams'
                paddle.save(new_state_dict, save_dir)
                print(f"=> saved at {save_dir} .")
                return
            if save_type == 'torch':
                save_dir = save_dir +'.pth'
                torch.save(new_state_dict, save_dir)
                print(f"=> saved at {save_dir} .")
                return 
            print(f"not support save type: {save_type}, please recieve state_dict and save later ...")
            return new_state_dict
        else:
            if self.source_type == 'paddle':
                save_dir = save_dir+'.pdparams'
                paddle.save(new_state_dict, save_dir)
                print(f"=> saved at {save_dir} .")
                return
            if self.source_type == 'torch':
                save_dir = save_dir +'.pth'
                torch.save(new_state_dict, save_dir)
                print(f"=> saved at {save_dir} .")
                return 
        
                    
    def source2target_rule(source_key: str, *args, **kwargs) -> str:
        raise NotImplementedError()
    
    def transfer_weight(self, key:str, source_weight: Any) -> Any:
        """ 输入是一个ndarray，输出也是一个ndarray。"""
        return source_weight.astype('float32')
    
    def beauty_str(self, str1='', str2='', tab=1):
        """
        将两个字符串进行美化组合，并返回结果字符串。
        
        Args:
            str1: 第一个要美化的字符串，默认为空字符串。
            str2: 第二个要美化的字符串，默认为空字符串。
            tab: 第二个字符串相对第一个字符串缩进的空格数，默认为1个空格。
        
        Returns:
            被美化后的字符串，第一个字符串加上一个换行符、一个制表符*tab空格和第二个字符串。
        
        """
        return str1 + '\n' + '\t' * tab + str2
    
    def __str__(self):
        """
        返回一个字符串，用于展示checkpoint 的关键字以供确定策略。
        
        Returns:
            str: 包含源语言和目标语言前缀分析结果以及关键词缺失分析结果的字符串。
        
        """
        source_top3, target_top3 = self._prefix_analyse()
        source2target, target2source, s2t_rate, t2s_rate = self._missing_analyse(source_top3, target_top3)
        if len(source2target.values()):
            s2t = reduce(self.beauty_str, [reduce(self.beauty_str, value) for value in source2target.values()])
        else:
            s2t = 'all in'
        
        if len(target2source.values()):
            t2s = reduce(self.beauty_str, [reduce(self.beauty_str, value) for value in target2source.values()])
        else:
            t2s = 'all in'
        
        strings = f"""{'-' * 100}
PREFIX ANALYSE:
    source_most_like_prefix: {source_top3}
    target_most_like_prefix: {target_top3}
Key word \'{list(source_top3.keys())[0]}\' most like to be a prefix of the source. 
Key word \'{list(target_top3.keys())[0]}\' most like to be a prefix of the target.
{'-' * 100}
KEY_WORD MISSING ANALYSE:
    Source targe in {(1 - s2t_rate) * 100 :.2f} %, Target target in {(1 - t2s_rate) * 100:.2f} %:
    IN SOURCE NOT IN TARGET: 
        {s2t}
    IN TARGET NOT IN SOURCE: 
        {t2s}
"""
        return strings
