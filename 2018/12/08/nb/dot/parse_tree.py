#! /usr/bin/env python

from functools import reduce
import dot

################################################################################
def format_node(n):
    fmt = 'node [label="%s&#92;n%s", shape="rectangle"] %s;'
    fmt_s = 'node [label="%s", shape="rectangle"] %s;'
    if type(n) == list:
        return 'node [label="", shape="circle"] %s;' % nid(n)

    if n.terminal:
        label = n.value.replace('"', '\\"')
        if n.type == 'EPSILON':
            return 'node [label="&epsilon;", shape="rectangle"] %s;' % nid(n)
            return fmt % ('&epsilon;', '', nid(n))
        else:
            if not n.type:
                return fmt_s % (label, nid(n))
            return fmt % (n.type, label, nid(n))
    else:
        return 'node [label="%s", shape="oval"] %s;' % (n.type, nid(n))

    
def nid(n): return 'n_%s' % id(n)


def format_edge(src, dest, invis=False):
    fmt = '%s -> %s [style=invis];' if invis else '%s -> %s;'
    return fmt % (nid(src), nid(dest))


def nodes(T):
    yield T
    if type(T) == list:
        for t in T:
            for n in nodes(t): yield n
    elif not T.terminal:
        for t in T.value:
            for n in nodes(t): yield n
            

def terminals(T): return (n for n in nodes(T) if getattr(n, 'terminal', False))


def edges(src):
    if type(src) == list:
        for dest in src:
            yield (src, dest)
            for e in edges(dest): yield e
    elif not src.terminal:
        for dest in src.value:
            yield (src, dest)
            for e in edges(dest): yield e

            
def make_rank(ns): return '{rank=same;%s}' % ';'.join(map(nid, ns))


 
def parse_tree(T, unconsumed="", display=True):
    acc = []
    emit = acc.append

    emit('digraph g {')
    emit('color="#ffffffff";')
    emit('bgcolor="#ffffff00";')
     
    for n in nodes(T): emit(format_node(n))
    for e in edges(T): emit(format_edge(*e))

    terms = list(terminals(T))
    last = None
    for t in terms:
        if last: emit(format_edge(last, t, invis=True))
        last = t

    unconsumed = unconsumed.strip()
    if unconsumed:
        emit('node [label="unconsumed: %s", shape="none"] unconsumed' % unconsumed)
        emit('%s -> unconsumed [style=invis]' % nid(last))
        
    emit(make_rank(terms))
    emit('}')

    cell = '\n'.join(acc)

    return dot.imgtex().dot(None, cell) if display else cell
    
