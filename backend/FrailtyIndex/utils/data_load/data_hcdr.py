import random
from torchvision import transforms
import torch
import torch.utils.data as data_utils
import numpy as np
import os
import copy
import csv
import torch
import pickle
import pandas as pd
import random
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import roc_auc_score
import h5py
from ..utils import timer
from sklearn.model_selection import KFold,StratifiedKFold
from sklearn.preprocessing import MinMaxScaler,StandardScaler


mean=np.array([ 9.23547630e+01,  2.78807853e+00,  2.82784657e+01,  2.64828099e+01,
  1.04738981e+02,  2.84897336e+01,  1.94902083e+00,  2.17113295e-01,
  5.56054234e+00,  2.12432943e-01,  3.32573727e+01,  2.75217858e-01,
  1.00710917e-01,  7.40018156e-01,  1.39625799e+01,  1.21286068e+00,
  9.37828375e+01,  1.15628492e+01,  1.48951482e+00,  3.43454581e+01,
  2.07975887e+00, -1.99450272e+01, 7.82053837e+01,  6.26737816e+00,
  2.61239147e+01,  4.32363998e+01,  1.61386995e+01,  9.95193823e+00,
  5.73549970e+01,  2.50024734e+00,  3.18283308e+00,  1.80521425e+01,
  2.94621075e+01])
std=np.array([1.36520419e+01, 7.69033991e-01, 4.97211006e+00, 1.00006431e+01,
        9.58733472e+00, 3.45656432e+00, 6.46241809e-01, 5.74661166e-02,
        1.80023016e+00, 1.21860507e-01, 4.98687708e+00, 1.56558327e-01,
        2.67749887e-02, 2.45160288e-01, 1.23153783e+00, 8.99535951e-01,
        4.31173171e+01, 7.88855505e+00, 1.00747882e+00, 2.89879673e+01,
        1.13898195e+00, 6.25230761e+00, 1.96321261e+01, 8.18046368e-01,
        7.25304079e+00, 1.50045010e+01, 1.87740753e+00, 1.03353620e+00,
        7.88629869e+00, 2.99704988e+00, 3.62921852e+00, 5.32756742e+00,
        1.15532677e+01])


    
def find_indices(query_list):
    multiplecat=[]
    singlecat=[]
    Continuous=[]
    Integer=[]

    Integer_df=pd.read_csv("./FrailtyIndex/data/Type/Integer.csv",sep=",")
    Continuous_df=pd.read_csv("./FrailtyIndex/data/Type/Continuous.csv",sep=",")
    Categoricalsingle_df=pd.read_csv("./FrailtyIndex/data/Type/Categorical(single).csv",sep=",")
    Categoricalmultiple_df=pd.read_csv("./FrailtyIndex/data/Type/Categorical(multiple).csv",sep=",")
    
    Integer_list=list(Integer_df["Field ID"])
    Continuous_list=list(Continuous_df["Field ID"])
    Categoricalsingle_list=list(Categoricalsingle_df["Field ID"])
    Categoricalmultiple_list=list(Categoricalmultiple_df["Field ID"])

    Integer_list =list(map(str,Integer_list))
    Continuous_list =list(map(str,Continuous_list))
    Categoricalsingle_list =list(map(str,Categoricalsingle_list))
    Categoricalmultiple_list=list(map(str,Categoricalmultiple_list))

    for index, element in enumerate(query_list):
        if element in ["24114-2.0","24142-2.0","24133-2.0"]:
            element1=element.split("-")[0]
        element1=element.split(".")
        if len(element1)>1:element1=element1[1]
        else:element1=element1[0]  
        if element1 in Integer_list:Integer.append(element)
        elif element1 in Continuous_list: Continuous.append(element)
        elif element1 in Categoricalsingle_list:singlecat.append(element)
        elif element1 in Categoricalmultiple_list:multiplecat.append(element)
        else:
            Continuous.append(element)
    return Integer,Continuous,singlecat,multiplecat

def mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)


class MyDataset(data_utils.Dataset):
    @timer
    def __init__(self, df,dataset_mode, args,fid2name,name2fid):
        self.df=df
        self.data_list = []

        col_base=["sex","age"]
        col_all=['f.1210.0.0', 'f.2110.0.0', 'f.1200.0.0', 'f.1070.0.0', 'f.924.0.0', 'f.1239.0.0', 'f.1249.0.0', 'f.1050.0.0', 'f.1558.0.0', 'f.2139.0.0', 'f.2335.0.0', 'f.2247.0.0', 'f.2257.0.0', 'f.46.0.0', 'f.48.0.0', 'f.3606.0.0', 'f.3063.0.0', 'f.21001.0.0', 'f.23100.0.0', 'f.49.0.0', '23456', '23457', '23528', '23643', '23562', '23636', '23561', '23536', '23403', '23592', 'V8', 'V40', 'V60', 'V67', 'V77', 'V217', '24142-2.0', '24114-2.0', '24133-2.0', 'f.24003.0.0', 'f.24004.0.0', 'f.24005.0.0', 'f.24006.0.0']
        self.df=self.df.rename(columns=name2fid)
        test_X=self.df[col_all+col_base]
        Integer,Continuous,singlecat,multiplecat=find_indices(col_all)
        Continuous+=["age"]
        singlecat+=["sex"]
        self.len_cate=len(singlecat+multiplecat)
        self.len_cont=len(Integer+Continuous)


        epsilon = 1e-9
        test_X=test_X.reset_index(drop=True)
        self.cate = test_X[singlecat+multiplecat].values
        self.cont = (test_X[Continuous+Integer] - mean)/(std + epsilon)
        self.cont=self.cont.values


        self.dataset_mode=dataset_mode
        mkdir(args.result_path)

        all_columns = set(Integer + Continuous + singlecat + multiplecat)
        missing_columns = all_columns - set(self.df.columns)
        if missing_columns:

            missing_columns_name = [fid2name.get(col, col) for col in missing_columns]
            raise ValueError(f"以下列在数据框中不存在: {missing_columns_name}")
        
        # 1. 检查缺失值
        self._check_missing_values(Integer, Continuous, singlecat, multiplecat)
        # 2. 检查数值列的合法性
        self._check_numeric_columns(Integer + Continuous)
        # 4. 执行数据类型转换
        self._convert_data_types(Integer, Continuous, singlecat, multiplecat)


        # test_X=self.df[col_all+col_base]
        self.outdf=test_X[col_all+col_base]

    def _check_missing_values(self, Integer, Continuous, singlecat, multiplecat):
        """检查关键列的缺失值"""
        all_columns_to_check = Integer + Continuous + singlecat + multiplecat
        
        # 检查是否有完全为空的列
        empty_columns = []
        for col in all_columns_to_check:
            if self.df[col].isnull().all():
                empty_columns.append(col)
        
        if empty_columns:
            raise ValueError(f"以下列完全为空: {empty_columns}")
        
        # 检查缺失值比例
        high_missing_columns = []
        for col in all_columns_to_check:
            missing_ratio = self.df[col].isnull().mean()
            if missing_ratio > 0.3:  # 超过30%的缺失值
                high_missing_columns.append((col, f"{missing_ratio:.1%}"))
        
        if high_missing_columns:
            raise ValueError(f"以下列缺失值比例过高: {high_missing_columns}")

    def _check_numeric_columns(self, numeric_columns):
        """检查数值列的合法性"""
        for col in numeric_columns:
            # 检查是否为数值类型或可转换为数值类型
            if not pd.api.types.is_numeric_dtype(self.df[col]):
                # 尝试转换为数值类型，检查是否成功
                try:
                    pd.to_numeric(self.df[col], errors='raise')
                except ValueError:
                    raise ValueError(f"列 '{col}' 包含无法转换为数值的数据")
            
            # 检查无穷大值
            if np.any(np.isinf(self.df[col])):
                raise ValueError(f"列 '{col}' 包含无穷大值")
            


    def _convert_data_types(self, Integer, Continuous, singlecat, multiplecat):
        try:
            self.df[Integer] = self.df[Integer].astype(float)
            self.df[Continuous] = self.df[Continuous].astype(float)
            self.df[singlecat] = self.df[singlecat].astype(int)
            self.df[multiplecat] = self.df[multiplecat].astype(int)
            
        except ValueError as e:
            raise ValueError(f"数据类型转换失败: {str(e)}")
        except TypeError as e:
            raise TypeError(f"数据类型不匹配: {str(e)}")
        
        # 验证转换结果
        self._validate_conversion(Integer, Continuous, singlecat, multiplecat)

    def _validate_conversion(self, Integer, Continuous, singlecat, multiplecat):
        """验证数据类型转换结果"""
        # 检查数值列转换
        for col in Integer + Continuous:
            if not pd.api.types.is_float_dtype(self.df[col]):
                raise ValueError(f"列 '{col}' 未能成功转换为float类型")
        
        # 检查分类列转换
        for col in singlecat + multiplecat:
            if not pd.api.types.is_integer_dtype(self.df[col]):
                raise ValueError(f"列 '{col}' 未能成功转换为int类型")
        
    def __getitem__(self, idx):
        cont = copy.deepcopy(self.cont[idx])
        cate = copy.deepcopy(self.cate[idx])
        return torch.LongTensor(cate), torch.FloatTensor(cont)
    
    def evaluate(self, label, pred):
        return roc_auc_score(label.item(), pred[:,1].item())

    def __len__(self):
        return len(self.cate)
    
