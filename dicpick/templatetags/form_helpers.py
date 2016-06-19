# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

from django import template
from django.forms import BaseForm
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def add_standard_classes(bound_field):
  widget_name = type(bound_field.field.widget).__name__.lower()
  form_control_class = '' if widget_name == 'checkboxinput' else 'form-control'
  css_class = '{} field-{} widget-{}'.format(form_control_class, bound_field.name, widget_name)
  return bound_field.as_widget(attrs={'class':css_class})


@register.filter(needs_autoescape=True)
def lightweight_formatting(text, autoescape=True):
  if autoescape:
    esc = conditional_escape
  else:
    esc = lambda x: x

  def indents(line):
    i = 0
    ret = ''
    while i < len(line) and line[i] == ' ':
      ret += '&nbsp;'
      i += 1
    ret += line[i:]
    return ret

  def newlines(block):
    return '<br>'.join([indents(esc(s)) for s in block.split('\n')])

  blocks = text.split('```')
  codified = ''
  for i in range(0, len(blocks) - 1):
    codified += newlines(blocks[i])
    if i % 2 == 0:
      codified += '<code>'
    else:
      codified += '</code>'
  codified += newlines(blocks[-1])

  return mark_safe(codified)


@register.filter
def has_required_fields(form):
  return _has_field_with_property(form, lambda field: field.required)


def _has_field_with_property(form, predicate):
  if isinstance(form, BaseForm):
    return any(predicate(x) for x in form.fields.values())
  else:  # Assume it's a FormSet.
    return any(predicate(x) for x in form.forms[0].fields.values())
