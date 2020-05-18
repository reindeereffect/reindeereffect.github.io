#! /usr/bin/env python

from dot import imgtex

def trim(start, accepts, delta, nfa=False):
    atled = {}
    for q in delta:
        for s in delta[q]:
            if nfa:
                for r in delta[q][s]:
                    atled.setdefault(r, {}).setdefault(s, set()).add(q)
            else:
                r = delta[q][s]
                atled.setdefault(r, {}).setdefault(s, set()).add(q)
    visited = set()
    todo = set(accepts)
    while todo:
        q = todo.pop()
        if q in visited: continue
        visited.add(q)
        for (s, rs) in atled.get(q, {}).items(): todo |= set(rs)

    delta2 = {}
    for q in delta:
        if q not in visited: continue
        for s in delta[q]:
            if nfa:
                for r in delta[q][s]:
                    if r not in visited: continue
                    delta2.setdefault(q, {}).setdefault(s, set()).add(r)
            else:
                r = delta[q][s]
                if r not in visited: continue
                delta2.setdefault(q, {})[s] = r

    return delta2

def collapse_ranges(xs):
    xs2 = sorted(xs)
    acc = [xs2[0]]
    
    for x in xs2[1:]:
        try:
            if ord(x) == ord(acc[-1]) + 1:
                acc.append(x)
                continue
        except: pass
        
        yield acc[0] if len(acc) == 1 else '%s-%s' % (acc[0], acc[-1])
        acc = [x]
        
    yield acc[0] if len(acc) == 1 else '%s-%s' % (acc[0], acc[-1])
    
def fsm(start, accepts, delta, nfa=False, label_states=True, trim_unreachable=True):
    accepts = set(accepts)
    states = set(accepts)
    states.add(start)
        
    edges_ = {}
    if trim_unreachable:
        delta = trim(start, accepts, delta, nfa=nfa)
    
    for src in delta:
        states.add(src)
        for lbl in delta[src]:
            if nfa:
                for dest in delta[src][lbl]:
                    states.add(dest)
                    edges_.setdefault((src, dest), set()).add(lbl)
            else:
                dest = delta[src][lbl]
                states.add(dest)
                edges_.setdefault((src, dest), set()).add(lbl)

    other = states - accepts

    n = lambda q: "q_%s" % str(q).replace(' ', '_')
    l = lambda s: '&epsilon;' if s == None else s
        
    na = '\n'.join('node [label="%s", shape="doublecircle"] %s;' % (a if label_states else "", n(a)) for a in accepts)
    ss = '\n'.join('node [label="%s", shape="circle"] %s;' % (s if label_states else "",n(s)) for s in other)
    edges = '\n'.join('%s -> %s [label="%s"];' % (n(src), n(dest), ','.join(map(l, sorted(collapse_ranges(lbls))))) for ((src, dest), lbls) in edges_.items())
        
    acc = '''
digraph g {
    graph [compound=true, rankdir=LR, splines="true"];
node [shape="none", label="start"] start;
%(nodes)s
start -> %(start)s [label=""];
%(edges)s
}''' % dict(nodes=na + '\n' + ss, edges=edges, start=n(start))
    #print(acc)
    imgtex().dot(None, acc)

