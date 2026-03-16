import os
import torch
import models
from tensorboardX import SummaryWriter
from cfgs.cfg import arg2str
# from torchmetrics import Accuracy, AUROC, MeanSquaredError
from torch.cuda.amp import autocast, GradScaler
import shutil
from scipy.stats import pearsonr
from sklearn.metrics import r2_score, mean_squared_error
import pandas as pd
# import shap
import matplotlib.pyplot as plt


class DefaultTrainer(object):
    def __init__(self, args,len_cont,len_cate):
        self.args = args
        self.batch_size = args.batch_size
        self.lr = self.lr_current = args.lr_my
        self.start_iter = args.start_iter
        self.max_iter = args.max_iter
        # self.sub_iter = args.max_iter//2 if args.sub_iter == -1 else args.sub_iter
        self.warmup_steps = args.warmup_steps
        self.cluster=args.cluster
        self.dim=args.dim
        self.depth=args.depth
        self.groups = args.groups
        self.att_dropout=args.att_dropout_my
        self.ff_dropout=args.ff_dropout_my
        self.sum_num_per_group = args.sum_num_per_group
        self.prod_num_per_group = args.prod_num_per_group
        if self.args.lr_adjust_my==0:
            self.args.lr_adjust="fix"

        # self.model = getattr(models, args.model_name.lower())(args)
        # self.model = models.amformer(dim = self.dim,
        #                         depth = self.depth,
        #                         heads = 8,
        #                         attn_dropout = self.att_dropout,
        #                         ff_dropout = self.ff_dropout,
        #                         use_cls_token = False,# TRue
                                
        #                         # groups = [120, 120, 120],
        #                         # sum_num_per_group = [32, 32, 32],
        #                         # prod_num_per_group = [6, 6, 6],
                                
        #                         groups = [136,136,136,136],
        #                         sum_num_per_group = [32, 32, 32,32],
        #                         prod_num_per_group = [8,8,8,8],
                                
                                
        #                         cluster = self.cluster,
        #                         target_mode = 'mix',
        #                         token_descent = False, #True,
        #                         use_prod = True,
        #                         num_special_tokens = 2,
        #                         num_unique_categories = 10000,
        #                         out = 1,
        #                         num_cont = len_cont,
        #                         num_cate = len_cate,
        #                         use_sigmoid = True,)
        self.model = models.amformer(
            dim=self.dim,
            depth=self.depth,
            heads=8,  # 可考虑从 args 中读取
            attn_dropout=0.3,
            ff_dropout=0.25,
            use_cls_token=False,
            groups=[self.groups] * self.depth,
            sum_num_per_group=[self.sum_num_per_group] * self.depth,
            prod_num_per_group=[self.prod_num_per_group] * self.depth,
            cluster=False,
            target_mode='mix',
            token_descent=False,
            use_prod=True,
            num_special_tokens=2,
            num_unique_categories=10000,  # 可根据数据实际大小调整
            out=1,
            num_cont=len_cont,
            num_cate=len_cate,
            use_sigmoid=True,
        )


        self.flag = 0
        # self.scaler = GradScaler()

        self.metrics = {
            'pcc':['high', 0],
            'r2':['high', 0],
            'loss':['low', 1000],
            'mse':['low', 1000],}
        
        self.start = 0
        self.wrong = None
        self.log_path = os.path.join(self.args.save_folder, self.args.exp_name, 'result.txt')

        params = []
        params_for_pretrain = []
        for keys, param_value in self.model.named_parameters():
            params += [{'params': [param_value], 'lr': self.lr}]
            
        self.optim = torch.optim.Adam(params, lr=self.lr, betas=(0.9, 0.999), eps=1e-08)
        self.grads = []
        self.notprove_epoch=0


    def hook_fn(self, grad):
        self.grads.append(grad.abs().max())
        return grad
        
    def test(self, test_dataloader,output,model_path,args,scaler=None,):
        if os.path.exists(model_path):
            checkpoint=torch.load(model_path,map_location=torch.device('cpu'))
            self.model.load_state_dict(checkpoint["net_state_dict"])
            self.optim = checkpoint["optim"]
            print("最终模型已成功加载。")   
        else:
            raise RuntimeError("未成功加载模型！请--model_path指定模型参数路径")
        test_iter = iter(test_dataloader)
        print('============Begin Testing============')
        epoch_size = len(test_dataloader)
        self.model.eval()

        with torch.no_grad():
            for i in range(epoch_size):

                cate, cont, = next(test_iter)
                pred = self.model(cate, cont,None )
                if i == 0:
                    total_pred = pred
                else:
                    total_pred = torch.cat([total_pred, pred], dim=0)

        # 保存结果
        output['DeepFI']=total_pred
        print('============End Testing============')
        return output

    def init_writer(self):

        if not os.path.exists(self.args.save_folder):
            os.makedirs(self.args.save_folder, exist_ok=True)

        log_path = os.path.join(self.args.save_log, self.args.exp_name)
        log_config_path = os.path.join(log_path, 'configs.log')

        self.writer = SummaryWriter(log_path)
        with open(log_config_path, 'w') as f:
            f.write(arg2str(self.args))


    def delete_model(self, best, index):
        if index == 0 or index == 1000000:
            return
        save_fname = '{}_{}_{:.4f}.pth'.format (self.args.model_name, best, index)
        save_path = os.path.join(self.args.save_folder, self.args.exp_name, save_fname)
        if os.path.exists(save_path):
            os.remove(save_path)

def write_scalars(writer, scalars, names, n_iter, tag=None):
    for scalar, name in zip(scalars, names):
        if tag is not None:
            name = '/'.join([tag, name])
        writer.add_scalar(name, scalar, n_iter)
