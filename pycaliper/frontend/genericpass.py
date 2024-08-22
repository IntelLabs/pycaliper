"""
    PyCaliper

    Author: Adwait Godbole, UC Berkeley

    File: frontend/genericpass.py

    Abstract pass class for pass-based compilation infrastructure.
"""

import logging

from pycaliper.frontend.pycast import PAST

logger = logging.getLogger(__name__)


class GenericPass:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.passes = []

    def generic_visit(self, node):

        if node is None:
            return
        logger.debug(
            f"generic_visit called for node {node} of class {node.__class__.__name__}"
        )
        if isinstance(node, list):
            for n in node:
                self.visit(n)
        if isinstance(node, PAST):
            for n in node.children:
                self.visit(n)

    def visit(self, node):
        method = f"visit_{node.__class__.__name__}"
        # Check if node specific visitor exists, otherwise use generic visitor
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)
