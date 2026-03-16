
import torch
from cfgs.cfg import BaseConfig
import os
from utils import data_load
import numpy as np
import training
from time import time
import random
import pandas as pd
from typing import Dict, List
os.environ["mapreduce_input_fileinputformat_split_maxsize"] = "64" 
import sys
sys.path.insert(0, os.path.dirname(__file__))


def custom_repr(self):
    return f'{{Tensor:{tuple(self.shape)}}} {original_repr(self)}'

original_repr = torch.Tensor.__repr__
torch.Tensor.__repr__ = custom_repr

fid2name={'f.1210.0.0': 'Snoring', 'f.2110.0.0': 'Able to confide', 'f.1200.0.0': 'Sleeplessness', 
          'f.1070.0.0': 'Time spent watching TV', 'f.924.0.0': 'Usual walking pace', 'f.1239.0.0': 'Current tobacco smoking', 
          'f.1249.0.0': 'Past tobacco smoking', 'f.1050.0.0': 'Time spend outdoors in summer', 'f.1558.0.0': 'Alcohol intake frequency', 
          'f.2139.0.0': 'Age first had sexual intercourse', 'f.2335.0.0': 'Chest pain or discomfort', 
          'f.2247.0.0': 'Hearing difficulty/problems', 'f.2257.0.0': 'Hearing difficulty/problems with background noise',
        'f.46.0.0': 'Hand grip strength (left)', 'f.48.0.0': 'Waist circumference', 
        'f.3606.0.0': 'Chest pain or discomfort walking normally', 'f.3063.0.0': 'Forced expiratory volume in 1-second (FEV1)', 
        'f.21001.0.0': 'Body mass index (BMI)', 'f.23100.0.0': 'Whole body fat mass', 'f.49.0.0': 'Hip circumference', 
        '23456': 'linoleic acid to total fatty acids', '23457': 'docosahexaenoic acid to total fatty acids','23528': 'free cholesterol in idl', '23643': 'triglycerides to total lipids in medium hdl', '23562': 'cholesteryl esters in large hdl', 
        '23636': 'cholesteryl esters to total lipids in large hdl', '23561': 'cholesterol in large hdl', 
        '23536': 'triglycerides in large ldl', '23403': 'vldl cholesterol', '23592': 'free cholesterol to total lipids in large vldl', 
        'V8': 'I_inteR', 'V40': 'III_S', 'V60': 'aVR_T', 'V67': 'aVR_inteT', 'V77': 'aVL_R', 'V217': 'V6_inteR', 
        '24142-2.0': 'LV circumferential strain AHA 2', '24114-2.0': 'RA maximum volume', '24133-2.0': 'LV mean myocardial wall thickness AHA 10', 
        'f.24003.0.0': 'Nitrogen dioxide air pollution; 2010', 'f.24004.0.0': 'Nitrogen oxides air pollution; 2010', 'f.24005.0.0': 'Particulate matter air pollution (pm10); 2010', 'f.24006.0.0': 'Particulate matter air pollution (pm2.5); 2010'}
# name2fid={'Snoring': 'f.1210.0.0', 'Able to confide': 'f.2110.0.0', 'Sleeplessness': 'f.1200.0.0', 'Time spent watching TV': 'f.1070.0.0', 'Usual walking pace': 'f.924.0.0', 'Current tobacco smoking': 'f.1239.0.0', 'Past tobacco smoking': 'f.1249.0.0', 'Time spend outdoors in summer': 'f.1050.0.0', 'Alcohol intake frequency': 'f.1558.0.0', 'Age first had sexual intercourse': 'f.2139.0.0', 'Chest pain or discomfort': 'f.2335.0.0', 'Hearing difficulty/problems': 'f.2247.0.0', 'Hearing difficulty/problems with background noise': 'f.2257.0.0', 'Hand grip strength (left)': 'f.46.0.0', 'Waist circumference': 'f.48.0.0', 'Chest pain or discomfort walking normally': 'f.3606.0.0', 'Forced expiratory volume in 1-second (FEV1)': 'f.3063.0.0', 'Body mass index (BMI)': 'f.21001.0.0', 'Whole body fat mass': 'f.23100.0.0', 'Hip circumference': 'f.49.0.0', 'LA_pct': '23456', 'DHA_pct': '23457', 'IDL_FC': '23528', 'M_HDL_TG_pct': '23643', 'L_HDL_CE': '23562', 'L_HDL_CE_pct': '23636', 'L_HDL_C': '23561', 'L_LDL_TG': '23536', 'VLDL_C': '23403', 'L_VLDL_FC_pct': '23592', 'I_inteR': 'V8', 'III_S': 'V40', 'aVR_T': 'V60', 'aVR_inteT': 'V67', 'aVL_R': 'V77', 'V6_inteR': 'V217', 'LVCC_AHA_2': '24142-2.0', 'RAV_max': '24114-2.0', 'LVWT_AHA_10': '24133-2.0', 'Nitrogen dioxide air pollution; 2010': 'f.24003.0.0', 'Nitrogen oxides air pollution; 2010': 'f.24004.0.0', 'Particulate matter air pollution (pm10); 2010': 'f.24005.0.0', 'Particulate matter air pollution (pm2.5); 2010': 'f.24006.0.0'}

name2fid={}
for key,value in fid2name.items():
    name2fid[value]=key
def seed_everything(seed=0):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    # backends
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def initialize(args,mode,gpu_id):
    args.gpu_id = gpu_id
    args.mode = mode
    runseed = args.seed
    os.environ['CUDA_VISIBLE_DEVICES'] = str(args.gpu_id)
    seed_everything(runseed)
    args.cont=33
    args.cate=12
    args.batch_size=1
    args.model_path="./FrailtyIndex/path/0.path"

    return args


def validate_input_data(data_df, expected_cont: int, expected_cate: int):
    if not isinstance(data_df, pd.DataFrame):
        raise TypeError("输入数据必须是pandas DataFrame")
    if  data_df.empty or len(data_df) == 0:
        raise ValueError("数据框为空，无法进行预处理")
    total_expected = expected_cont + expected_cate
    if len(data_df.columns) < total_expected:
        raise ValueError(f"期望至少 {total_expected} 个特征，但只得到 {len(data_df.columns)} 个")
    if data_df.isnull().any().any():
        # print("警告: 数据中存在缺失值，可能会影响预测结果")
        raise ValueError("警告: 数据中存在缺失值，可能会影响预测结果")
    # 是否有缺失的列
        



def ForBackend(df,args):# 这个地方需要控制gpu_id
    dataset = getattr(data_load, 'hcdr')
    trainer = getattr(training,'delta')(args,args.cont,args.cate)

    test_data = dataset(
            df=df,
            dataset_mode='test',
            args=args,
            fid2name=fid2name,
            name2fid=name2fid
            
    )

    test_load = torch.utils.data.DataLoader(test_data, batch_size=max(args.batch_size, 2048), shuffle=False, num_workers=args.num_workers)
    res_df=trainer.test(test_load,
                        output=test_data.outdf,
                        model_path=args.model_path,
                        args=args)
    res_df.rename(columns=fid2name, inplace=True)
    return res_df



    

