import cPickle

import mxnet as mx

from utils.symbol import Symbol
from operator_py.proposal import *
from operator_py.proposal_annotator import *
from operator_py.box_parser import *
from operator_py.box_annotator_ohem import *


class resnext_101_fcis(Symbol):

    def __init__(self):
        """
        Use __init__ to define parameter network needs
        """
        self.eps = 1e-5
        self.use_global_stats = True
        self.workspace = 512
        self.units = (3, 4, 23, 3)  # use for 101
        self.filter_list = [256, 512, 1024, 2048]

    def get_resnext_conv4(self, data, is_train, num_group=32):
        """

        :param data:
        :param num_group:
        :return:
        """
        """----------------------------------------------------------------------------------------------------------"""

        # batch normalization
        data = mx.sym.BatchNorm(name='bn_data', data=data, fix_gamma=True, eps=2 * self.eps)

        """----------------------------------------------------------------------------------------------------------"""

        # res1
        conv0 = mx.symbol.Convolution(name='conv0', data=data, num_filter=64, pad=(3, 3), kernel=(7, 7), stride=(2, 2),
                                      no_bias=True)
        bn0 = mx.symbol.BatchNorm(name='bn0', data=conv0, use_global_stats=True, fix_gamma=False, eps=self.eps)
        scale_conv0 = bn0
        relu0 = mx.symbol.Activation(name='relu0', data=scale_conv0, act_type='relu')
        pool0 = mx.symbol.Pooling(name='pooling0', data=relu0, pooling_convention='full', pad=(0, 0), kernel=(3, 3),
                                  stride=(2, 2), pool_type='max')

        """----------------------------------------------------------------------------------------------------------"""

        # stage1
        # res2a unit1
        # branch 1
        res2a_branch1 = mx.symbol.Convolution(name='stage1_unit1_sc', data=pool0, num_filter=256, pad=(0, 0),
                                              kernel=(1, 1),
                                              stride=(1, 1), no_bias=True)
        bn2a_branch1 = mx.symbol.BatchNorm(name='stage1_unit1_sc_bn', data=res2a_branch1, use_global_stats=True,
                                           fix_gamma=False, eps=self.eps)
        scale2a_branch1 = bn2a_branch1

        # branch 2
        res2a_branch2a = mx.symbol.Convolution(name='stage1_unit1_conv1', data=pool0, num_filter=128, pad=(0, 0),
                                               kernel=(1, 1),
                                               stride=(1, 1), no_bias=True)
        bn2a_branch2a = mx.symbol.BatchNorm(name='stage1_unit1_bn1', data=res2a_branch2a, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale2a_branch2a = bn2a_branch2a
        res2a_branch2a_relu = mx.symbol.Activation(name='stage1_unit1_relu1', data=scale2a_branch2a, act_type='relu')
        res2a_branch2b = mx.symbol.Convolution(name='stage1_unit1_conv2', data=res2a_branch2a_relu, num_filter=128,
                                               num_group=num_group,
                                               pad=(1, 1),
                                               kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn2a_branch2b = mx.symbol.BatchNorm(name='stage1_unit1_bn2', data=res2a_branch2b, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale2a_branch2b = bn2a_branch2b
        res2a_branch2b_relu = mx.symbol.Activation(name='stage1_unit1_relu2', data=scale2a_branch2b, act_type='relu')
        res2a_branch2c = mx.symbol.Convolution(name='stage1_unit1_conv3', data=res2a_branch2b_relu, num_filter=256,
                                               pad=(0, 0),
                                               kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn2a_branch2c = mx.symbol.BatchNorm(name='stage1_unit1_bn3', data=res2a_branch2c, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale2a_branch2c = bn2a_branch2c

        # concatenate
        res2a = mx.symbol.broadcast_add(name='res2a', *[scale2a_branch1, scale2a_branch2c])
        res2a_relu = mx.symbol.Activation(name='stage1_unit1_relu', data=res2a, act_type='relu')

        # res2b unit2
        # branch 2
        res2b_branch2a = mx.symbol.Convolution(name='stage1_unit2_conv1', data=res2a_relu, num_filter=128, pad=(0, 0),
                                               kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn2b_branch2a = mx.symbol.BatchNorm(name='stage1_unit2_bn1', data=res2b_branch2a, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale2b_branch2a = bn2b_branch2a
        res2b_branch2a_relu = mx.symbol.Activation(name='stage1_unit2_relu1', data=scale2b_branch2a, act_type='relu')
        res2b_branch2b = mx.symbol.Convolution(name='stage1_unit2_conv2', data=res2b_branch2a_relu, num_filter=128,
                                               num_group=num_group,
                                               pad=(1, 1),
                                               kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn2b_branch2b = mx.symbol.BatchNorm(name='stage1_unit2_bn2', data=res2b_branch2b, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale2b_branch2b = bn2b_branch2b
        res2b_branch2b_relu = mx.symbol.Activation(name='stage1_unit2_relu2', data=scale2b_branch2b, act_type='relu')
        res2b_branch2c = mx.symbol.Convolution(name='stage1_unit2_conv3', data=res2b_branch2b_relu, num_filter=256,
                                               pad=(0, 0),
                                               kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn2b_branch2c = mx.symbol.BatchNorm(name='stage1_unit2_bn3', data=res2b_branch2c, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale2b_branch2c = bn2b_branch2c

        # concatenate
        res2b = mx.symbol.broadcast_add(name='res2b', *[res2a_relu, scale2b_branch2c])
        res2b_relu = mx.symbol.Activation(name='stage1_unit2_relu', data=res2b, act_type='relu')

        # res2c unit3
        # branch 2
        res2c_branch2a = mx.symbol.Convolution(name='stage1_unit3_conv1', data=res2b_relu, num_filter=128, pad=(0, 0),
                                               kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn2c_branch2a = mx.symbol.BatchNorm(name='stage1_unit3_bn1', data=res2c_branch2a, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale2c_branch2a = bn2c_branch2a
        res2c_branch2a_relu = mx.symbol.Activation(name='stage1_unit3_relu1', data=scale2c_branch2a, act_type='relu')
        res2c_branch2b = mx.symbol.Convolution(name='stage1_unit3_conv2', data=res2c_branch2a_relu, num_filter=128,
                                               num_group=num_group,
                                               pad=(1, 1),
                                               kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn2c_branch2b = mx.symbol.BatchNorm(name='stage1_unit3_bn2', data=res2c_branch2b, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale2c_branch2b = bn2c_branch2b
        res2c_branch2b_relu = mx.symbol.Activation(name='stage1_unit3_relu2', data=scale2c_branch2b, act_type='relu')
        res2c_branch2c = mx.symbol.Convolution(name='stage1_unit3_conv3', data=res2c_branch2b_relu, num_filter=256,
                                               pad=(0, 0),
                                               kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn2c_branch2c = mx.symbol.BatchNorm(name='stage1_unit3_bn3', data=res2c_branch2c, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale2c_branch2c = bn2c_branch2c

        # concatenate
        res2c = mx.symbol.broadcast_add(name='res2c', *[res2b_relu, scale2c_branch2c])
        res2c_relu = mx.symbol.Activation(name='stage1_unit3_relu', data=res2c, act_type='relu')

        """----------------------------------------------------------------------------------------------------------"""

        # res3a stage2
        # branch 1 unit1
        res3a_branch1 = mx.symbol.Convolution(name='stage2_unit1_sc', data=res2c_relu, num_filter=512, pad=(0, 0),
                                              kernel=(1, 1), stride=(2, 2), no_bias=True)
        bn3a_branch1 = mx.symbol.BatchNorm(name='stage2_unit1_sc_bn', data=res3a_branch1, use_global_stats=True,
                                           fix_gamma=False, eps=self.eps)
        scale3a_branch1 = bn3a_branch1

        # branch 2
        res3a_branch2a = mx.symbol.Convolution(name='stage2_unit1_conv1', data=res2c_relu, num_filter=256, pad=(0, 0),
                                               kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn3a_branch2a = mx.symbol.BatchNorm(name='stage2_unit1_bn1', data=res3a_branch2a, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale3a_branch2a = bn3a_branch2a
        res3a_branch2a_relu = mx.symbol.Activation(name='stage2_unit1_relu1', data=scale3a_branch2a, act_type='relu')
        res3a_branch2b = mx.symbol.Convolution(name='stage2_unit1_conv2', data=res3a_branch2a_relu, num_filter=256,
                                               pad=(1, 1),
                                               num_group=num_group,
                                               kernel=(3, 3), stride=(2, 2), no_bias=True)
        bn3a_branch2b = mx.symbol.BatchNorm(name='stage2_unit1_bn2', data=res3a_branch2b, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale3a_branch2b = bn3a_branch2b
        res3a_branch2b_relu = mx.symbol.Activation(name='stage2_unit1_relu2', data=scale3a_branch2b, act_type='relu')
        res3a_branch2c = mx.symbol.Convolution(name='stage2_unit1_conv3', data=res3a_branch2b_relu, num_filter=512,
                                               pad=(0, 0),
                                               kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn3a_branch2c = mx.symbol.BatchNorm(name='stage2_unit1_bn3', data=res3a_branch2c, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale3a_branch2c = bn3a_branch2c

        # concatenate
        res3a = mx.symbol.broadcast_add(name='res3a', *[scale3a_branch1, scale3a_branch2c])
        res3a_relu = mx.symbol.Activation(name='stage2_unit1_relu', data=res3a, act_type='relu')

        # res3b1 unit2
        # branch 2
        res3b1_branch2a = mx.symbol.Convolution(name='stage2_unit2_conv1', data=res3a_relu, num_filter=256, pad=(0, 0),
                                                kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn3b1_branch2a = mx.symbol.BatchNorm(name='stage2_unit2_bn1', data=res3b1_branch2a, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale3b1_branch2a = bn3b1_branch2a
        res3b1_branch2a_relu = mx.symbol.Activation(name='stage2_unit2_relu1', data=scale3b1_branch2a,
                                                    act_type='relu')
        res3b1_branch2b = mx.symbol.Convolution(name='stage2_unit2_conv2', data=res3b1_branch2a_relu, num_filter=256,
                                                num_group=num_group, pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn3b1_branch2b = mx.symbol.BatchNorm(name='stage2_unit2_bn2', data=res3b1_branch2b, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale3b1_branch2b = bn3b1_branch2b
        res3b1_branch2b_relu = mx.symbol.Activation(name='stage2_unit2_relu2', data=scale3b1_branch2b,
                                                    act_type='relu')
        res3b1_branch2c = mx.symbol.Convolution(name='stage2_unit2_conv3', data=res3b1_branch2b_relu, num_filter=512,
                                                pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn3b1_branch2c = mx.symbol.BatchNorm(name='stage2_unit2_bn3', data=res3b1_branch2c, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale3b1_branch2c = bn3b1_branch2c

        # concatenate
        res3b1 = mx.symbol.broadcast_add(name='res3b1', *[res3a_relu, scale3b1_branch2c])
        res3b1_relu = mx.symbol.Activation(name='stage2_unit2_relu', data=res3b1, act_type='relu')

        # res3b2 unit 3
        # branch 2
        res3b2_branch2a = mx.symbol.Convolution(name='stage2_unit3_conv1', data=res3b1_relu, num_filter=256, pad=(0, 0),
                                                kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn3b2_branch2a = mx.symbol.BatchNorm(name='stage2_unit3_bn1', data=res3b2_branch2a, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale3b2_branch2a = bn3b2_branch2a
        res3b2_branch2a_relu = mx.symbol.Activation(name='stage2_unit3_relu1', data=scale3b2_branch2a,
                                                    act_type='relu')
        res3b2_branch2b = mx.symbol.Convolution(name='stage2_unit3_conv2', data=res3b2_branch2a_relu, num_filter=256,
                                                num_group=num_group, pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn3b2_branch2b = mx.symbol.BatchNorm(name='stage2_unit3_bn2', data=res3b2_branch2b, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale3b2_branch2b = bn3b2_branch2b
        res3b2_branch2b_relu = mx.symbol.Activation(name='stage2_unit3_relu2', data=scale3b2_branch2b,
                                                    act_type='relu')
        res3b2_branch2c = mx.symbol.Convolution(name='stage2_unit3_conv3', data=res3b2_branch2b_relu, num_filter=512,
                                                pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn3b2_branch2c = mx.symbol.BatchNorm(name='stage2_unit3_bn3', data=res3b2_branch2c, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale3b2_branch2c = bn3b2_branch2c

        # concatenate
        res3b2 = mx.symbol.broadcast_add(name='res3b2', *[res3b1_relu, scale3b2_branch2c])
        res3b2_relu = mx.symbol.Activation(name='stage2_unit3_relu', data=res3b2, act_type='relu')

        # res3b3 unit4
        # branch 2
        res3b3_branch2a = mx.symbol.Convolution(name='stage2_unit4_conv1', data=res3b2_relu, num_filter=256, pad=(0, 0),
                                                kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn3b3_branch2a = mx.symbol.BatchNorm(name='stage2_unit4_bn1', data=res3b3_branch2a, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale3b3_branch2a = bn3b3_branch2a
        res3b3_branch2a_relu = mx.symbol.Activation(name='stage2_unit4_relu1', data=scale3b3_branch2a,
                                                    act_type='relu')
        res3b3_branch2b = mx.symbol.Convolution(name='stage2_unit4_conv2', data=res3b3_branch2a_relu, num_filter=256,
                                                num_group=num_group, pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn3b3_branch2b = mx.symbol.BatchNorm(name='stage2_unit4_bn2', data=res3b3_branch2b, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale3b3_branch2b = bn3b3_branch2b
        res3b3_branch2b_relu = mx.symbol.Activation(name='stage2_unit4_relu2', data=scale3b3_branch2b,
                                                    act_type='relu')
        res3b3_branch2c = mx.symbol.Convolution(name='stage2_unit4_conv3', data=res3b3_branch2b_relu, num_filter=512,
                                                pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn3b3_branch2c = mx.symbol.BatchNorm(name='stage2_unit4_bn3', data=res3b3_branch2c, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale3b3_branch2c = bn3b3_branch2c

        # concatenate
        res3b3 = mx.symbol.broadcast_add(name='res3b3', *[res3b2_relu, scale3b3_branch2c])
        res3b3_relu = mx.symbol.Activation(name='stage2_unit4_relu', data=res3b3, act_type='relu')

        """----------------------------------------------------------------------------------------------------------"""

        # res4a stage3 unit1
        # branch 1
        res4a_branch1 = mx.symbol.Convolution(name='stage3_unit1_sc', data=res3b3_relu, num_filter=1024, pad=(0, 0),
                                              kernel=(1, 1), stride=(2, 2), no_bias=True)
        bn4a_branch1 = mx.symbol.BatchNorm(name='stage3_unit1_sc_bn', data=res4a_branch1, use_global_stats=True,
                                           fix_gamma=False, eps=self.eps)
        scale4a_branch1 = bn4a_branch1

        # branch 2
        res4a_branch2a = mx.symbol.Convolution(name='stage3_unit1_conv1', data=res3b3_relu, num_filter=512, pad=(0, 0),
                                               kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4a_branch2a = mx.symbol.BatchNorm(name='stage3_unit1_bn1', data=res4a_branch2a, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale4a_branch2a = bn4a_branch2a
        res4a_branch2a_relu = mx.symbol.Activation(name='stage3_unit1_relu1', data=scale4a_branch2a, act_type='relu')
        res4a_branch2b = mx.symbol.Convolution(name='stage3_unit1_conv2', data=res4a_branch2a_relu, num_filter=512,
                                               num_group=num_group,
                                               pad=(1, 1),
                                               kernel=(3, 3), stride=(2, 2), no_bias=True)
        bn4a_branch2b = mx.symbol.BatchNorm(name='stage3_unit1_bn2', data=res4a_branch2b, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale4a_branch2b = bn4a_branch2b
        res4a_branch2b_relu = mx.symbol.Activation(name='stage3_unit1_relu2', data=scale4a_branch2b, act_type='relu')
        res4a_branch2c = mx.symbol.Convolution(name='stage3_unit1_conv3', data=res4a_branch2b_relu, num_filter=1024,
                                               pad=(0, 0),
                                               kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4a_branch2c = mx.symbol.BatchNorm(name='stage3_unit1_bn3', data=res4a_branch2c, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale4a_branch2c = bn4a_branch2c

        # concatenate
        res4a = mx.symbol.broadcast_add(name='res4a', *[scale4a_branch1, scale4a_branch2c])
        res4a_relu = mx.symbol.Activation(name='stage3_unit1_relu', data=res4a, act_type='relu')

        # res4b1 unit2
        # branch 2
        res4b1_branch2a = mx.symbol.Convolution(name='stage3_unit2_conv1', data=res4a_relu, num_filter=512, pad=(0, 0),
                                                kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b1_branch2a = mx.symbol.BatchNorm(name='stage3_unit2_bn1', data=res4b1_branch2a, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b1_branch2a = bn4b1_branch2a
        res4b1_branch2a_relu = mx.symbol.Activation(name='stage3_unit2_relu1', data=scale4b1_branch2a,
                                                    act_type='relu')
        res4b1_branch2b = mx.symbol.Convolution(name='stage3_unit2_conv2', data=res4b1_branch2a_relu, num_filter=512,
                                                num_group=num_group,
                                                pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b1_branch2b = mx.symbol.BatchNorm(name='stage3_unit2_bn2', data=res4b1_branch2b, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b1_branch2b = bn4b1_branch2b
        res4b1_branch2b_relu = mx.symbol.Activation(name='stage3_unit2_relu2', data=scale4b1_branch2b,
                                                    act_type='relu')
        res4b1_branch2c = mx.symbol.Convolution(name='stage3_unit2_conv3', data=res4b1_branch2b_relu, num_filter=1024,
                                                pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b1_branch2c = mx.symbol.BatchNorm(name='stage3_unit2_bn3', data=res4b1_branch2c, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b1_branch2c = bn4b1_branch2c

        # concatenate
        res4b1 = mx.symbol.broadcast_add(name='res4b1', *[res4a_relu, scale4b1_branch2c])
        res4b1_relu = mx.symbol.Activation(name='stage3_unit2_relu', data=res4b1, act_type='relu')

        # res4b2 unit3
        # branch 2
        res4b2_branch2a = mx.symbol.Convolution(name='stage3_unit3_conv1', data=res4b1_relu, num_filter=512, pad=(0, 0),
                                                kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b2_branch2a = mx.symbol.BatchNorm(name='stage3_unit3_bn1', data=res4b2_branch2a, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b2_branch2a = bn4b2_branch2a
        res4b2_branch2a_relu = mx.symbol.Activation(name='stage3_unit3_relu1', data=scale4b2_branch2a,
                                                    act_type='relu')
        res4b2_branch2b = mx.symbol.Convolution(name='stage3_unit3_conv2', data=res4b2_branch2a_relu, num_filter=512,
                                                num_group=num_group,
                                                pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b2_branch2b = mx.symbol.BatchNorm(name='stage3_unit3_bn2', data=res4b2_branch2b, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b2_branch2b = bn4b2_branch2b
        res4b2_branch2b_relu = mx.symbol.Activation(name='stage3_unit3_relu2', data=scale4b2_branch2b,
                                                    act_type='relu')
        res4b2_branch2c = mx.symbol.Convolution(name='stage3_unit3_conv3', data=res4b2_branch2b_relu, num_filter=1024,
                                                pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b2_branch2c = mx.symbol.BatchNorm(name='stage3_unit3_bn3', data=res4b2_branch2c, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b2_branch2c = bn4b2_branch2c

        # concatenate
        res4b2 = mx.symbol.broadcast_add(name='res4b2', *[res4b1_relu, scale4b2_branch2c])
        res4b2_relu = mx.symbol.Activation(name='stage3_unit3_relu', data=res4b2, act_type='relu')

        # res4b3 unit4
        # branch 2
        res4b3_branch2a = mx.symbol.Convolution(name='stage3_unit4_conv1', data=res4b2_relu, num_filter=512, pad=(0, 0),
                                                kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b3_branch2a = mx.symbol.BatchNorm(name='stage3_unit4_bn1', data=res4b3_branch2a, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b3_branch2a = bn4b3_branch2a
        res4b3_branch2a_relu = mx.symbol.Activation(name='stage3_unit4_relu1', data=scale4b3_branch2a,
                                                    act_type='relu')
        res4b3_branch2b = mx.symbol.Convolution(name='stage3_unit4_conv2', data=res4b3_branch2a_relu, num_filter=512,
                                                num_group=num_group,
                                                pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b3_branch2b = mx.symbol.BatchNorm(name='stage3_unit4_bn2', data=res4b3_branch2b, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b3_branch2b = bn4b3_branch2b
        res4b3_branch2b_relu = mx.symbol.Activation(name='stage3_unit4_relu2', data=scale4b3_branch2b,
                                                    act_type='relu')
        res4b3_branch2c = mx.symbol.Convolution(name='stage3_unit4_conv3', data=res4b3_branch2b_relu, num_filter=1024,
                                                pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b3_branch2c = mx.symbol.BatchNorm(name='stage3_unit4_bn3', data=res4b3_branch2c, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b3_branch2c = bn4b3_branch2c

        # concatenate
        res4b3 = mx.symbol.broadcast_add(name='res4b3', *[res4b2_relu, scale4b3_branch2c])
        res4b3_relu = mx.symbol.Activation(name='stage3_unit4_relu', data=res4b3, act_type='relu')

        # res4b4 unit5
        # branch 2
        res4b4_branch2a = mx.symbol.Convolution(name='stage3_unit5_conv1', data=res4b3_relu, num_filter=512, pad=(0, 0),
                                                kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b4_branch2a = mx.symbol.BatchNorm(name='stage3_unit5_bn1', data=res4b4_branch2a, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b4_branch2a = bn4b4_branch2a
        res4b4_branch2a_relu = mx.symbol.Activation(name='stage3_unit5_relu1', data=scale4b4_branch2a,
                                                    act_type='relu')
        res4b4_branch2b = mx.symbol.Convolution(name='stage3_unit5_conv2', data=res4b4_branch2a_relu, num_filter=512,
                                                num_group=num_group,
                                                pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b4_branch2b = mx.symbol.BatchNorm(name='stage3_unit5_bn2', data=res4b4_branch2b, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b4_branch2b = bn4b4_branch2b
        res4b4_branch2b_relu = mx.symbol.Activation(name='stage3_unit5_relu2', data=scale4b4_branch2b,
                                                    act_type='relu')
        res4b4_branch2c = mx.symbol.Convolution(name='stage3_unit5_conv3', data=res4b4_branch2b_relu, num_filter=1024,
                                                pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b4_branch2c = mx.symbol.BatchNorm(name='stage3_unit5_bn3', data=res4b4_branch2c, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b4_branch2c = bn4b4_branch2c

        # concatenate
        res4b4 = mx.symbol.broadcast_add(name='res4b4', *[res4b3_relu, scale4b4_branch2c])
        res4b4_relu = mx.symbol.Activation(name='stage3_unit5_relu', data=res4b4, act_type='relu')

        # res4b5 unit6
        # branch 2
        res4b5_branch2a = mx.symbol.Convolution(name='stage3_unit6_conv1', data=res4b4_relu, num_filter=512, pad=(0, 0),
                                                kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b5_branch2a = mx.symbol.BatchNorm(name='stage3_unit6_bn1', data=res4b5_branch2a, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b5_branch2a = bn4b5_branch2a
        res4b5_branch2a_relu = mx.symbol.Activation(name='stage3_unit6_relu1', data=scale4b5_branch2a,
                                                    act_type='relu')
        res4b5_branch2b = mx.symbol.Convolution(name='stage3_unit6_conv2', data=res4b5_branch2a_relu, num_filter=512,
                                                num_group=num_group,
                                                pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b5_branch2b = mx.symbol.BatchNorm(name='stage3_unit6_bn2', data=res4b5_branch2b, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b5_branch2b = bn4b5_branch2b
        res4b5_branch2b_relu = mx.symbol.Activation(name='stage3_unit6_relu2', data=scale4b5_branch2b,
                                                    act_type='relu')
        res4b5_branch2c = mx.symbol.Convolution(name='stage3_unit6_conv3', data=res4b5_branch2b_relu, num_filter=1024,
                                                pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b5_branch2c = mx.symbol.BatchNorm(name='stage3_unit6_bn3', data=res4b5_branch2c, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b5_branch2c = bn4b5_branch2c

        # concatenate
        res4b5 = mx.symbol.broadcast_add(name='res4b5', *[res4b4_relu, scale4b5_branch2c])
        res4b5_relu = mx.symbol.Activation(name='stage3_unit6_relu', data=res4b5, act_type='relu')

        # res4b6 unit7
        # branch 2
        res4b6_branch2a = mx.symbol.Convolution(name='stage3_unit7_conv1', data=res4b5_relu, num_filter=512, pad=(0, 0),
                                                kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b6_branch2a = mx.symbol.BatchNorm(name='stage3_unit7_bn1', data=res4b6_branch2a, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b6_branch2a = bn4b6_branch2a
        res4b6_branch2a_relu = mx.symbol.Activation(name='stage3_unit7_relu1', data=scale4b6_branch2a,
                                                    act_type='relu')
        res4b6_branch2b = mx.symbol.Convolution(name='stage3_unit7_conv2', data=res4b6_branch2a_relu, num_filter=512,
                                                num_group=num_group,
                                                pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b6_branch2b = mx.symbol.BatchNorm(name='stage3_unit7_bn2', data=res4b6_branch2b, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b6_branch2b = bn4b6_branch2b
        res4b6_branch2b_relu = mx.symbol.Activation(name='stage3_unit7_relu2', data=scale4b6_branch2b,
                                                    act_type='relu')
        res4b6_branch2c = mx.symbol.Convolution(name='stage3_unit7_conv3', data=res4b6_branch2b_relu, num_filter=1024,
                                                pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b6_branch2c = mx.symbol.BatchNorm(name='stage3_unit7_bn3', data=res4b6_branch2c, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b6_branch2c = bn4b6_branch2c

        # concatenate
        res4b6 = mx.symbol.broadcast_add(name='res4b6', *[res4b5_relu, scale4b6_branch2c])
        res4b6_relu = mx.symbol.Activation(name='stage3_unit7_relu', data=res4b6, act_type='relu')

        # res4b7 unit8
        # branch 2
        res4b7_branch2a = mx.symbol.Convolution(name='stage3_unit8_conv1', data=res4b6_relu, num_filter=512, pad=(0, 0),
                                                kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b7_branch2a = mx.symbol.BatchNorm(name='stage3_unit8_bn1', data=res4b7_branch2a, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b7_branch2a = bn4b7_branch2a
        res4b7_branch2a_relu = mx.symbol.Activation(name='stage3_unit8_relu1', data=scale4b7_branch2a,
                                                    act_type='relu')
        res4b7_branch2b = mx.symbol.Convolution(name='stage3_unit8_conv2', data=res4b7_branch2a_relu, num_filter=512,
                                                num_group=num_group,
                                                pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b7_branch2b = mx.symbol.BatchNorm(name='stage3_unit8_bn2', data=res4b7_branch2b, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b7_branch2b = bn4b7_branch2b
        res4b7_branch2b_relu = mx.symbol.Activation(name='stage3_unit8_relu2', data=scale4b7_branch2b,
                                                    act_type='relu')
        res4b7_branch2c = mx.symbol.Convolution(name='stage3_unit8_conv3', data=res4b7_branch2b_relu, num_filter=1024,
                                                pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b7_branch2c = mx.symbol.BatchNorm(name='stage3_unit8_bn3', data=res4b7_branch2c, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b7_branch2c = bn4b7_branch2c

        # concatenate
        res4b7 = mx.symbol.broadcast_add(name='res4b7', *[res4b6_relu, scale4b7_branch2c])
        res4b7_relu = mx.symbol.Activation(name='stage3_unit8_relu', data=res4b7, act_type='relu')

        # res4b8 unit9
        # branch 2
        res4b8_branch2a = mx.symbol.Convolution(name='stage3_unit9_conv1', data=res4b7_relu, num_filter=512, pad=(0, 0),
                                                kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b8_branch2a = mx.symbol.BatchNorm(name='stage3_unit9_bn1', data=res4b8_branch2a, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b8_branch2a = bn4b8_branch2a
        res4b8_branch2a_relu = mx.symbol.Activation(name='stage3_unit9_relu1', data=scale4b8_branch2a,
                                                    act_type='relu')
        res4b8_branch2b = mx.symbol.Convolution(name='stage3_unit9_conv2', data=res4b8_branch2a_relu, num_filter=512,
                                                num_group=num_group,
                                                pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b8_branch2b = mx.symbol.BatchNorm(name='stage3_unit9_bn2', data=res4b8_branch2b, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b8_branch2b = bn4b8_branch2b
        res4b8_branch2b_relu = mx.symbol.Activation(name='stage3_unit9_relu2', data=scale4b8_branch2b,
                                                    act_type='relu')
        res4b8_branch2c = mx.symbol.Convolution(name='stage3_unit9_conv3', data=res4b8_branch2b_relu, num_filter=1024,
                                                pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b8_branch2c = mx.symbol.BatchNorm(name='stage3_unit9_bn3', data=res4b8_branch2c, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b8_branch2c = bn4b8_branch2c

        # concatenate
        res4b8 = mx.symbol.broadcast_add(name='res4b8', *[res4b7_relu, scale4b8_branch2c])
        res4b8_relu = mx.symbol.Activation(name='stage3_unit9_relu', data=res4b8, act_type='relu')

        # res4b9 unit10
        # branch 2
        res4b9_branch2a = mx.symbol.Convolution(name='stage3_unit10_conv1', data=res4b8_relu, num_filter=512, pad=(0, 0),
                                                kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b9_branch2a = mx.symbol.BatchNorm(name='stage3_unit10_bn1', data=res4b9_branch2a, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b9_branch2a = bn4b9_branch2a
        res4b9_branch2a_relu = mx.symbol.Activation(name='stage3_unit10_relu1', data=scale4b9_branch2a,
                                                    act_type='relu')
        res4b9_branch2b = mx.symbol.Convolution(name='stage3_unit10_conv2', data=res4b9_branch2a_relu, num_filter=512,
                                                num_group=num_group,
                                                pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b9_branch2b = mx.symbol.BatchNorm(name='stage3_unit10_bn2', data=res4b9_branch2b, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b9_branch2b = bn4b9_branch2b
        res4b9_branch2b_relu = mx.symbol.Activation(name='stage3_unit10_relu2', data=scale4b9_branch2b,
                                                    act_type='relu')
        res4b9_branch2c = mx.symbol.Convolution(name='stage3_unit10_conv3', data=res4b9_branch2b_relu, num_filter=1024,
                                                pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b9_branch2c = mx.symbol.BatchNorm(name='stage3_unit10_bn3', data=res4b9_branch2c, use_global_stats=True,
                                             fix_gamma=False, eps=self.eps)
        scale4b9_branch2c = bn4b9_branch2c

        # concatenate
        res4b9 = mx.symbol.broadcast_add(name='res4b9', *[res4b8_relu, scale4b9_branch2c])
        res4b9_relu = mx.symbol.Activation(name='stage3_unit10_relu', data=res4b9, act_type='relu')

        # res4b10 unit11
        # branch 2
        res4b10_branch2a = mx.symbol.Convolution(name='stage3_unit11_conv1', data=res4b9_relu, num_filter=512, pad=(0, 0),
                                                 kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b10_branch2a = mx.symbol.BatchNorm(name='stage3_unit11_bn1', data=res4b10_branch2a, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b10_branch2a = bn4b10_branch2a
        res4b10_branch2a_relu = mx.symbol.Activation(name='stage3_unit11_relu1', data=scale4b10_branch2a,
                                                     act_type='relu')
        res4b10_branch2b = mx.symbol.Convolution(name='stage3_unit11_conv2', data=res4b10_branch2a_relu, num_filter=512,
                                                 num_group=num_group,
                                                 pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b10_branch2b = mx.symbol.BatchNorm(name='stage3_unit11_bn2', data=res4b10_branch2b, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b10_branch2b = bn4b10_branch2b
        res4b10_branch2b_relu = mx.symbol.Activation(name='stage3_unit11_relu2', data=scale4b10_branch2b,
                                                     act_type='relu')
        res4b10_branch2c = mx.symbol.Convolution(name='stage3_unit11_conv3', data=res4b10_branch2b_relu, num_filter=1024,
                                                 pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b10_branch2c = mx.symbol.BatchNorm(name='stage3_unit11_bn3', data=res4b10_branch2c, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b10_branch2c = bn4b10_branch2c

        # concatenate
        res4b10 = mx.symbol.broadcast_add(name='res4b10', *[res4b9_relu, scale4b10_branch2c])
        res4b10_relu = mx.symbol.Activation(name='stage3_unit11_relu', data=res4b10, act_type='relu')

        # res4b11 unit12
        # branch 2
        res4b11_branch2a = mx.symbol.Convolution(name='stage3_unit12_conv1', data=res4b10_relu, num_filter=512, pad=(0, 0),
                                                 kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b11_branch2a = mx.symbol.BatchNorm(name='stage3_unit12_bn1', data=res4b11_branch2a, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b11_branch2a = bn4b11_branch2a
        res4b11_branch2a_relu = mx.symbol.Activation(name='stage3_unit12_relu1', data=scale4b11_branch2a,
                                                     act_type='relu')
        res4b11_branch2b = mx.symbol.Convolution(name='stage3_unit12_conv2', data=res4b11_branch2a_relu, num_filter=512,
                                                 num_group=num_group,
                                                 pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b11_branch2b = mx.symbol.BatchNorm(name='stage3_unit12_bn2', data=res4b11_branch2b, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b11_branch2b = bn4b11_branch2b
        res4b11_branch2b_relu = mx.symbol.Activation(name='stage3_unit12_relu2', data=scale4b11_branch2b,
                                                     act_type='relu')
        res4b11_branch2c = mx.symbol.Convolution(name='stage3_unit12_conv3', data=res4b11_branch2b_relu, num_filter=1024,
                                                 pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b11_branch2c = mx.symbol.BatchNorm(name='stage3_unit12_bn3', data=res4b11_branch2c, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b11_branch2c = bn4b11_branch2c

        # concatenate
        res4b11 = mx.symbol.broadcast_add(name='res4b11', *[res4b10_relu, scale4b11_branch2c])
        res4b11_relu = mx.symbol.Activation(name='stage3_unit12_relu', data=res4b11, act_type='relu')

        # res4b12 unit13
        # branch 2
        res4b12_branch2a = mx.symbol.Convolution(name='stage3_unit13_conv1', data=res4b11_relu, num_filter=512, pad=(0, 0),
                                                 kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b12_branch2a = mx.symbol.BatchNorm(name='stage3_unit13_bn1', data=res4b12_branch2a, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b12_branch2a = bn4b12_branch2a
        res4b12_branch2a_relu = mx.symbol.Activation(name='stage3_unit13_relu1', data=scale4b12_branch2a,
                                                     act_type='relu')
        res4b12_branch2b = mx.symbol.Convolution(name='stage3_unit13_conv2', data=res4b12_branch2a_relu, num_filter=512,
                                                 num_group=num_group,
                                                 pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b12_branch2b = mx.symbol.BatchNorm(name='stage3_unit13_bn2', data=res4b12_branch2b, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b12_branch2b = bn4b12_branch2b
        res4b12_branch2b_relu = mx.symbol.Activation(name='stage3_unit13_relu2', data=scale4b12_branch2b,
                                                     act_type='relu')
        res4b12_branch2c = mx.symbol.Convolution(name='stage3_unit13_conv3', data=res4b12_branch2b_relu, num_filter=1024,
                                                 pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b12_branch2c = mx.symbol.BatchNorm(name='stage3_unit13_bn3', data=res4b12_branch2c, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b12_branch2c = bn4b12_branch2c

        # concatenate
        res4b12 = mx.symbol.broadcast_add(name='res4b12', *[res4b11_relu, scale4b12_branch2c])
        res4b12_relu = mx.symbol.Activation(name='stage3_unit13_relu', data=res4b12, act_type='relu')

        # res4b13 unit14
        res4b13_branch2a = mx.symbol.Convolution(name='stage3_unit14_conv1', data=res4b12_relu, num_filter=512, pad=(0, 0),
                                                 kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b13_branch2a = mx.symbol.BatchNorm(name='stage3_unit14_bn1', data=res4b13_branch2a, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b13_branch2a = bn4b13_branch2a
        res4b13_branch2a_relu = mx.symbol.Activation(name='stage3_unit14_relu1', data=scale4b13_branch2a,
                                                     act_type='relu')
        res4b13_branch2b = mx.symbol.Convolution(name='stage3_unit14_conv2', data=res4b13_branch2a_relu, num_filter=512,
                                                 num_group=num_group,
                                                 pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b13_branch2b = mx.symbol.BatchNorm(name='stage3_unit14_bn2', data=res4b13_branch2b, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b13_branch2b = bn4b13_branch2b
        res4b13_branch2b_relu = mx.symbol.Activation(name='stage3_unit14_relu2', data=scale4b13_branch2b,
                                                     act_type='relu')
        res4b13_branch2c = mx.symbol.Convolution(name='stage3_unit14_conv3', data=res4b13_branch2b_relu, num_filter=1024,
                                                 pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b13_branch2c = mx.symbol.BatchNorm(name='stage3_unit14_bn3', data=res4b13_branch2c, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b13_branch2c = bn4b13_branch2c

        # concatenate
        res4b13 = mx.symbol.broadcast_add(name='res4b13', *[res4b12_relu, scale4b13_branch2c])
        res4b13_relu = mx.symbol.Activation(name='stage3_unit14_relu', data=res4b13, act_type='relu')

        # res4b14 unit15
        # branch 2
        res4b14_branch2a = mx.symbol.Convolution(name='stage3_unit15_conv1', data=res4b13_relu, num_filter=512, pad=(0, 0),
                                                 kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b14_branch2a = mx.symbol.BatchNorm(name='stage3_unit15_bn1', data=res4b14_branch2a, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b14_branch2a = bn4b14_branch2a
        res4b14_branch2a_relu = mx.symbol.Activation(name='stage3_unit15_relu1', data=scale4b14_branch2a,
                                                     act_type='relu')
        res4b14_branch2b = mx.symbol.Convolution(name='stage3_unit15_conv2', data=res4b14_branch2a_relu, num_filter=512,
                                                 num_group=num_group,
                                                 pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b14_branch2b = mx.symbol.BatchNorm(name='stage3_unit15_bn2', data=res4b14_branch2b, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b14_branch2b = bn4b14_branch2b
        res4b14_branch2b_relu = mx.symbol.Activation(name='stage3_unit15_relu2', data=scale4b14_branch2b,
                                                     act_type='relu')
        res4b14_branch2c = mx.symbol.Convolution(name='stage3_unit15_conv3', data=res4b14_branch2b_relu, num_filter=1024,
                                                 pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b14_branch2c = mx.symbol.BatchNorm(name='stage3_unit15_bn3', data=res4b14_branch2c, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b14_branch2c = bn4b14_branch2c

        # concatenate
        res4b14 = mx.symbol.broadcast_add(name='res4b14', *[res4b13_relu, scale4b14_branch2c])
        res4b14_relu = mx.symbol.Activation(name='stage3_unit15_relu', data=res4b14, act_type='relu')

        # res4b15 unit16
        # branch 2
        res4b15_branch2a = mx.symbol.Convolution(name='stage3_unit16_conv1', data=res4b14_relu, num_filter=512, pad=(0, 0),
                                                 kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b15_branch2a = mx.symbol.BatchNorm(name='stage3_unit16_bn1', data=res4b15_branch2a, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b15_branch2a = bn4b15_branch2a
        res4b15_branch2a_relu = mx.symbol.Activation(name='stage3_unit16_relu1', data=scale4b15_branch2a,
                                                     act_type='relu')
        res4b15_branch2b = mx.symbol.Convolution(name='stage3_unit16_conv2', data=res4b15_branch2a_relu, num_filter=512,
                                                 num_group=num_group,
                                                 pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b15_branch2b = mx.symbol.BatchNorm(name='stage3_unit16_bn2', data=res4b15_branch2b, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b15_branch2b = bn4b15_branch2b
        res4b15_branch2b_relu = mx.symbol.Activation(name='stage3_unit16_relu2', data=scale4b15_branch2b,
                                                     act_type='relu')
        res4b15_branch2c = mx.symbol.Convolution(name='stage3_unit16_conv3', data=res4b15_branch2b_relu, num_filter=1024,
                                                 pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b15_branch2c = mx.symbol.BatchNorm(name='stage3_unit16_bn3', data=res4b15_branch2c, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b15_branch2c = bn4b15_branch2c

        # concatenate
        res4b15 = mx.symbol.broadcast_add(name='res4b15', *[res4b14_relu, scale4b15_branch2c])
        res4b15_relu = mx.symbol.Activation(name='stage3_unit16_relu', data=res4b15, act_type='relu')

        # res4b16 unit17
        # branch 2
        res4b16_branch2a = mx.symbol.Convolution(name='stage3_unit17_conv1', data=res4b15_relu, num_filter=512, pad=(0, 0),
                                                 kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b16_branch2a = mx.symbol.BatchNorm(name='stage3_unit17_bn1', data=res4b16_branch2a, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b16_branch2a = bn4b16_branch2a
        res4b16_branch2a_relu = mx.symbol.Activation(name='stage3_unit17_relu1', data=scale4b16_branch2a,
                                                     act_type='relu')
        res4b16_branch2b = mx.symbol.Convolution(name='stage3_unit17_conv2', data=res4b16_branch2a_relu, num_filter=512,
                                                 num_group=num_group,
                                                 pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b16_branch2b = mx.symbol.BatchNorm(name='stage3_unit17_bn2', data=res4b16_branch2b, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b16_branch2b = bn4b16_branch2b
        res4b16_branch2b_relu = mx.symbol.Activation(name='stage3_unit17_relu2', data=scale4b16_branch2b,
                                                     act_type='relu')
        res4b16_branch2c = mx.symbol.Convolution(name='stage3_unit17_conv3', data=res4b16_branch2b_relu, num_filter=1024,
                                                 pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b16_branch2c = mx.symbol.BatchNorm(name='stage3_unit17_bn3', data=res4b16_branch2c, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b16_branch2c = bn4b16_branch2c

        # concatenate
        res4b16 = mx.symbol.broadcast_add(name='res4b16', *[res4b15_relu, scale4b16_branch2c])
        res4b16_relu = mx.symbol.Activation(name='stage3_unit17_relu', data=res4b16, act_type='relu')

        # res4b unit18
        # branch 2
        res4b17_branch2a = mx.symbol.Convolution(name='stage3_unit18_conv1', data=res4b16_relu, num_filter=512, pad=(0, 0),
                                                 kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b17_branch2a = mx.symbol.BatchNorm(name='stage3_unit18_bn1', data=res4b17_branch2a, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b17_branch2a = bn4b17_branch2a
        res4b17_branch2a_relu = mx.symbol.Activation(name='stage3_unit18_relu1', data=scale4b17_branch2a,
                                                     act_type='relu')
        res4b17_branch2b = mx.symbol.Convolution(name='stage3_unit18_conv2', data=res4b17_branch2a_relu, num_filter=512,
                                                 num_group=num_group,
                                                 pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b17_branch2b = mx.symbol.BatchNorm(name='stage3_unit18_bn2', data=res4b17_branch2b, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b17_branch2b = bn4b17_branch2b
        res4b17_branch2b_relu = mx.symbol.Activation(name='stage3_unit18_relu2', data=scale4b17_branch2b,
                                                     act_type='relu')
        res4b17_branch2c = mx.symbol.Convolution(name='stage3_unit18_conv3', data=res4b17_branch2b_relu, num_filter=1024,
                                                 pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b17_branch2c = mx.symbol.BatchNorm(name='stage3_unit18_bn3', data=res4b17_branch2c, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b17_branch2c = bn4b17_branch2c

        # concatenate
        res4b17 = mx.symbol.broadcast_add(name='res4b17', *[res4b16_relu, scale4b17_branch2c])
        res4b17_relu = mx.symbol.Activation(name='stage3_unit18_relu', data=res4b17, act_type='relu')

        # res4b18 unit19
        # branch 2
        res4b18_branch2a = mx.symbol.Convolution(name='stage3_unit19_conv1', data=res4b17_relu, num_filter=512, pad=(0, 0),
                                                 kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b18_branch2a = mx.symbol.BatchNorm(name='stage3_unit19_bn1', data=res4b18_branch2a, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b18_branch2a = bn4b18_branch2a
        res4b18_branch2a_relu = mx.symbol.Activation(name='stage3_unit19_relu1', data=scale4b18_branch2a,
                                                     act_type='relu')
        res4b18_branch2b = mx.symbol.Convolution(name='stage3_unit19_conv2', data=res4b18_branch2a_relu, num_filter=512,
                                                 num_group=num_group,
                                                 pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b18_branch2b = mx.symbol.BatchNorm(name='stage3_unit19_bn2', data=res4b18_branch2b, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b18_branch2b = bn4b18_branch2b
        res4b18_branch2b_relu = mx.symbol.Activation(name='stage3_unit19_relu2', data=scale4b18_branch2b,
                                                     act_type='relu')
        res4b18_branch2c = mx.symbol.Convolution(name='stage3_unit19_conv3', data=res4b18_branch2b_relu, num_filter=1024,
                                                 pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b18_branch2c = mx.symbol.BatchNorm(name='stage3_unit19_bn3', data=res4b18_branch2c, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b18_branch2c = bn4b18_branch2c

        # concatenate
        res4b18 = mx.symbol.broadcast_add(name='res4b18', *[res4b17_relu, scale4b18_branch2c])
        res4b18_relu = mx.symbol.Activation(name='stage3_unit19_relu', data=res4b18, act_type='relu')

        # res4b19 unit20
        # branch 2
        res4b19_branch2a = mx.symbol.Convolution(name='stage3_unit20_conv1', data=res4b18_relu, num_filter=512, pad=(0, 0),
                                                 kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b19_branch2a = mx.symbol.BatchNorm(name='stage3_unit20_bn1', data=res4b19_branch2a, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b19_branch2a = bn4b19_branch2a
        res4b19_branch2a_relu = mx.symbol.Activation(name='stage3_unit20_relu1', data=scale4b19_branch2a,
                                                     act_type='relu')
        res4b19_branch2b = mx.symbol.Convolution(name='stage3_unit20_conv2', data=res4b19_branch2a_relu, num_filter=512,
                                                 num_group=num_group,
                                                 pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b19_branch2b = mx.symbol.BatchNorm(name='stage3_unit20_bn2', data=res4b19_branch2b, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b19_branch2b = bn4b19_branch2b
        res4b19_branch2b_relu = mx.symbol.Activation(name='stage3_unit20_relu2', data=scale4b19_branch2b,
                                                     act_type='relu')
        res4b19_branch2c = mx.symbol.Convolution(name='stage3_unit20_conv3', data=res4b19_branch2b_relu, num_filter=1024,
                                                 pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b19_branch2c = mx.symbol.BatchNorm(name='stage3_unit20_bn3', data=res4b19_branch2c, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b19_branch2c = bn4b19_branch2c

        # concatenate
        res4b19 = mx.symbol.broadcast_add(name='res4b19', *[res4b18_relu, scale4b19_branch2c])
        res4b19_relu = mx.symbol.Activation(name='stage3_unit20_relu', data=res4b19, act_type='relu')

        # res4b20 unit21
        # branch 2
        res4b20_branch2a = mx.symbol.Convolution(name='stage3_unit21_conv1', data=res4b19_relu, num_filter=512, pad=(0, 0),
                                                 kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b20_branch2a = mx.symbol.BatchNorm(name='stage3_unit21_bn1', data=res4b20_branch2a, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b20_branch2a = bn4b20_branch2a
        res4b20_branch2a_relu = mx.symbol.Activation(name='stage3_unit21_relu1', data=scale4b20_branch2a,
                                                     act_type='relu')
        res4b20_branch2b = mx.symbol.Convolution(name='stage3_unit21_conv2', data=res4b20_branch2a_relu, num_filter=512,
                                                 num_group=num_group,
                                                 pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b20_branch2b = mx.symbol.BatchNorm(name='stage3_unit21_bn2', data=res4b20_branch2b, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b20_branch2b = bn4b20_branch2b
        res4b20_branch2b_relu = mx.symbol.Activation(name='stage3_unit21_relu2', data=scale4b20_branch2b,
                                                     act_type='relu')
        res4b20_branch2c = mx.symbol.Convolution(name='stage3_unit21_conv3', data=res4b20_branch2b_relu, num_filter=1024,
                                                 pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b20_branch2c = mx.symbol.BatchNorm(name='stage3_unit21_bn3', data=res4b20_branch2c, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b20_branch2c = bn4b20_branch2c

        # concatenate
        res4b20 = mx.symbol.broadcast_add(name='res4b20', *[res4b19_relu, scale4b20_branch2c])
        res4b20_relu = mx.symbol.Activation(name='stage3_unit21_relu', data=res4b20, act_type='relu')

        # res4b21 unit22
        # branch 2
        res4b21_branch2a = mx.symbol.Convolution(name='stage3_unit22_conv1', data=res4b20_relu, num_filter=512, pad=(0, 0),
                                                 kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b21_branch2a = mx.symbol.BatchNorm(name='stage3_unit22_bn1', data=res4b21_branch2a, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b21_branch2a = bn4b21_branch2a
        res4b21_branch2a_relu = mx.symbol.Activation(name='stage3_unit22_relu1', data=scale4b21_branch2a,
                                                     act_type='relu')
        res4b21_branch2b = mx.symbol.Convolution(name='stage3_unit22_conv2', data=res4b21_branch2a_relu, num_filter=512,
                                                 num_group=num_group,
                                                 pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b21_branch2b = mx.symbol.BatchNorm(name='stage3_unit22_bn2', data=res4b21_branch2b, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b21_branch2b = bn4b21_branch2b
        res4b21_branch2b_relu = mx.symbol.Activation(name='stage3_unit22_relu2', data=scale4b21_branch2b,
                                                     act_type='relu')
        res4b21_branch2c = mx.symbol.Convolution(name='stage3_unit22_conv3', data=res4b21_branch2b_relu, num_filter=1024,
                                                 pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b21_branch2c = mx.symbol.BatchNorm(name='stage3_unit22_bn3', data=res4b21_branch2c, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b21_branch2c = bn4b21_branch2c

        # concatenate
        res4b21 = mx.symbol.broadcast_add(name='res4b21', *[res4b20_relu, scale4b21_branch2c])
        res4b21_relu = mx.symbol.Activation(name='stage3_unit22_relu', data=res4b21, act_type='relu')

        # res4b22 unit23
        # branch 2
        res4b22_branch2a = mx.symbol.Convolution(name='stage3_unit23_conv1', data=res4b21_relu, num_filter=512, pad=(0, 0),
                                                 kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b22_branch2a = mx.symbol.BatchNorm(name='stage3_unit23_bn1', data=res4b22_branch2a, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b22_branch2a = bn4b22_branch2a
        res4b22_branch2a_relu = mx.symbol.Activation(name='stage3_unit23_relu1', data=scale4b22_branch2a,
                                                     act_type='relu')
        res4b22_branch2b = mx.symbol.Convolution(name='stage3_unit23_conv2', data=res4b22_branch2a_relu, num_filter=512,
                                                 num_group=num_group,
                                                 pad=(1, 1), kernel=(3, 3), stride=(1, 1), no_bias=True)
        bn4b22_branch2b = mx.symbol.BatchNorm(name='stage3_unit23_bn2', data=res4b22_branch2b, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b22_branch2b = bn4b22_branch2b
        res4b22_branch2b_relu = mx.symbol.Activation(name='stage3_unit23_relu2', data=scale4b22_branch2b,
                                                     act_type='relu')
        res4b22_branch2c = mx.symbol.Convolution(name='stage3_unit23_conv3', data=res4b22_branch2b_relu, num_filter=1024,
                                                 pad=(0, 0), kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn4b22_branch2c = mx.symbol.BatchNorm(name='stage3_unit23_bn3', data=res4b22_branch2c, use_global_stats=True,
                                              fix_gamma=False, eps=self.eps)
        scale4b22_branch2c = bn4b22_branch2c
        # concatenate
        res4b22 = mx.symbol.broadcast_add(name='res4b22', *[res4b21_relu, scale4b22_branch2c])
        res4b22_relu = mx.symbol.Activation(name='stage3_unit23_relu', data=res4b22, act_type='relu')

        if is_train:
            return res4b22_relu
        else:
            return res4b22_relu, res3b3_relu, res2c_relu

    def get_resnext_conv5(self, conv_feat, num_group=32):

        # res5a stage4 unit1
        # branch 1
        res5a_branch1 = mx.symbol.Convolution(name='stage4_unit1_sc', data=conv_feat, num_filter=2048, pad=(0, 0),
                                              kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn5a_branch1 = mx.symbol.BatchNorm(name='stage4_unit1_sc_bn', data=res5a_branch1, use_global_stats=True, fix_gamma=False, eps=self.eps)
        scale5a_branch1 = bn5a_branch1

        # branch 2
        res5a_branch2a = mx.symbol.Convolution(name='stage4_unit1_conv1', data=conv_feat, num_filter=1024, pad=(0, 0),
                                               kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn5a_branch2a = mx.symbol.BatchNorm(name='stage4_unit1_bn1', data=res5a_branch2a, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale5a_branch2a = bn5a_branch2a
        res5a_branch2a_relu = mx.symbol.Activation(name='stage4_unit1_relu1', data=scale5a_branch2a, act_type='relu')
        res5a_branch2b = mx.symbol.Convolution(name='stage4_unit1_conv2', data=res5a_branch2a_relu, num_filter=1024, pad=(2, 2),
                                               num_group=num_group,
                                               kernel=(3, 3), stride=(1, 1), dilate=(2, 2), no_bias=True)
        bn5a_branch2b = mx.symbol.BatchNorm(name='stage4_unit1_bn2', data=res5a_branch2b, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale5a_branch2b = bn5a_branch2b
        res5a_branch2b_relu = mx.symbol.Activation(name='stage4_unit1_relu2', data=scale5a_branch2b, act_type='relu')
        res5a_branch2c = mx.symbol.Convolution(name='stage4_unit1_conv3', data=res5a_branch2b_relu, num_filter=2048, pad=(0, 0),
                                               kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn5a_branch2c = mx.symbol.BatchNorm(name='stage4_unit1_bn3', data=res5a_branch2c, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale5a_branch2c = bn5a_branch2c

        # concatenate
        res5a = mx.symbol.broadcast_add(name='res5a', *[scale5a_branch1, scale5a_branch2c])
        res5a_relu = mx.symbol.Activation(name='stage4_unit1_relu', data=res5a, act_type='relu')

        # res5b unit2
        # branch 2
        res5b_branch2a = mx.symbol.Convolution(name='stage4_unit2_conv1', data=res5a_relu, num_filter=1024, pad=(0, 0),
                                               kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn5b_branch2a = mx.symbol.BatchNorm(name='stage4_unit2_bn1', data=res5b_branch2a, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale5b_branch2a = bn5b_branch2a
        res5b_branch2a_relu = mx.symbol.Activation(name='stage4_unit2_relu1', data=scale5b_branch2a, act_type='relu')
        res5b_branch2b = mx.symbol.Convolution(name='stage4_unit2_conv2', data=res5b_branch2a_relu, num_filter=1024, pad=(2, 2),
                                               num_group=num_group,
                                               kernel=(3, 3), stride=(1, 1), dilate=(2, 2), no_bias=True)
        bn5b_branch2b = mx.symbol.BatchNorm(name='stage4_unit2_bn2', data=res5b_branch2b, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale5b_branch2b = bn5b_branch2b
        res5b_branch2b_relu = mx.symbol.Activation(name='stage4_unit2_relu2', data=scale5b_branch2b, act_type='relu')
        res5b_branch2c = mx.symbol.Convolution(name='stage4_unit2_conv3', data=res5b_branch2b_relu, num_filter=2048, pad=(0, 0),
                                               kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn5b_branch2c = mx.symbol.BatchNorm(name='stage4_unit2_bn3', data=res5b_branch2c, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale5b_branch2c = bn5b_branch2c

        # concatenate
        res5b = mx.symbol.broadcast_add(name='res5b', *[res5a_relu, scale5b_branch2c])
        res5b_relu = mx.symbol.Activation(name='stage4_unit2_relu', data=res5b, act_type='relu')

        # res5c unit3
        # branch 2
        res5c_branch2a = mx.symbol.Convolution(name='stage4_unit3_conv1', data=res5b_relu, num_filter=1024, pad=(0, 0),
                                               kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn5c_branch2a = mx.symbol.BatchNorm(name='stage4_unit3_bn1', data=res5c_branch2a, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale5c_branch2a = bn5c_branch2a
        res5c_branch2a_relu = mx.symbol.Activation(name='stage4_unit3_relu1', data=scale5c_branch2a, act_type='relu')
        res5c_branch2b = mx.symbol.Convolution(name='stage4_unit3_conv2', data=res5c_branch2a_relu, num_filter=1024, pad=(2, 2),
                                               num_group=num_group,
                                               kernel=(3, 3), stride=(1, 1), dilate=(2, 2), no_bias=True)
        bn5c_branch2b = mx.symbol.BatchNorm(name='stage4_unit3_bn2', data=res5c_branch2b, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale5c_branch2b = bn5c_branch2b
        res5c_branch2b_relu = mx.symbol.Activation(name='stage4_unit3_relu2', data=scale5c_branch2b, act_type='relu')
        res5c_branch2c = mx.symbol.Convolution(name='stage4_unit3_conv3', data=res5c_branch2b_relu, num_filter=2048, pad=(0, 0),
                                               kernel=(1, 1), stride=(1, 1), no_bias=True)
        bn5c_branch2c = mx.symbol.BatchNorm(name='stage4_unit3_bn3', data=res5c_branch2c, use_global_stats=True,
                                            fix_gamma=False, eps=self.eps)
        scale5c_branch2c = bn5c_branch2c

        # concatenate
        res5c = mx.symbol.broadcast_add(name='res5c', *[res5b_relu, scale5c_branch2c])
        res5c_relu = mx.symbol.Activation(name='stage4_unit3_relu', data=res5c, act_type='relu')
        return res5c_relu

    def get_rpn(self, conv_feat, num_anchors):
        rpn_conv = mx.sym.Convolution(data=conv_feat, kernel=(3, 3), pad=(1, 1), num_filter=512, name="rpn_conv_3x3")

        rpn_relu = mx.sym.Activation(data=rpn_conv, act_type="relu", name="rpn_relu")

        rpn_cls_score = mx.sym.Convolution(data=rpn_relu, kernel=(1, 1), pad=(0, 0),
                                           num_filter=2 * num_anchors, name="rpn_cls_score")

        rpn_bbox_pred = mx.sym.Convolution(data=rpn_relu, kernel=(1, 1), pad=(0, 0),
                                           num_filter=4 * num_anchors, name="rpn_bbox_pred")
        return rpn_cls_score, rpn_bbox_pred

    def get_symbol(self, cfg, is_train=True):

        # config alias for convenient
        num_classes = cfg.dataset.NUM_CLASSES  # including background (80 + 1)
        num_reg_classes = (2 if cfg.CLASS_AGNOSTIC else num_classes)
        num_anchors = cfg.network.NUM_ANCHORS

        # input init
        if is_train:
            data = mx.sym.Variable(name='data')
            im_info = mx.sym.Variable(name='im_info')
            gt_boxes = mx.sym.Variable(name='gt_boxes')
            gt_masks = mx.sym.Variable(name='gt_masks')
            rpn_label = mx.sym.Variable(name='proposal_label')
            rpn_bbox_target = mx.sym.Variable(name='proposal_bbox_target')
            rpn_bbox_weight = mx.sym.Variable(name='proposal_bbox_weight')
        else:
            data = mx.sym.Variable(name="data")
            im_info = mx.sym.Variable(name="im_info")

        # conv4: shared convolutional layers
        if is_train:
            conv_feat = self.get_resnext_conv4(data, is_train)
        else:
            conv_feat, res3b3_relu, res2c_relu = self.get_resnext_conv4(data, is_train)

        # conv5: branch of position-sensitive inside/outside score maps
        relu1 = self.get_resnext_conv5(conv_feat)

        # rpn: branch of region proposal network
        rpn_cls_score, rpn_bbox_pred = self.get_rpn(conv_feat, num_anchors)
        # RPN network has two output: objectiveness score, bbox regression

        if is_train:
            # prepare rpn data
            rpn_cls_score_reshape = mx.sym.Reshape(
                data=rpn_cls_score, shape=(0, 2, -1, 0),
                name="rpn_cls_score_reshape")

            rpn_cls_act = mx.sym.SoftmaxActivation(
                data=rpn_cls_score_reshape, mode="channel",
                name="rpn_cls_act")

            rpn_cls_act_reshape = mx.sym.Reshape(
                data=rpn_cls_act, shape=(0, 2 * num_anchors, -1, 0),
                name='rpn_cls_act_reshape')

            # classification loss
            rpn_cls_prob = mx.sym.SoftmaxOutput(
                data=rpn_cls_score_reshape, label=rpn_label, multi_output=True,
                normalization='valid', use_ignore=True, ignore_label=-1,
                name="rpn_cls_prob")

            # bounding box regression loss
            rpn_bbox_loss_ = rpn_bbox_weight * mx.sym.smooth_l1(name='rpn_bbox_loss_', scalar=3.0, data=(rpn_bbox_pred - rpn_bbox_target))
            rpn_bbox_loss = mx.sym.MakeLoss(name='rpn_bbox_loss', data=rpn_bbox_loss_, grad_scale=1.0 / cfg.TRAIN.RPN_BATCH_SIZE)

            if cfg.TRAIN.CXX_PROPOSAL:
                rois = mx.contrib.sym.Proposal(
                    cls_prob=rpn_cls_act_reshape, bbox_pred=rpn_bbox_pred, im_info=im_info, name='rois',
                    feature_stride=cfg.network.RPN_FEAT_STRIDE, scales=tuple(cfg.network.ANCHOR_SCALES), ratios=tuple(cfg.network.ANCHOR_RATIOS),
                    rpn_pre_nms_top_n=cfg.TRAIN.RPN_PRE_NMS_TOP_N, rpn_post_nms_top_n=cfg.TRAIN.RPN_POST_NMS_TOP_N,
                    threshold=cfg.TRAIN.RPN_NMS_THRESH, rpn_min_size=cfg.TRAIN.RPN_MIN_SIZE)
            else:
                rois = mx.sym.Custom(
                    cls_prob=rpn_cls_act_reshape, bbox_pred=rpn_bbox_pred, im_info=im_info, name='rois',
                    op_type='proposal', feat_stride=cfg.network.RPN_FEAT_STRIDE,
                    scales=tuple(cfg.network.ANCHOR_SCALES), ratios=tuple(cfg.network.ANCHOR_RATIOS),
                    rpn_pre_nms_top_n=cfg.TRAIN.RPN_PRE_NMS_TOP_N, rpn_post_nms_top_n=cfg.TRAIN.RPN_POST_NMS_TOP_N,
                    nms_threshold=cfg.TRAIN.RPN_NMS_THRESH, rpn_min_size=cfg.TRAIN.RPN_MIN_SIZE)
            # ROI proposal target
            gt_boxes_reshape = mx.sym.Reshape(data=gt_boxes, shape=(-1, 5), name='gt_boxes_reshape')
            group = mx.sym.Custom(rois=rois, gt_boxes=gt_boxes_reshape, gt_masks=gt_masks,
                                  op_type='proposal_annotator',
                                  num_classes=num_reg_classes, mask_size=cfg.MASK_SIZE, binary_thresh=cfg.TRAIN.BINARY_THRESH,
                                  batch_images=cfg.TRAIN.BATCH_IMAGES, cfg=cPickle.dumps(cfg),
                                  batch_rois=cfg.TRAIN.BATCH_ROIS, fg_fraction=cfg.TRAIN.FG_FRACTION)
            rois = group[0]
            label = group[1]
            bbox_target = group[2]
            bbox_weight = group[3]
            mask_reg_targets = group[4]
        else:
            # ROI Proposal
            rpn_cls_score_reshape = mx.sym.Reshape(
                data=rpn_cls_score, shape=(0, 2, -1, 0),
                name="rpn_cls_score_reshape")

            rpn_cls_prob = mx.sym.SoftmaxActivation(
                data=rpn_cls_score_reshape, mode="channel",
                name="rpn_cls_prob")

            rpn_cls_prob_reshape = mx.sym.Reshape(
                data=rpn_cls_prob, shape=(0, 2 * num_anchors, -1, 0),
                name='rpn_cls_prob_reshape')

            # project rois to 16x smaller feature maps.
            if cfg.TEST.CXX_PROPOSAL:
                rois = mx.contrib.sym.Proposal(
                    cls_prob=rpn_cls_prob_reshape, bbox_pred=rpn_bbox_pred, im_info=im_info, name='rois',
                    feature_stride=cfg.network.RPN_FEAT_STRIDE, scales=tuple(cfg.network.ANCHOR_SCALES), ratios=tuple(cfg.network.ANCHOR_RATIOS),
                    rpn_pre_nms_top_n=cfg.TEST.RPN_PRE_NMS_TOP_N, rpn_post_nms_top_n=cfg.TEST.RPN_POST_NMS_TOP_N,
                    threshold=cfg.TEST.RPN_NMS_THRESH, rpn_min_size=cfg.TEST.RPN_MIN_SIZE)
            else:
                rois = mx.sym.Custom(
                    cls_prob=rpn_cls_prob_reshape, bbox_pred=rpn_bbox_pred, im_info=im_info, name='rois',
                    op_type='proposal', feat_stride=cfg.network.RPN_FEAT_STRIDE,
                    scales=tuple(cfg.network.ANCHOR_SCALES), ratios=tuple(cfg.network.ANCHOR_RATIOS),
                    rpn_pre_nms_top_n=cfg.TEST.RPN_PRE_NMS_TOP_N, rpn_post_nms_top_n=cfg.TEST.RPN_POST_NMS_TOP_N,
                    nms_threshold=cfg.TEST.RPN_NMS_THRESH, rpn_min_size=cfg.TEST.RPN_MIN_SIZE)

        # conv new 1
        if cfg.TRAIN.CONVNEW3: # reduce the dimension from 2048 to 1024
            conv_new_1 = mx.sym.Convolution(data=relu1, kernel=(1, 1), num_filter=1024, name='conv_new_1',
                                            attr={'lr_mult':'3.00'})
        else:
            conv_new_1 = mx.sym.Convolution(data=relu1, kernel=(1, 1), num_filter=1024, name='conv_new_1')

        relu_new_1 = mx.sym.Activation(data=conv_new_1, act_type='relu', name='relu_new_1')


        fcis_cls_seg = mx.sym.Convolution(data=relu_new_1, kernel=(1, 1), num_filter=7*7*num_classes*2,
                                          name='fcis_cls_seg') # 2 x K^2 x (C + 1) score maps #

        fcis_bbox = mx.sym.Convolution(data=relu_new_1, kernel=(1, 1), num_filter=7*7*4*num_reg_classes,
                                       name='fcis_bbox') # 4 x K^2 score maps #

        psroipool_cls_seg = mx.contrib.sym.PSROIPooling(name='psroipool_cls_seg', data=fcis_cls_seg, rois=rois,
                                                        group_size=7, pooled_size=21, output_dim=num_classes*2, spatial_scale=0.0625)

        psroipool_bbox_pred = mx.contrib.sym.PSROIPooling(name='psroipool_bbox', data=fcis_bbox, rois=rois,
                                                          group_size=7, pooled_size=21,  output_dim=num_reg_classes*4, spatial_scale=0.0625)
        if is_train:
            # classification path
            psroipool_cls = mx.contrib.sym.ChannelOperator(name='psroipool_cls', data=psroipool_cls_seg, group=num_classes, op_type='Group_Max')
            cls_score = mx.sym.Pooling(name='cls_score', data=psroipool_cls, pool_type='avg', global_pool=True, kernel=(21, 21))
            cls_score = mx.sym.Reshape(name='cls_score_reshape', data=cls_score, shape=(-1, num_classes))

            # mask regression path
            label_seg = mx.sym.Reshape(name='label_seg', data=label, shape=(-1, 1, 1, 1))
            seg_pred = mx.contrib.sym.ChannelOperator(name='seg_pred', data=psroipool_cls_seg, pick_idx=label_seg, group=num_classes, op_type='Group_Pick', pick_type='Label_Pick')

            # bbox regression path
            bbox_pred = mx.sym.Pooling(name='bbox_pred', data=psroipool_bbox_pred, pool_type='avg', global_pool=True, kernel=(21, 21))
            bbox_pred = mx.sym.Reshape(name='bbox_pred_reshape', data=bbox_pred, shape=(-1, 4 * num_reg_classes))
        else:
            # classification path
            # (1) max to differentiate detection+ and detection-
            psroipool_cls = mx.contrib.sym.ChannelOperator(name='psroipool_cls', data=psroipool_cls_seg, group=num_classes, op_type='Group_Max')
            # (2) detection score is obtained by average pooling
            cls_score = mx.sym.Pooling(name='cls_score', data=psroipool_cls, pool_type='avg', global_pool=True, kernel=(21, 21))
            cls_score = mx.sym.Reshape(name='cls_score_reshape', data=cls_score, shape=(-1, num_classes))
            # (3) softmax across all the categories
            cls_prob = mx.sym.SoftmaxActivation(name='cls_prob', data=cls_score)

            # mask regression path
            # (1) softmax to differentiate segmentation+ and segmentation-
            score_seg = mx.sym.Reshape(name='score_seg', data=cls_prob, shape=(-1, num_classes, 1, 1))
            seg_softmax = mx.contrib.sym.ChannelOperator(name='seg_softmax', data=psroipool_cls_seg, group=num_classes, op_type='Group_Softmax')
            # (2) mask is the union of the per-pixel segmentation score for each category
            seg_pred = mx.contrib.sym.ChannelOperator(name='seg_pred', data=seg_softmax, pick_idx=score_seg, group=num_classes, op_type='Group_Pick', pick_type='Score_Pick')

            # bbox regression path
            bbox_pred = mx.sym.Pooling(name='bbox_pred', data=psroipool_bbox_pred, pool_type='avg', global_pool=True, kernel=(21, 21))
            bbox_pred = mx.sym.Reshape(name='bbox_pred_reshape', data=bbox_pred, shape=(-1, 4 * num_reg_classes))

        if is_train:
            if cfg.TRAIN.ENABLE_OHEM:
                labels_ohem, mask_targets_ohem, bbox_weights_ohem = mx.sym.Custom(op_type='BoxAnnotatorOHEM',
                                                                                  num_classes=num_classes,
                                                                                  num_reg_classes=num_reg_classes,
                                                                                  roi_per_img=cfg.TRAIN.BATCH_ROIS_OHEM,
                                                                                  cfg=cPickle.dumps(cfg),
                                                                                  cls_score=cls_score,
                                                                                  seg_pred=seg_pred,
                                                                                  bbox_pred=bbox_pred, labels=label,
                                                                                  mask_targets=mask_reg_targets,
                                                                                  bbox_targets=bbox_target,
                                                                                  bbox_weights=bbox_weight)

                cls_prob = mx.sym.SoftmaxOutput(name='cls_prob', data=cls_score, label=labels_ohem,
                                                normalization='valid',
                                                use_ignore=True, ignore_label=-1,
                                                grad_scale=cfg.TRAIN.LOSS_WEIGHT[0])


                seg_prob = mx.sym.SoftmaxOutput(name='seg_prob', data=seg_pred, label=mask_targets_ohem,
                                                multi_output=True,
                                                normalization='null', use_ignore=True, ignore_label=-1,
                                                grad_scale=cfg.TRAIN.LOSS_WEIGHT[1] / cfg.TRAIN.BATCH_ROIS_OHEM)

                bbox_loss_t = bbox_weights_ohem * mx.sym.smooth_l1(name='bbox_loss_t', scalar=1.0,
                                                                   data=(bbox_pred - bbox_target))
                bbox_loss = mx.sym.MakeLoss(name='bbox_loss', data=bbox_loss_t,
                                            grad_scale=cfg.TRAIN.LOSS_WEIGHT[2] / cfg.TRAIN.BATCH_ROIS_OHEM)
                rcnn_label = labels_ohem
            else:

                cls_prob = mx.sym.SoftmaxOutput(name='cls_prob', data=cls_score, label=label, normalization='valid',
                                                use_ignore=True, ignore_label=-1, grad_scale=cfg.TRAIN.LOSS_WEIGHT[0])


                seg_prob = mx.sym.SoftmaxOutput(name='seg_prob', data=seg_pred, label=mask_reg_targets, multi_output=True,
                                                normalization='null', use_ignore=True, ignore_label=-1,
                                                grad_scale=cfg.TRAIN.LOSS_WEIGHT[1] / cfg.TRAIN.BATCH_ROIS)

                bbox_loss_t = bbox_weight * mx.sym.smooth_l1(name='bbox_loss_t', scalar=1.0, data=(bbox_pred - bbox_target))
                bbox_loss = mx.sym.MakeLoss(name='bbox_loss', data=bbox_loss_t, grad_scale=cfg.TRAIN.LOSS_WEIGHT[2] / cfg.TRAIN.BATCH_ROIS)
                rcnn_label = label

            rcnn_label = mx.sym.Reshape(data=rcnn_label, shape=(cfg.TRAIN.BATCH_IMAGES, -1), name='label_reshape')
            cls_prob = mx.sym.Reshape(data=cls_prob, shape=(cfg.TRAIN.BATCH_IMAGES, -1, num_classes),
                                      name='cls_prob_reshape')
            bbox_loss = mx.sym.Reshape(data=bbox_loss, shape=(cfg.TRAIN.BATCH_IMAGES, -1, 4 * num_reg_classes),
                                       name='bbox_loss_reshape')
            group = mx.sym.Group([rpn_cls_prob, rpn_bbox_loss, cls_prob, bbox_loss, seg_prob, mx.sym.BlockGrad(mask_reg_targets), mx.sym.BlockGrad(rcnn_label)])
        else:
            cls_prob = mx.sym.SoftmaxActivation(name='cls_prob', data=cls_score)

            if cfg.TEST.ITER == 2:
                rois_iter2 = mx.sym.Custom(bottom_rois=rois, bbox_delta=bbox_pred, im_info=im_info, cls_prob=cls_prob,
                                           name='rois_iter2', b_clip_boxes=True, bbox_class_agnostic=True,
                                           bbox_means=tuple(cfg.TRAIN.BBOX_MEANS), bbox_stds=tuple(cfg.TRAIN.BBOX_STDS), op_type='BoxParser')
                # rois = mx.sym.Concat(*[rois, rois_iter2], dim=0, name='rois')
                psroipool_cls_seg_iter2 = mx.contrib.sym.PSROIPooling(name='psroipool_cls_seg', data=fcis_cls_seg, rois=rois_iter2,
                                                              group_size=7, pooled_size=21,
                                                              output_dim=num_classes*2, spatial_scale=0.0625)
                psroipool_bbox_pred_iter2 = mx.contrib.sym.PSROIPooling(name='psroipool_bbox', data=fcis_bbox, rois=rois_iter2,
                                                                group_size=7, pooled_size=21,
                                                                output_dim=num_reg_classes*4, spatial_scale=0.0625)

                # classification path
                psroipool_cls_iter2 = mx.contrib.sym.ChannelOperator(name='psroipool_cls', data=psroipool_cls_seg_iter2, group=num_classes, op_type='Group_Max')
                cls_score_iter2 = mx.sym.Pooling(name='cls_score', data=psroipool_cls_iter2, pool_type='avg', global_pool=True, kernel=(21, 21), stride=(21,21))
                cls_score_iter2 = mx.sym.Reshape(name='cls_score_reshape', data=cls_score_iter2, shape=(-1, num_classes))
                cls_prob_iter2 = mx.sym.SoftmaxActivation(name='cls_prob', data=cls_score_iter2)

                # mask regression path
                score_seg_iter2 = mx.sym.Reshape(name='score_seg', data=cls_prob_iter2, shape=(-1, num_classes, 1, 1))
                seg_softmax_iter2 = mx.contrib.sym.ChannelOperator(name='seg_softmax', data=psroipool_cls_seg_iter2, group=num_classes, op_type='Group_Softmax')
                seg_pred_iter2 = mx.contrib.sym.ChannelOperator(name='seg_pred', data=seg_softmax_iter2, pick_idx=score_seg_iter2, group=num_classes, op_type='Group_Pick', pick_type='Score_Pick')

                # bbox regression path
                bbox_pred_iter2 = mx.sym.Pooling(name='bbox_pred', data=psroipool_bbox_pred_iter2, pool_type='avg', global_pool=True, kernel=(21, 21), stride=(21,21))
                bbox_pred_iter2 = mx.sym.Reshape(name='bbox_pred_reshape', data=bbox_pred_iter2, shape=(-1, 4 * num_reg_classes))

                rois      = mx.sym.Concat(*[rois, rois_iter2], dim=0, name='rois')
                cls_prob  = mx.sym.Concat(*[cls_prob, cls_prob_iter2], dim=0, name='cls_prob')
                seg_pred  = mx.sym.Concat(*[seg_pred, seg_pred_iter2], dim=0, name='seg_pred')
                bbox_pred = mx.sym.Concat(*[bbox_pred, bbox_pred_iter2], dim=0, name='box_pred')

            # reshape output
            cls_prob = mx.sym.Reshape(data=cls_prob, shape=(cfg.TEST.BATCH_IMAGES, -1, num_classes), name='cls_prob_reshape')
            bbox_pred = mx.sym.Reshape(data=bbox_pred, shape=(cfg.TEST.BATCH_IMAGES, -1, 4 * num_reg_classes), name='bbox_pred_reshape')

            """"""
            # group = mx.sym.Group([rois, cls_prob, bbox_pred, seg_pred])
            lst = [rois, cls_prob, bbox_pred, seg_pred]
            for i in range(len(cfg.feature)):
                if cfg.feature[i] == 2:
                    lst.append(res2c_relu)
                elif cfg.feature[i] == 3:
                    lst.append(res3b3_relu)
                elif cfg.feature[i] == 4:
                    lst.append(conv_feat)
                elif cfg.feature[i] == 5:
                    lst.append(relu1)
                elif cfg.feature[i] == 6:
                    lst.append(relu_new_1)
            group = mx.sym.Group(lst)
            """"""

        self.sym = group
        return group

    def init_weight(self, cfg, arg_params, aux_params):
        arg_params['rpn_conv_3x3_weight'] = mx.random.normal(0, 0.01, shape=self.arg_shape_dict['rpn_conv_3x3_weight'])
        arg_params['rpn_conv_3x3_bias'] = mx.nd.zeros(shape=self.arg_shape_dict['rpn_conv_3x3_bias'])
        arg_params['rpn_cls_score_weight'] = mx.random.normal(0, 0.01, shape=self.arg_shape_dict['rpn_cls_score_weight'])
        arg_params['rpn_cls_score_bias'] = mx.nd.zeros(shape=self.arg_shape_dict['rpn_cls_score_bias'])
        arg_params['rpn_bbox_pred_weight'] = mx.random.normal(0, 0.01, shape=self.arg_shape_dict['rpn_bbox_pred_weight'])
        arg_params['rpn_bbox_pred_bias'] = mx.nd.zeros(shape=self.arg_shape_dict['rpn_bbox_pred_bias'])
        arg_params['conv_new_1_weight'] = mx.random.normal(0, 0.01, shape=self.arg_shape_dict['conv_new_1_weight'])
        arg_params['conv_new_1_bias'] = mx.nd.zeros(shape=self.arg_shape_dict['conv_new_1_bias'])
        arg_params['fcis_cls_seg_weight'] = mx.random.normal(0, 0.01, shape=self.arg_shape_dict['fcis_cls_seg_weight'])
        arg_params['fcis_cls_seg_bias'] = mx.nd.zeros(shape=self.arg_shape_dict['fcis_cls_seg_bias'])
        arg_params['fcis_bbox_weight'] = mx.random.normal(0, 0.01, shape=self.arg_shape_dict['fcis_bbox_weight'])
        arg_params['fcis_bbox_bias'] = mx.nd.zeros(shape=self.arg_shape_dict['fcis_bbox_bias'])
