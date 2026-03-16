import argparse
import yaml
import os
from datetime import datetime
import time

def arg2str(args):
    # args.run_time = datetime.now().strftime('%b%d_%H-%M-%S')
    args_dict = vars(args)
    option_str = 'run_time: ' + datetime.now().strftime('%b%d_%H-%M-%S') + '\n'

    for k, v in sorted(args_dict.items()):
        option_str += ('{}: {}\n'.format(str(k), str(v)))

    return option_str


class BaseConfig(object):

    def __init__(self, config = None):
        self.config = config

        self.parser = argparse.ArgumentParser()
        # self.parser.add_argument('--confag', type=str, default='a')
        # self.parser.add_argument('--config', type=str, default='/home/zhangzhe/Workshop/AIgent/Gene/backend/CBAFI/cfg/configs/base.yaml')
        self.parser.add_argument('--config',type=str, default="./FrailtyIndex/cfgs/run/ours_fttrans-hcdr.yaml")
        self.parser.add_argument('--model_path', type=str, default="",help="模型加载路径")
        self.parser.add_argument('--result_path', type=str, default="./output",help="结果保存路径")
        self.parser.add_argument('--seed', type=int, default=2)
        self.parser.add_argument('--gpu_id', type=int, default=0)
        self.parser.add_argument('--ratio', type=float, default=0.15,help="测试集和训练验证集的比例")
        self.parser.add_argument('--depth', type=int, default=3,help="模型深度")
        self.parser.add_argument('--dim', type=int, default=512,help="模型深度")
        self.parser.add_argument('--att_dropout_my', type=float, default=0.3,help="att_dropout")
        self.parser.add_argument('--ff_dropout_my', type=float, default=0.25,help="ff_dropout")
        self.parser.add_argument('--lr_my', type=float, default=0.001,help="lrs")
        self.parser.add_argument('--lr_adjust_my', type=int, default=0,help="lrs_adjust")
        self.parser.add_argument('--Kfold', type=int, default=5,help="kfolds")
        self.parser.add_argument('--cont', type=int, default=9,help="连续变量的个数") # 9
        self.parser.add_argument('--cate', type=int, default=8,help="分类变量的个数") # 8
        self.parser.add_argument('--mode', type=int, default=43,help="调用的模型 43-43个特征 20-20个特征")
        
        # self.parser.add_argument('--pheno_path', type=str, default="./data/pheno_sampled.csv")
        # self.parser.add_argument('--base_path', type=str, default="./data/base_sampled.csv")
        # self.parser.add_argument('--ecg_dir', type=str, default="./data/ecg_sampled.csv")
        # self.parser.add_argument('--air_path', type=str, default="./data/air_sampled.csv")
        # self.parser.add_argument('--lipid_path', type=str, default="./data/lipid_sampled.csv")
        # self.parser.add_argument('--cmr_path', type=str, default="./data/cmr_sampled.csv")
    
    def load_base(self, derived_config, config):
        if '__base__' in derived_config:
            for each in derived_config['__base__']:
                with open(each) as f:
                    derived_config_ = yaml.safe_load(f)
                    config = self.load_base(derived_config_, config)
            # config = {**config, **derived_config}
        # else:
        config = {**config, **derived_config}
        return config

    # def load_base(self, derived_config, config):
    #     config = self._load_base(derived_config, config)
    #     if config['exp_param'] not in [None, 'None']:
    #         for each in config['exp_param']:
    #             config['exp_name'] = config['exp_name'] + '-' + each + '=' + config[each]

    #     return config

    def initialize(self, config = None):
        args = self.parser.parse_args()

        # print(self.parser.config)
        # print(self.parser.confag)
        # raise ValueError

        if self.config:
            args.config = self.config

        config = {}
        with open(args.config) as f:
            derived_config = yaml.safe_load(f)
            config = self.load_base(derived_config, config)



        if 'exp_param' in config and config['exp_param'] not in [None, 'None']:
            if isinstance(config['exp_param'], str):
                config['exp_name'] = str(config['exp_name']) + '-' + str(config['exp_param']) + '=' + str(config[config['exp_param']])
            else:
                for each in config['exp_param']:
                    config['exp_name'] = str(config['exp_name']) + '-' + str(each) + '=' + str(config[each])


                
        for key, value in config.items():
            setattr(args, key, value)


        if args.time_delay != 0:
            print('================ {:^30s} ================'.format('Delay for {} seconds'.format(args.time_delay)))
            time.sleep(args.time_delay)

        return args


    def save_result(self, acc_list, loss_list, loss_refine_list):

        acc_save_path = os.path.join(self.args.save_folder, self.args.exp_name) + '/acc_{}_std_{}.txt'.format(acc_mean, acc_std)
        loss_save_path = os.path.join(self.args.save_folder, self.args.exp_name) + '/loss_{}_std_{}.txt'.format(loss_mean, loss_std)
        loss_refine_save_path = os.path.join(self.args.save_folder, self.args.exp_name) + '/loss2_{}_std_{}.txt'.format(loss_refine_mean, loss_refine_std)

        with open(acc_save_path, "w") as f:
            for c, ac in enumerate(acc_list):
                f.write('train_{}_acc is {}\n'.format(c, ac))
        f.close()

        with open(loss_save_path, "w") as f:
            for c, ac in enumerate(loss_list):
                f.write('train_{}_loss is {}\n'.format(c, ac))
        f.close()

        with open(loss_refine_save_path, "w") as f:
            for c, ac in enumerate(loss_refine_list):
                f.write('train_{}_loss is {}\n'.format(c, ac))
        f.close()


