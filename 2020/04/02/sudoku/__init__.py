#! /usr/bin/env python3

'useful utilities for manipulating Sudoku puzzles'

import copy


from math import inf
import random
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
    cell2divs = dict(enumerate((i,
                                n + j,
                                2*n + box(i, j))
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
  n = order**2
  possible_vals = set(range(1, n + 1))
  return board({},
              {i:set(possible_vals) for i in range(n**2)},
              *board_divs(order))


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
    for div, cells in bd.div2cells.items():
        spots =  transpose({cell: bd.unknown.get(cell, set())
                            for cell in cells})
        for v, cs in spots.items():
            if len(cs) == 1:
                cell = cs.pop()
                if v in bd.unknown.get(cell, set()):
                    bd.mark(cell, v)
                    marked = True

    return marked


def mark_forced(bd):
    '''
    iteratively applies single candidate and hidden single rules until no
    further modifications are possible
    '''
    fns = (mark_single_vals, mark_single_cells)
    while any(fn(bd) for fn in fns): pass


def solve(bd, maxdepth=inf):
    'given a board bd, generates all solutions in maxdepth guesses'
    def _solve(bd, depth=0):
        mark_forced(bd)    
        if issolved(bd):
            yield bd 
        elif depth < maxdepth:
            _, _, cell, vals = min((len(vals), random.random(), cell, vals)
                                   for (cell, vals) in bd.unknown.items())
            for val in random.sample(vals, len(vals)):
                yield from _solve(bd.marked(cell, val), depth=depth+1)

    return _solve(bd.copy())


def issolved(bd):
    'returns True when no unknown cells remain. Assumes the board is valid.'
    return not bd.unknown


def generate_from(soln, minrule=False, maxdepth=inf):
    'given a solution, generate a puzzle (like Jeopardy!)'

    known = soln.known.copy()
    order = int(len(known) ** 0.25)
    clues = {}

    def new():
        bd = blank(order)
        for (cell, val) in known.items(): bd.mark(cell, val)
        for (cell, val) in clues.items(): bd.mark(cell, val)
        return bd

    minvals = lambda bd: min(map(len, bd.unknown.values()))

    while known:
        cell = random.choice(list(known))
        val = known.pop(cell)
        bd2 = new()
        mark_forced(bd2)

        if cell in bd2.known:
            pass
        elif minrule and len(bd2.unknown[cell]) > minvals(bd2):
            clues[cell] = val
        elif not isproper(bd2, maxdepth=maxdepth):
            clues[cell] = val

    return new()


def isproper(bd, maxdepth=inf):
    nsolns = 0
    for soln in solve(bd, maxdepth):
        nsolns += 1
        if nsolns > 1: break

    return nsolns == 1


def rate(bd):
    'estimate the difficulty of bd'
    ncells = len(bd.known) + len(bd.unknown)
    soln2 = bd.copy()
    mark_forced(soln2)
    first_guess = len(soln2.known)
    return 1 - first_guess/ncells


def isvalid(bd):
    if not bd.known and not bd.unknown: return False
    
    for (div, cells) in bd.div2cells.items():
        vals = [bd.known[cell] for cell in cells if cell in bd.known]
        if len(vals) != len(set(vals)):
            return False
        elif any(bd.unknown.get(cell, set()) & set(vals) for cell in cells):
            return False
        
    return True
