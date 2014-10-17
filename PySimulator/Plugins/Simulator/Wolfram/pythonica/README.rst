*********
pythonica
*********

Introduction
============

pythonica is a Python package for the sane interface between Mathematica and
python via mathlink. The mathlink api provided with Mathematica has a
comprehensive and universal way of communicating with the Mathematica Kernel
that doesn't make quick and dirty communication all that easy. This wraps
around the mathlink module in a way to make things easier.

Quick Start
===========

Getting started is easy::

        >>> import pythonica
        >>> m = pythonica.Pythonica()
        >>> result = m.eval('D[Log[x],x]')
        >>> print(result)
        x^(-1)
        >>> X = [1,2,3,4]
        >>> m.push(X)
        >>> m.eval('sX = Mean[X];')
        >>> sX = m.pull('sX')
        >>> print(sX)
        2.5

The Pythonica Class
===================

The workhorse of the module is the Pythonica class, this makes a link to the
Mathematica kernel, and takes care of all the token, packet communication that
goes on between mathlink and python. It can take several arguments.

* ``name`` - The name provided to mathlink to start the Kernel
* ``mode`` - The mode to launch the mathlink Kernel. In combination with name 
  you can start remote kernels, but I don't understand howthis works, so best 
  to leave it be.
* ``timeout`` - Provides the time to wait after starting the Kernel
  before it's usable. 1 second seems to overkill, adjust at will.
* ``debug`` - For debugging use, will printout tons of information if
  you use it.
* ``plot_dir`` - Where to store plots created by Mathematica. If set to
  ``None``, no plots will be produces.
* ``plot_size`` - Tuple indicating the size in pixels for plots
* ``plot_format`` - string indicating file extension. If Mathematica
  can use it, it should work.
* ``input_prompt`` - boolean indicating whether to print input prompts
  from Mathematica
* ``output_prompt`` - boolean indicating whether to print output prompts
  from Mathematica

All of the values from ``debug`` on can be set interactively, for example::

        >>> m.debug = False

Pythonica.eval
================

The eval function takes string to be processes as Mathematica input and returns
the result. It takes several options

* ``expression`` - The expression to be evaluated. If it is malformed
  it will throw a ``PythonicaException``.
* ``make_plots`` - A boolean indicating whether to make any plots
  occuring from the function call.
* ``output_type`` - A string indicating the type of output to produce.
  If the output type is 'string' it will produce a string. If the output
  type is 'python' will attempt to convert the output to python for 
  storage. For conversion to work the str_format must be 'input' See 
  *Pythonica.pull* for more info.
* ``str_format`` - A string indicating the type of string to produce if
  ``output_type`` is 'string'. If 'input' will produce a string which is valid
  Mathematica Code, and can be fed back into ``eval``, if 'tex' will produce tex 
  code, or if 'plain' will produce whatever mathematica would have produced. If 
  you use ``print`` this usually looks ok.



Examples
--------
::

        >>> m.eval('Series[Exp[x],{x,0,3}]')
        'SeriesData[x, 0, {1, 1, 1/2, 1/6}, 0, 4, 1]'
        >>> m.eval('Series[Exp[x],{x,0,3}]', str_format='tex')
        '1+x+\\\\frac{x^2}{2}+\\\\frac{x^3}{6}+O\\\\left(x^4\\\\right)'
        >>> result = m.eval('Series[Exp[x],{x,0,3}]',str_format='plain')
        >>> print(result)
                 2    3
                x    x        4
        1 + x + -- + -- + O[x]
                2    6
        >>> m.eval('Mean[{1,2,3,4}]',output_type='python')
        2.5


Pythonica.push
==============

This function attempts to push a python value to the Mathematica Kernel. It
attempts to convert the value first then sends it.

* ``name`` - The name the value will have in the Mathematica Kernel
* ``value`` - The python value to be passed.

This currently works by just calling the Mathematica function ``Set``.
Mathematica's type system is not as extensive as Python's here are how things
are set.

* Python type -> Mathematica type
* ``bool`` -> ``Booleans``
* ``None`` -> ``Null``
* ``float`` -> ``Real``
* ``int`` -> ``Integer``
* ``long`` -> ``Integer``
* ``complex`` -> ``Complex``
* ``iter`` -> ``List``
* ``list`` -> ``List``
* ``set`` -> ``List``
* ``xrange`` -> ``List``
* ``str``-> ``String``
* ``tuple`` -> ``List``
* ``frozenset`` -> ``List``

Note that there is currently no support for numpy arrays. This could be
possible in the future given the current interface, but for large arrays would
be slow. Note that since we are essentially converting everything to strings,
this can be exceptionally slow and memory intensive for large amounts of data.
Consider reading and writing to and from files.

There is no simple type in Mathematica that corresponds to dict, or at least
not that I can find, patches welcome!

The conversion happens recursively so a list of lists will be appropriately
converted.

Examples
--------
::

        >>> m.push('x',5)
        >>> m.eval('x')
        '5'
        >>> m.push('l',4L)
        >>> m.eval('l')
        '4'
        >>> m.push('y',.5)
        >>> m.eval('y')
        '0.5'
        >>> m.push('z',complex(3,4))
        >>> m.eval('z')
        '3. + 4.*I'
        >>> m.push('t',True)
        >>> m.eval('t')
        'True'
        >>> m.push('f',False)
        >>> m.eval('f')
        'False')
        >>> m.push('n',None)
        >>> m.eval('n')
        'None'
        >>> m.push('r',range(3))
        >>> m.eval('r')
        '{0, 1, 2}'
        >>> m.push('L',[1,2,3])
        >>> m.eval('L')
        '{1, 2, 3}'
        >>> m.push('s',set([1,2,3])
        >>> m.eval('s')
        '{1, 2, 3}'
        >>> m.push('xr',xrange(2))
        >>> m.eval('xr')
        '{0, 1}'
        >>> m.push('st','spam')
        >>> m.eval('st')
        '"spam"'
        >>> m.push('fs',frozenset([1,2,3])
        >>> m.eval('fs')
        '{1, 2, 3}'
        >>> m.push('ll', [1,2,'hello',[2,2.5,4],complex(3,4)]
        >>> m.eval('ll')
        '{1, 2, "hello", {2, 2.5, 4}, 3. + 4*I}'

Pythonica.pull
==============

This command pulls variables out of the Mathematica kernel into python and
attempts to convert them into python types. The return value is the same as the
return from ``eval`` when ``output_type`` is 'python'. Since Mathematica
returns expressions which are based on function calls we take those function
calls and try to convert them. First the basics.

* Mathematica Type -> Python Type
* ``Integer`` -> ``int`` or ``long`` depending on size
* ``Rational`` or anything with '\' -> Attempts to go to ``float``
* ``Complex`` or anything with 'I' -> Attempts to go to ``complex``
* ``String`` -> str
* symbols -> str
* functions -> dict...

Let me explain the functions -> dict. If we can't convert the part of the
expression into a python type, we make a dictionary with a single key, the
function name, the value of which is a list of arguments to that function. If
there are nested function calls the produces dicts of lists of dicts. If all
else fails it just returns the original string. Still with me? If not here 
are some...

Examples
--------
::

        >>> m.eval('X = Unevaluated[D[Log[x],x]];')
        >>> m.pull('X')
        {'Hold': [{'D': [{'Log': ['q']}, 'q']}]}
        >>> m.eval('Y = Integrate[D[Log[q],q],{q,1.1,10.1}];'
        >>> m.pull('Y')
        2.2172252349699813

Other Types
-----------

In the future we could convert different function types. IE if Mathematica
returns ``Log[10]``, we could evaluate ``math.log(10)``.

Plotting
========

Mathematica has a rich graphics system. If any of your output produces the
words 'Graphics', 'Graphics3D', 'Image', or 'Grid', pythonica will use the
``Export`` function of Mathematica to produce the image. The images will be
called 'pythonica_plot_x.ext' where 'x' is an increasing number as you produce
more plots, and 'ext' is the extension provided by ``Pythonica.plot_format``.

Examples
--------
::

        >>> m.plot_dir = '.'
        >>> res = m.eval('Plot[Sin[q],{q,0,10}]')

Produces a plot called 'pythonica_plot_0.png' in the current directory.


Copyright (C) 2012 
Benjamin Edwards <bedwards@cs.unm.edu>

Distributed with a BSD license; see LICENSE

