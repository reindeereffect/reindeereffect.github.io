#! /usr/bin/env python3

# [[file:~/dev/re/2020/05/05/index.org::sudoku/__init__.py][sudoku/__init__.py]]
'useful utilities for manipulating Sudoku puzzles'

import copy


from functools import reduce


import random


from math import inf
class board:
    'Utility class for representing and tracking board state.'

    def __init__(self, known, unknown, cell2divs, div2cells):
        '''
        known   dictionary mapping known cells to their respective values
        unknown dictionary mapping unknown cells to sets of possible values
    
        cell2divs, div2cells
                complementary mappings describing the board structure, such as those
                produced by board_divs
        '''
        assert not set(known) & set(unknown)
        self.known = known
        self.unknown = unknown
        self.cell2divs = cell2divs
        self.div2cells = div2cells
    def mark(self, cell, val):
        'set cell to val, updating unknowns as necessary'
        self.known[cell] = val
        self.unknown.pop(cell, None)
    
        for div in self.cell2divs[cell]:
            for cell2 in self.div2cells[div]:
                self.elim(cell2, val)
    
    def elim(self, cell, val):
        "remove val from cell's possibilities"
        self.unknown.get(cell, set()).discard(val)
    
    
    def marked(self, cell, val):
        'returns a new board, with cell marked as val and possibilities eliminated'
        new = self.copy()
        new.mark(cell, val)
        return new
    def copy(self):
        'copies board'
        return self.__class__(copy.deepcopy(self.known),
                              copy.deepcopy(self.unknown),
                              self.cell2divs,
                              self.div2cells)
    
def board_divs(order):
    '''
    generates a dictionary (cell2divs) mapping cells to their various divisions 
    in boards of the given order. Also generates a complementary mapping, 
    div2cells. Returns (cell2divs, div2cells).
    '''
    n = order**2
    box = lambda i, j: i//order * order + j//order
    cell2divs = dict(enumerate({i,
                                n + j,
                                2*n + box(i, j)}
                               for i in range(n)
                               for j in range(n)))

    return cell2divs, transpose(cell2divs)


def transpose(m):
    '''
    given a binary matrix represented as a dictionary whose values are sets,
    and where a 1 at (i,j) is indicated by

        j in m[i]

    return the transpose of m.
    '''
    t = {}
    for i, js in m.items():
        for j in js:
            t.setdefault(j, set()).add(i)

    return t


def load_board(s, validate_vals=True):
    '''
    given a string representing a board, returns a board object. For a board of
    a given order:

    - Order is computed as the fourth root of board length, and it must be an 
      integer.

    - Each cell must be represented by an integer in [1, order**2] inclusive, 
      or `.' to denote unknown cells. This check can be disabled by setting
      validate_vals to False.

    - Cells must be separated from each other by any sequences of characters in
      /[^0-9.]+/.

    On failure, raises ValueError.
    '''

    vals = [cell
            for cell in ''.join(c if c in '0123456789.' else ' '
                                for c in s).strip().split()
            if cell.isdigit() or cell == '.']

    order = int(len(vals) ** 0.25)
    n = order**2
    if len(vals) != order**4: raise ValueError

    bd = blank(order)

    for (cell, val_) in enumerate(vals):
        if val_ == '.': continue
        val = int(val_)
        if validate_vals and (val < 1 or val > n): raise ValueError
        bd.mark(cell, val)

    return bd


def blank(order):
  'generate a blank board'
  n = order**2
  possible_vals = set(range(1, n + 1))
  return board({},
               {i:set(possible_vals) for i in range(n**2)},
               *board_divs(order))


def isvalid(bd):
    '''
    returns True if
    - no known cells' values conflict
    - no unknown cell's possibilities conflict with any known cell's value
    '''
    return not any(val0 in {bd.known.get(cell)} | bd.unknown.get(cell, set())
                   for (cell0, val0) in bd.known.items()
                   for cell in neighbors(bd, cell0)
                   if cell in bd.known and cell != cell0)

def neighbors(bd, cell0):
    return union(bd.div2cells[div] for div in bd.cell2divs[cell0])

def union(xss):
    return {x for xs in xss for x in xs}


def dump_board(bd):
    'returns a "pretty printed" string representation of board bd'
    order = int((len(bd.known) + len(bd.unknown)) ** 0.25)
    n = order**2

    svals = [str(bd.known[i] if i in bd.known else '.')
             for i in range(n**2)]

    width = max(map(len, svals))
    fmt = lambda cell: ('%%%ds' % width) % cell

    n_x_n = [svals[i*n : i*n + n] for i in range(n)]
    cols_grpd = [' | '.join(' '.join(map(fmt, row[j*order : j*order + order]))
                           for j in range(order))
                 for row in n_x_n]    
    rows_grpd = ['\n'.join(cols_grpd[i*order : i*order + order])
                 for i in range(order)]

    rule = '\n' + ''.join('+' if c == '|' else '-' for c in cols_grpd[0]) + '\n'

    return rule.join(rows_grpd)


def mark_single_vals(bd):
    'applies the "single candidate" (a.k.a. "naked single") rule'
    marked = False
    for (cell, vals) in list(bd.unknown.items()):
        if len(vals) == 1:
            bd.mark(cell, set(vals).pop())
            marked = True

    return marked


def mark_single_cells(bd):
    'applies the "hidden single" rule'
    marked = False
    hidden = ((val, cells.pop())
              for div in bd.div2cells
              for (val, cells) in placements(bd, div).items()
              if len(cells) == 1)
    for (val, cell) in hidden:
        if val in bd.unknown.get(cell, set()):
            bd.mark(cell, val)
            marked = True
    return marked


def placements(bd, div):
    return transpose({cell: bd.unknown[cell]
                      for cell in bd.div2cells[div]
                      if cell in bd.unknown})


def mark_excluded(bd):
    marked = False
    excluded = ((cell, val)
                for div0 in bd.div2cells
                for (val, cells) in placements(bd, div0).items()
                for div in (intersection(bd.cell2divs[cell] for cell in cells)
                            - {div0})
                for cell in bd.div2cells[div] - cells - set(bd.known)
                if val in bd.unknown[cell])
    for (cell, val) in excluded:
        bd.elim(cell, val)
        marked = True
    return marked


def intersection(xs): return reduce(lambda a,x: a&x, xs)


def mark_forced(bd):
    '''
    iteratively applies single candidate, hidden single, and rule of exclusion
    until no further modifications are possible
    '''
    fns = (mark_single_vals, mark_single_cells, mark_excluded)
    while any(fn(bd) for fn in fns): pass
    return bd


def issolved(bd):
    'return True when no unknown cells remain. Assumes the board is valid.'
    return not bd.unknown


def solve(bd0, maxguesses=inf):
    'given a board bd0, generate all solutions in maxguesses guesses'
    stack = [(0, bd0.copy(), None)]
    while stack:
        depth, bd, delta = stack.pop()
        if delta: bd = bd.marked(*delta)
        mark_forced(bd)
        if issolved(bd): yield bd
        elif depth < maxguesses:
            _, _, cell, vals = min((len(vals), random.random(), cell, vals)
                                   for (cell, vals) in bd.unknown.items())
            stack.extend((depth+1, bd, (cell, val))
                         for val in random.sample(vals, len(vals)))


def marked_up(order, *marks):
    '''
    returns a new board of the given order, with the given marks, (cell, val)
    pairs, applied
    '''
    bd = blank(order)
    for mark in marks: bd.mark(*mark)
    return bd


def generate_from(soln, minbranch=False, maxguesses=inf):
    '''
    Generate a board for which soln is a solution, within at most maxguesses
    guesses. If set, minbranch restricts unknown cells to those that

    - can be easily deduced or
    - are among those with the fewest possible values.

    If maxguesses < inf, the generated board is guaranteed to be solvable
    within the prescribed number of guesses, but is not guaranteed to have only
    one solution.

    Returns (bd, difficulty) where bd is the generated board and difficulty is 
    a difficulty estimate.
    '''
    known = soln.known.copy()
    order = int(len(known) ** 0.25)
    clues = {}
    new = lambda: marked_up(order, *known.items(), *clues.items())    
    minunks = lambda bd: min(map(len, bd.unknown.values()))
    guesses = 0
    difficulty = 1

    while known:
        cell = random.choice(list(known))
        val = known.pop(cell)
        bd2 = new()
        mark_forced(bd2)

        if cell in bd2.known: pass
        elif (guesses >= maxguesses
              or minbranch and len(bd2.unknown[cell]) > minunks(bd2)
              or not isproper(bd2, maxguesses=maxguesses, clue=(cell, val))):
            clues[cell] = val
        else:
            difficulty *= len(bd2.unknown[cell])
            guesses += 1

    return new(), difficulty


def isproper(bd, maxguesses=inf, clue=None):
    'bd has exactly one solution within maxguesses guesses'
    nsolns = 0
    if clue:
        cell0, val0 = clue
        nsolns += 1
        for val in bd.unknown[cell0] - {val0}:
            for soln in solve(bd.marked(cell0, val), maxguesses):
                nsolns += 1
                if nsolns > 1: return False
    else:
        for soln in solve(bd, maxguesses):
            nsolns += 1
            if nsolns > 1: return False

    return nsolns == 1
# sudoku/__init__.py ends here
