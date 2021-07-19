# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: add
short_description: Add 2 numbers together
version_added: "1.0.0"
description:
    - Add 2 numbers together
options:
  first:
    description:
      - The first number
    type: float
    required: True
  second:
    choices:
    - 10
    - 20
    description:
      - The second number
    type: float
    required: True
  third:
    description:
      - The third number
    type: float
  fourth:
    description:
      - The fourth number
    type: float

notes:

author:
- Bradley Thornton (@cidrblock)
"""

EXAMPLES = r"""
"""


RETURN = """
connection_details:
  description: connection details
  returned: always
  type: dict
sum:
  description: The sum of the numbers
  returned: always
  type: int
"""