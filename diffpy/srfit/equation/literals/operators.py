#!/usr/bin/env python
########################################################################
#
# diffpy.srfit      by DANSE Diffraction group
#                   Simon J. L. Billinge
#                   (c) 2008 Trustees of the Columbia University
#                   in the City of New York.  All rights reserved.
#
# File coded by:    Chris Farrow
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
########################################################################
"""Operator classes. 

Operators are combined with other Literals to create an equation. Operators are
non-leaf nodes on a Literal tree. These trees can be evaluated by the Evaluator
visitor, or otherwise inspected. 

The Operator class contains all the information necessary to be identified and
evaluated by a Visitor. Thus, a single onOperator method exists in the Visitor
base class. Other Operators can be derived from Operator (see AdditionOperator),
but they all identify themselves with the Visitor.onOperator method.

Operators can be made to operate conditionally by specifying tags.  When applied
to a Partition, only parts of the Partition that contain one of the tags
specified by the Operator will be operated upon.  If the operator specifies no
tags, then it will work on all parts of a Partition.

Operators have a 'setCombine' method that will tell an Evaluator whether a
Partition can be combined after the operation. By default they cannot. The
CombineOperator will combine a Partition but leave other literals unchanged.
See the Partition module for combination rules.

"""

from .literal import Literal
import numpy

class Operator(Literal):
    """Class for holding a general operator.

    This holds a general operator and records its function, arguments, name and
    symbol.  The visitors should be able to process any Operator with this
    information alone.

    Attributes
    args    --  List of Literal arguments, set with addLiteral
    clicker --  A Clicker instance for recording change in the dependent
                arguments.
    name    --  A name for this operator. e.g. "add" or "sin"
    nin     --  Number of inputs (negative means this is variable)
    nout    --  Number of outputs
    operation   --  Function that performs the operation. e.g. numpy.add or
    symbol  --  The symbolic representation. e.g. "+" or "sin"
                numpy.sin
    _tags   --  Set of tags for this operator
    _cancombine --  Indicates whether this operator can combine a Partition.
    _proxy      --  The Argument, Partition or value that this Operator results
                    in (used by the Evaluator).

    """

    # Required attributes - used for type checking
    args = None
    nin = None
    nout = None
    operation = None
    symbol = None
    _tags = None
    _cancombine = None
    _proxy = None

    def __init__(self, name = None, symbol = None, operation = None,
            nin = 2, nout = 1, tags = []):
        """Initialization."""
        Literal.__init__(self)
        self.name = name
        self.symbol = symbol
        self.nin = nin
        self.nout = nout
        self.args = []
        self.operation = operation
        self._tags = set(tags)
        self._cancombine = False
        # used by Evaluator
        self._proxy = None
        return

    def identify(self, visitor):
        """Identify self to a visitor."""
        visitor.onOperator(self)
        return

    def addLiteral(self, literal):
        """Add a literal to this operator.

        Note that order of operation matters. The first literal added is the
        leftmost argument. The last is the rightmost.

        """
        self.args.append(literal)
        self.clicker.addSubject(literal.clicker)
        return

    def setCombine(self, combine=True):
        """Set whether this operator can combine Partitions.

        By default, operators cannot combine Partitions.

        combine --  combine flag (default True)

        """
        if combine != self._cancombine:
            self._cancombine = combine
            self._proxy = None
            self.clicker.click()
        return

    def addTags(self, *args):
        """Add tags to the operator."""
        map(self._tags.add, args)
        self._proxy = None
        self.clicker.click()
        return

    def clearTags(self):
        """Clear all tags."""
        self._tags = set()
        self._proxy = None
        self.clicker.click()
        return

    def __str__(self):
        if self.name:
            return "Operator(" + self.name + ")"
        return self.__repr__()


# Some specified operators


class AdditionOperator(Operator):
    """Addition operator."""

    def __init__(self):
        """Initialization."""
        Operator.__init__(self)
        self.name = "add"
        self.symbol = "+"
        self.operation = numpy.add
        return

class SubtractionOperator(Operator):
    """Subtraction operator."""

    def __init__(self):
        """Initialization."""
        Operator.__init__(self)
        self.name = "subtract"
        self.symbol = "-"
        self.operation = numpy.subtract
        return

class MultiplicationOperator(Operator):
    """Multiplication operator."""

    def __init__(self):
        """Initialization."""
        Operator.__init__(self)
        self.name = "multiply"
        self.symbol = "*"
        self.operation = numpy.multiply
        return

class DivisionOperator(Operator):
    """Division operator."""

    def __init__(self):
        """Initialization."""
        Operator.__init__(self)
        self.name = "divide"
        self.symbol = "/"
        self.operation = numpy.divide
        return

class ExponentiationOperator(Operator):
    """Exponentiation operator."""

    def __init__(self):
        """Initialization."""
        Operator.__init__(self)
        self.name = "power"
        self.symbol = "**"
        self.operation = numpy.power
        return

class RemainderOperator(Operator):
    """Remainder operator."""

    def __init__(self):
        """Initialization."""
        Operator.__init__(self)
        self.name = "mod"
        self.symbol = "%"
        self.operation = numpy.mod
        return

class NegationOperator(Operator):
    """Negation operator."""

    def __init__(self):
        """Initialization."""
        Operator.__init__(self)
        self.name = "negative"
        self.symbol = "-"
        self.nin = 1
        self.operation = numpy.negative
        return

class ConvolutionOperator(Operator):
    """Scaled version of the numpy.convolve operator.

    This calls numpy.convolve, but divides by the sum of the second argument in
    hopes of preserving the scale of the first argument.
    numpy.conolve(v1, v2, mode = "same")/sum(v2)
    It then truncates to the length of the first array.

    """

    def __init__(self):
        """Initialization."""
        Operator.__init__(self)
        self.name = "convolve"
        self.symbol = "convolve"

        def conv(v1, v2):
            """numpy.conolve(v1, v2, mode = "same")/sum(v2)"""
            c = numpy.convolve(v1, v2, mode="same")/sum(v2)
            c.resize((len(v1),))
            return c

        self.operation = conv
        return


class SumOperator(Operator):
    """numpy.sum operator."""

    def __init__(self):
        """Initialization."""
        Operator.__init__(self)
        self.name = "sum"
        self.symbol = "sum"
        self.nin = 1
        self.nout = 1
        self.operation = numpy.sum
        return

class UFuncOperator(Operator):
    """A operator wrapper around a numpy ufunc.

    The name and symbol attributes are set equal to the ufunc.__name__
    attribute. nin and nout are also taken from the ufunc.
    
    """

    def __init__(self, op):
        """Initialization.

        Arguments
        op  --  A numpy ufunc

        """
        Operator.__init__(self)
        self.name = op.__name__
        self.symbol = op.__name__
        self.nin = op.nin
        self.nout = op.nout
        self.operation = op
        return

class CombineOperator(Operator):
    """Operator for combining Partitions.

    This acts as the identity function (f(x) = x) to non-Partition literals.

    """

    def __init__(self):
        """Initialization."""
        Operator.__init__(self)
        self.name = "combine"
        self.symbol = "combine"
        self.nin = 1
        self.operation = lambda x: x
        self._cancombine = True
        return

class ListOperator(Operator):
    """Operator that will take parameters and turn them into a list."""

    def __init__(self):
        """Initialization."""
        Operator.__init__(self)
        self.name = "list"
        self.symbol = "list"
        self.nin = -1

        def makeList(*args):
            return args

        self.operation = makeList
        return

class SetOperator(Operator):
    """Operator that will take parameters and turn them into a set."""

    def __init__(self):
        """Initialization."""
        Operator.__init__(self)
        self.name = "set"
        self.symbol = "set"
        self.nin = -1

        def makeSet(*args):
            return set(args)

        self.operation = makeSet
        return

class ArrayOperator(Operator):
    """Operator that will take parameters and turn them into an array."""

    def __init__(self):
        """Initialization."""
        Operator.__init__(self)
        self.name = "array"
        self.symbol = "array"
        self.nin = -1

        def makeArray(*args):
            return numpy.array(args)

        self.operation = makeArray
        return


class PolyvalOperator(Operator):
    """Operator for numpy polyval."""

    def __init__(self):
        """Initialization."""
        Operator.__init__(self)
        self.name = "polyval"
        self.symbol = "polyval"
        self.nin = 2
        self.operation = numpy.polyval
        return

# version
__id__ = "$Id$"

#
# End of file
