""" Docstrings that support AI code generation.

This module provides a decorator that allows you to write a function's docstring
before creating the function itself, enabling AI code generation.
"""

def describe(docstring):
    """ Decorator that adds a docstring to a function. """
    def decorator(func):
        if func.__doc__:
            func.__doc__ += '\n' + docstring
        else:
            func.__doc__ = docstring
        return func
    return decorator