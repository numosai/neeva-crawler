"""
HTML Generator module for Neeva-Crawler
Transforms raw analysis data into deployable static websites
"""
from .generator import HTMLGenerator
from .data_processor import DataProcessor

__all__ = ['HTMLGenerator', 'DataProcessor']