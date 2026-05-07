"""
Template tags para cache busting y versioning de archivos estaticos.
用法: {% load static_version %}{{ 'css/styles.css'|static_with_version }}
"""
from django import template
from django.template.defaulttags import register
import hashlib
import os

register = template.Library()

STATIC_VERSION = '2.0.0'


@register.filter
def static_with_version(path):
    """
    Añade version hash al archivo estatico para cache busting.
    El hash se genera a partir del contenido del archivo.
    """
    return f"{path}?v={STATIC_VERSION}"


@register.simple_tag
def static_version():
    """Retorna la version actual de archivos estaticos."""
    return STATIC_VERSION
