import torch
import torch.nn.functional as F
from torch import nn, einsum
from einops import rearrange
import math
from typing import List, Optional, Union

# ----------------------------------- 辅助模块 -----------------------------------
import torch
import torch.nn as nn
import torch.nn.functional as F

import torch
import torch.nn as nn
import torch.nn.functional as F

# class InducedPointAggregator(nn.Module):
#     """
#     基于诱导点的集合聚合器，兼容旧版 PyTorch（无 batch_first）。
#     参考：Set Transformer (Lee et al., 2019)
#     """
#     def __init__(self, head_dim, num_heads=4, ff_mult=2, dropout=0.0):
#         super().__init__()
#         self.head_dim = head_dim
#         self.num_heads = num_heads

#         # 可学习的诱导点（1个）
#         self.inducing = nn.Parameter(torch.randn(1, 1, head_dim))  # (1, 1, d)

#         # 交叉注意力（不使用 batch_first）
#         self.cross_attn = nn.MultiheadAttention(head_dim, num_heads, dropout=dropout)

#         # 前馈网络
#         self.ffn = nn.Sequential(
#             nn.Linear(head_dim, head_dim * ff_mult),
#             nn.GELU(),
#             nn.Dropout(dropout),
#             nn.Linear(head_dim * ff_mult, head_dim* ff_mult),
#             nn.GELU(),
#             nn.Dropout(dropout),
#             nn.Linear(head_dim * ff_mult, head_dim),
#             # nn.Dropout(dropout)
#         )

#         self.norm1 = nn.LayerNorm(head_dim)
#         # self.norm2 = nn.LayerNorm(head_dim)

#     def forward(self, gathered):
#         """
#         Args:
#             gathered: (batch, heads, num_queries, num_per_group, head_dim)
#         Returns:
#             aggregated: (batch, heads, num_queries, head_dim)
#         """
#         b, h, q, k, d = gathered.shape

#         # 合并 batch、head、query 维度，每个集合独立处理
#         gathered_flat = gathered.view(b * h * q, k, d)          # (b*h*q, k, d)
#         inducing = self.inducing.expand(b * h * q, -1, -1)      # (b*h*q, 1, d)

#         # 转换为 (seq_len, batch, embed_dim) 格式
#         gathered_t = gathered_flat.transpose(0, 1)   # (k, b*h*q, d)
#         inducing_t = inducing.transpose(0, 1)        # (1, b*h*q, d)

#         # 交叉注意力：诱导点作为 query，集合作为 key/value
#         h_attn_t, _ = self.cross_attn(inducing_t, gathered_t, gathered_t)  # (1, b*h*q, d)

#         # 转回 (b*h*q, 1, d)
#         h_attn = h_attn_t.transpose(0, 1)

#         # 残差连接 + LayerNorm
#         h_attn = self.norm1(h_attn + inducing)

#         # 前馈网络
#         h_out = self.ffn(h_attn)
#         # h_out = self.norm2(h_out + h_attn)

#         # 去掉长度为1的维度，得到 (b*h*q, d)
#         aggregated = h_out.squeeze(1)

#         # 恢复形状
#         return aggregated.view(b, h, q, d)
    
class GEGLU(nn.Module):
    """GEGLU激活函数"""
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x, gates = x.chunk(2, dim=-1)
        return x * F.gelu(gates)


def FeedForward(dim: int, mult: int = 4, dropout: float = 0.) -> nn.Sequential:
    """前馈网络（包含LayerNorm、GEGLU、Dropout）"""
    return nn.Sequential(
        nn.LayerNorm(dim),
        nn.Linear(dim, dim * mult * 2),
        GEGLU(),
        nn.Dropout(dropout),
        nn.Linear(dim * mult, dim)
    )


class Attention(nn.Module):
    """标准多头自注意力（带LayerNorm）"""
    def __init__(self, heads: int = 8, dim: int = 64, dropout: float = 0., inner_dim: int = 0):
        super().__init__()
        self.heads = heads
        inner_dim = inner_dim if inner_dim > 0 else dim
        self.scale = (inner_dim / heads) ** -0.5

        self.norm = nn.LayerNorm(dim)
        self.to_qkv = nn.Linear(dim, inner_dim * 3, bias=False)
        self.to_out = nn.Linear(inner_dim, dim, bias=False)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, attn_out: bool = False) -> Union[torch.Tensor, tuple]:
        h = self.heads
        x = self.norm(x)

        q, k, v = self.to_qkv(x).chunk(3, dim=-1)
        q, k, v = map(lambda t: rearrange(t, 'b n (h d) -> b h n d', h=h), (q, k, v))
        q = q * self.scale

        sim = einsum('b h i d, b h j d -> b h i j', q, k)
        attn = sim.softmax(dim=-1)
        dropped_attn = self.dropout(attn)

        out = einsum('b h i j, b h j d -> b h i d', dropped_attn, v)
        out = rearrange(out, 'b h n d -> b n (h d)')
        out = self.to_out(out)

        if attn_out:
            return out, attn
        return out


class MemoryBlock(nn.Module):
    """
    记忆块（Memory Block），支持聚类（cluster）和两种聚合方式（sum / prod）。
    可对注意力得分的 top-k 进行分组卷积，实现 token 数量压缩。
    """
    def __init__(
        self,
        token_num: int,                # 输入 token 数量（仅用于构建，不参与计算）
        heads: int,
        dim: int,
        attn_dropout: float,
        cluster: bool,
        target_mode: str,               # 'mix' 或 None
        groups: int,                     # 聚类后的 token 数量
        num_per_group: int,               # 每个聚类的 top-k 数量
        use_cls_token: bool,
        sum_or_prod: str                  # 'sum' 或 'prod'
    ):
        super().__init__()
        self.heads = heads
        self.use_cls_token = use_cls_token
        self.cluster = cluster
        self.target_mode = target_mode
        self.sum_or_prod = sum_or_prod
        self.num_per_group = num_per_group
        self.scale = dim / heads

        if cluster:
            if target_mode == 'mix':
                self.target_token = nn.Parameter(torch.randn([groups, dim]))
                # 将 [target_token, x] 混合后映射回 groups + cls_flag
                self.to_target = nn.Linear(
                    groups + token_num + int(use_cls_token),
                    groups + int(use_cls_token)
                )
            else:
                self.target_token = nn.Parameter(torch.randn([groups + int(use_cls_token), dim]))

        # 如果启用了分组（num_per_group != -1），则使用卷积进行特征聚合
        # if num_per_group != -1:
        #     self.gather_layer = nn.Conv1d(
        #         (groups + int(use_cls_token)) * num_per_group,
        #         groups + int(use_cls_token),
        #         groups=groups + int(use_cls_token),
        #         kernel_size=1
        #     )

        self.soft = nn.Softmax(dim=-1)
        self.dropout = nn.Dropout(attn_dropout)

        self.q = nn.Linear(dim, dim)
        self.k = nn.Linear(dim, dim)
        self.v = nn.Linear(dim, dim)
        self.out = nn.Sequential(
            nn.Linear(dim, dim),
            nn.Dropout(attn_dropout)
        )
        # self.mlp = nn.Sequential(
        #     nn.Linear(64, 64*2),
        #     nn.GELU(),
        #     nn.Linear(64*2, 64)
        # )
        self.mlp = nn.Sequential(
            nn.Linear(64, 64),
            nn.GELU(),
        )
        # pooling 方式可选：mean, max, sum
        self.pool = 'mean'  # 可配置

        # self.aggregator = InducedPointAggregator(
        #         head_dim=dim // heads,
        #         num_heads=8,                # 可调节
        #         ff_mult=2,
        #         dropout=0.3,
        #     )
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, l, d = x.shape
        h = self.heads

        # 乘法分支：取对数（保证非负）
        if self.sum_or_prod == 'prod':
            x = torch.log(F.relu(x) + 1)

        # ========== 确定 query ==========
        if self.cluster:
            target = self.target_token
            target = target.unsqueeze(0).repeat(b, 1, 1)
            if self.target_mode == 'mix':
                target = torch.cat([target, x], dim=-2)
                target = self.to_target(target.transpose(-1, -2)).transpose(-1, -2)
            q = self.q(target)
        else:
            q = self.q(x)

        k = self.k(x)
        v = self.v(x)

        # 多头拆分
        q = q.reshape(b, -1, h, d // h).permute(0, 2, 1, 3)
        k = k.reshape(b, -1, h, d // h).permute(0, 2, 1, 3)
        v = v.reshape(b, -1, h, d // h).permute(0, 2, 1, 3)

        # ========== 注意力计算 ==========
        attn = self.soft(torch.matmul(q, k.transpose(-1, -2)) * (self.scale ** -0.5))
        attn = self.dropout(attn)
        
        # ========== 基于 top-k 选取并聚合 ==========
        if self.num_per_group == -1:
            # 不使用分组，直接加权求和
            x = einsum('b h i j, b h j d -> b h i d', attn, v)
        else:
            # 取每个 query 的 top-k 个 key
            values, indices = torch.topk(attn, dim=-1, k=self.num_per_group)
            
            # 扩展索引以匹配 v 的维度
            idx = indices.unsqueeze(-1).repeat(1, 1, 1, 1, d // h)
            # 扩展 v 以进行 gather
            vv = v.unsqueeze(-2).repeat(1, 1, 1, self.num_per_group, 1)
            # 收集选中的 value
            gathered = torch.gather(vv, 2, idx)  # (b, h, groups+flag, num_per_group, d//h)

            ################################
            # values = values / (values.sum(dim=-1, keepdim=True) + 1e-8)
            # b, h, q, k, d = gathered.shape
            # gathered_flat = gathered.view(-1, k, d)  # [b*h*q, k, d]
            # # transformed = self.mlp(gathered_flat)     # [b*h*q, k, d]
            # values_flat = values.view(-1, k, 1) 

            # weighted = gathered_flat * values_flat
            # pooled = weighted.sum(dim=1)                               # (b*h*q, head_dim)
            # x = pooled.view(b, h, q, d)
            ################################


            ################################
            # b, h, q, k, d = gathered.shape
            # gathered_flat = gathered.view(-1, k, d)  # [b*h*q, k, d]
            # transformed = self.mlp(gathered_flat)     # [b*h*q, k, d]
            # if self.pool == 'mean':
            #     pooled = transformed.mean(dim=1)       # [b*h*q, d]
            # elif self.pool == 'max':
            #     pooled = transformed.max(dim=1)[0]
            # else: # sum
            #     pooled = transformed.sum(dim=1)
            # x=pooled.view(b, h, q, d)
            ################################


            ################################
            if self.pool == 'mean':
                x = gathered.mean(dim=-2)       # [b*h*q, d]
            elif self.pool == 'max':
                x = gathered.max(dim=-2)[0]
            else: # sum
                x = gathered.sum(dim=-2)
            ################################


            ################################
            # x=self.aggregator(gathered)
            ################################


            ################################
            # # 重塑并用卷积聚合
            # # gathered = gathered.reshape(b * h, -1, d // h)
            # # x = self.gather_layer(gathered).reshape(b, h, -1, d // h)
            ################################

            ################################
            # b, h, q, k, d = gathered.shape
            # gathered_flat = gathered.view(-1, k, d)  # [b*h*q, k, d]

            # transformed = self.mlp(gathered_flat)     # [b*h*q, k, d]
            # if self.pool == 'mean':
            #     pooled = transformed.mean(dim=1)       # [b*h*q, d]
            # elif self.pool == 'max':
            #     pooled = transformed.max(dim=1)[0]
            # else: # sum
            #     pooled = transformed.sum(dim=1)
            # x=pooled.view(b, h, q, d)
            # ###############################

        # att: torch.Size([256, 8, 47, 47])
        # indices: torch.Size([256, 8, 47, 8])
        # idx: torch.Size([256, 8, 47, 8, 64])
        # vv: torch.Size([256, 8, 47, 8, 64])
        # gathered: torch.Size([256, 8, 47, 8, 64])
        # gathered: torch.Size([2048, 376, 64])
        # x: torch.Size([256, 8, 47, 64])

        # ========== 乘法分支后处理 ==========
        if self.sum_or_prod == 'prod':
            x = (x - x.min()) / (x.max() - x.min())
            x = torch.exp(x)

        out = rearrange(x, 'b h n d -> b n (h d)')
        out = self.out(out)
        return out

class DynamicGatedFusion(nn.Module):
    """动态门控融合（基于CTGFSR, 2025）"""
    def __init__(self, dim=192):
        super().__init__()
        # 门控网络
        self.gate_net = nn.Sequential(
            nn.Linear(dim * 2, dim),
            nn.LayerNorm(dim),
            nn.GELU(),
            nn.Linear(dim, 2),  # 输出2个门控值
            nn.Softmax(dim=-1)
        )
        self.fusion_proj = nn.Linear(dim * 2, dim)
    
    def forward(self, sum_out, prod_out):
        # sum_out, prod_out: (batch, 47, 192)
        
        # 拼接特征
        combined = torch.cat([sum_out, prod_out], dim=-1)  # (batch, 47, 384)
        
        # 计算动态门控权重
        gates = self.gate_net(combined)  # (batch, 47, 2)
        gate_sum = gates[:, :, 0:1]      # (batch, 47, 1)
        gate_prod = gates[:, :, 1:2]     # (batch, 47, 1)
        
        # 门控加权
        weighted_sum = sum_out * gate_sum
        weighted_prod = prod_out * gate_prod
        
        # 融合投影
        fused = torch.cat([weighted_sum, weighted_prod], dim=-1)
        output = self.fusion_proj(fused)  # (batch, 47, 192)
        
        return output
    
class Transformer(nn.Module):
    """
    多层 Transformer，每层包含可选的乘积记忆块、求和记忆块、融合线性层、
    token 数量压缩层和前馈网络。
    """
    def __init__(
        self,
        dim: int,
        depth: int,
        heads: int,
        attn_dropout: float,
        ff_dropout: float,
        use_cls_token: bool,
        groups: List[int],
        sum_num_per_group: List[int],
        prod_num_per_group: List[int],
        cluster: bool,
        target_mode: str,
        token_num: int,
        token_descent: bool = False,
        use_prod: bool = True,
    ):
        super().__init__()
        self.layers = nn.ModuleList([])
        flag = int(use_cls_token)

        # 如果不进行 token 数量下降，则每层的输出 token 数保持为输入 token_num
        if not token_descent:
            groups = [token_num for _ in groups]


        for i in range(depth):
            # 当前层的输入 token 数（仅用于记忆块打印，实际未使用）
            cur_token_num = token_num if i == 0 else groups[i-1]

            # 乘积记忆块（prod）
            prod_block = MemoryBlock(
                token_num=cur_token_num,
                heads=heads,
                dim=dim,
                attn_dropout=attn_dropout,
                cluster=cluster,
                target_mode=target_mode,
                groups=groups[i],
                num_per_group=prod_num_per_group[i],
                use_cls_token=use_cls_token,
                sum_or_prod='prod'
            ) if use_prod else nn.Identity()

            # 求和记忆块（sum）——若 token_descent 为 False 则替换为标准 Attention
            sum_block = MemoryBlock(
                token_num=cur_token_num,
                heads=heads,
                dim=dim,
                attn_dropout=attn_dropout,
                cluster=cluster,
                target_mode=target_mode,
                groups=groups[i],
                num_per_group=sum_num_per_group[i],
                use_cls_token=use_cls_token,
                sum_or_prod='sum'
            ) if token_descent else Attention(heads=heads, dim=dim, dropout=attn_dropout)

            # 融合两个分支的线性层
            fusion = nn.Linear(2 * (groups[i] + flag), groups[i] + flag)

            test_fusion = nn.Linear(groups[i] + flag, groups[i] + flag)

            # token 数量下降层（将输入 token 数压缩到 groups[i] + flag）
            downsample = nn.Linear(token_num + flag, groups[i] + flag) if token_descent else nn.Identity()

            # 前馈网络
            ff = FeedForward(dim, dropout=ff_dropout)

            self.layers.append(nn.ModuleList([prod_block, sum_block, fusion,test_fusion, downsample, ff]))

        self.use_prod = use_prod
        self.gate=DynamicGatedFusion(dim=dim)

    # def forward(self, x: torch.Tensor) -> torch.Tensor:
    #     for prod_block, sum_block, fusion, downsample, ff in self.layers:
    #         attn_out = sum_block(x)

    #         if self.use_prod:
    #             prod_out = prod_block(x)
    #             # 拼接两个分支并通过融合层
    #             combined = torch.cat([attn_out, prod_out], dim=-2)  # (b, n1+n2, d)
    #             combined = combined.transpose(-1, -2)              # (b, d, n1+n2)
    #             attn_out = fusion(combined).transpose(-1, -2)      # (b, new_n, d)

    #         # 压缩 token 数量（如果启用）
    #         x_res = downsample(x.transpose(-1, -2)).transpose(-1, -2)
    #         x = attn_out + x_res
    #         x = ff(x) + x
    #     return x
     
    # test
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for prod_block, sum_block, fusion, test_fusion,downsample, ff in self.layers:
            attn_out = sum_block(x)
            # prod_out = prod_block(x)
            if self.use_prod:
                prod_out = prod_block(x)
                # attn_out=self.gate(attn_out, prod_out)
                combined = torch.cat([attn_out,prod_out], dim=-2)  # (b, n1+n2, d)
                combined = combined.transpose(-1, -2)              # (b, d, n1+n2)
                attn_out = fusion(combined).transpose(-1, -2)      # (b, new_n, d)
               
            x_res = downsample(x.transpose(-1, -2)).transpose(-1, -2)
            x = attn_out + x_res
            x = ff(x) + x
        return x


class NumericalEmbedder(nn.Module):
    """连续特征嵌入层：对每个数值特征学习一个线性变换"""
    def __init__(self, dim: int, num_numerical_types: int):
        super().__init__()
        self.weights = nn.Parameter(torch.randn(num_numerical_types, dim))
        self.biases = nn.Parameter(torch.randn(num_numerical_types, dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, num_numerical)
        x = x.unsqueeze(-1)  # (batch, num_numerical, 1)
        return x * self.weights + self.biases


class FTTransformer(nn.Module):
    """
    FT-Transformer 主模型
    参数说明：
        dim: token 维度
        depth: Transformer 层数
        heads: 多头注意力的头数
        attn_dropout: 注意力层 dropout
        ff_dropout: 前馈网络 dropout
        use_cls_token: 是否使用 [CLS] token
        groups: 每层聚类后的 token 数量列表（长度 = depth）
        sum_num_per_group: 求和分支每组的 top-k 数量列表
        prod_num_per_group: 乘积分支每组的 top-k 数量列表
        cluster: 是否启用聚类（若 False 则 query 来自输入 x）
        target_mode: 聚类模式，'mix' 或 None
        token_descent: 是否逐层减少 token 数量
        use_prod: 是否使用乘积分支
        num_special_tokens: 特殊 token 数量（如 [PAD], [MASK]）
        num_unique_categories: 所有离散特征的总类别数（用于 embedding 表大小）
        out: 输出维度（回归=1，分类=类别数）
        num_cont: 连续特征的数量
        num_cate: 离散特征的数量
        use_sigmoid: 回归任务时是否对输出应用 sigmoid
    """
    def __init__(
        self,
        dim: int = 192,
        depth: int = 3,
        heads: int = 8,
        attn_dropout: float = 0.2,
        ff_dropout: float = 0.1,
        use_cls_token: bool = True,
        groups: List[int] = [54, 54, 54],
        sum_num_per_group: List[int] = [32, 16, 8],
        prod_num_per_group: List[int] = [6, 6, 6],
        cluster: bool = True,
        target_mode: str = 'mix',
        token_descent: bool = True,
        use_prod: bool = True,
        num_special_tokens: int = 200,
        num_unique_categories: int = 10000,
        out: int = 2,
        num_cont: int = 104,
        num_cate: int = 16,
        use_sigmoid: bool = True,
    ):
        super().__init__()

        token_num = num_cont + num_cate

        # 离散特征嵌入表（+1 用于 [MASK] 等，+num_special_tokens 根据需求调整）
        if num_unique_categories > 0:
            total_tokens = num_unique_categories + num_special_tokens + 1
            self.categorical_embeds = nn.Embedding(total_tokens, dim)

        # 连续特征嵌入
        if num_cont > 0:
            self.numerical_embedder = NumericalEmbedder(dim, num_cont)

        # [CLS] token
        self.cls_token = nn.Parameter(torch.randn(1, 1, dim))

        # 主 Transformer
        self.transformer = Transformer(
            dim=dim,
            depth=depth,
            heads=heads,
            attn_dropout=attn_dropout,
            ff_dropout=ff_dropout,
            use_cls_token=use_cls_token,
            groups=groups,
            sum_num_per_group=sum_num_per_group,
            prod_num_per_group=prod_num_per_group,
            cluster=cluster,
            target_mode=target_mode,
            token_num=token_num,
            token_descent=token_descent,
            use_prod=use_prod,
        )

        # 输出层
        self.to_logits = nn.Sequential(
            nn.LayerNorm(dim),
            nn.ReLU(),
            nn.Linear(dim, out)
        )

        # 如果不使用 [CLS]，则通过池化将 token 数压缩为 1
        self.pool = nn.Linear(num_cont + num_cate, 1)

        # 其他参数
        self.use_sigmoid = use_sigmoid
        self.use_cls_token = use_cls_token
        self.num_unique_categories = num_unique_categories
        self.num_cont = num_cont
        self.out = out

    def forward(self, x_categ: torch.Tensor, x_numer: torch.Tensor, label: Optional[torch.Tensor] = None, step: int = 0):
        """
        Args:
            x_categ: 离散特征索引，形状 (batch, num_cate)
            x_numer: 连续特征值，形状 (batch, num_cont)
            label:  标签（可选），用于训练时计算损失
        Returns:
            logit: 模型输出
            loss:  如果 label 不为 None 则返回损失，否则返回 0
        """
        # 确保离散特征为 long 类型
        if self.num_unique_categories > 0:
            x_categ = x_categ.long()
        xs = []
        if self.num_unique_categories > 0:
            xs.append(self.categorical_embeds(x_categ))
        if self.num_cont > 0:
            xs.append(self.numerical_embedder(x_numer))

        x = torch.cat(xs, dim=1)  # (batch, num_cate+num_cont, dim)
        b = x.shape[0]

        if self.use_cls_token:
            cls_tokens = self.cls_token.repeat(b, 1, 1)
            x = torch.cat([cls_tokens, x], dim=1)
        # Transformer 前向
        x = self.transformer(x)

        if self.use_cls_token:
            x = x[:, 0]    
        else:
            x = self.pool(x.transpose(-1, -2)).squeeze(-1)  # (batch, dim)
        x = self.to_logits(x)
        # 损失计算
        loss = torch.tensor(0., device=x.device)
        x = torch.sigmoid(x)

        return x#, loss


        