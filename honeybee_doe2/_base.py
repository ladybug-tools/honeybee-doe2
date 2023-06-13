# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*-
"""Base class for Honeybee-Doe2 Objects"""
import uuid


class _Base(object):
    """doe2 base class"""

    def __init__(self):
        self._identifier = uuid.uuid4()
        self.user_data = {}
        self._display_name = self._identifier
