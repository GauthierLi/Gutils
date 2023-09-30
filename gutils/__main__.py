# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2023 Baidu.com, Inc. All Rights Reserved
#
################################################################################
"""
本文件允许模块包以python -m gutils方式直接执行。

Authors: liweikang02(liweikang02@baidu.com)
Date:    2023/09/27 11:12:47
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals


import sys
from gutils.cmdline import main
sys.exit(main())
