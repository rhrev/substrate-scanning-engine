#!/usr/bin/env python3
# Copyright (c) 2026 Ricardo Hernández Reveles
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Serie I · Graph Spectral Engine — 29 features from any graph"""
import numpy as np
from numpy.linalg import eigh
from scipy.stats import spearmanr
import time

class Graph:
    def __init__(self, adj, labels=None, name='graph'):
        self.A = np.array(adj, dtype=float); self.N = self.A.shape[0]
        self.name = name; self.labels = labels or list(range(self.N))
        self.degrees = self.A.sum(axis=1); self.total_edges = int(self.A.sum()/2)
        self.mean_degree = self.degrees.mean()
        self.is_regular = (self.degrees.max()-self.degrees.min()) < 0.01
        self.L = np.diag(self.degrees) - self.A
        self._evals = None; self._evecs = None
    def spectrum(self, n=None):
        if self._evals is None:
            v, w = eigh(self.L); self._evals = v; self._evecs = w
        return self._evals[:n] if n else self._evals
    def eigenvector(self, i):
        if self._evecs is None: self.spectrum()
        return self._evecs[:,i] if i < self._evecs.shape[1] else np.zeros(self.N)
    @staticmethod
    def from_edge_list(edges, N=None, name='graph'):
        if N is None: N = max(max(e) for e in edges)+1
        a = np.zeros((N,N))
        for i,j in edges: a[i,j]=a[j,i]=1
        return Graph(a, name=name)

class GG:
    @staticmethod
    def erdos_renyi(N, p, seed=None):
        rng=np.random.RandomState(seed); a=np.zeros((N,N))
        for i in range(N):
            for j in range(i+1,N):
                if rng.random()<p: a[i,j]=a[j,i]=1
        return Graph(a, name=f'ER({N},{p:.2f})')
    @staticmethod
    def barabasi_albert(N, m, seed=None):
        rng=np.random.RandomState(seed); a=np.zeros((N,N))
        for i in range(m+1):
            for j in range(i+1,m+1): a[i,j]=a[j,i]=1
        for new in range(m+1,N):
            d=a[:new].sum(axis=1); pr=d/(d.sum()+1e-15)
            for t in rng.choice(new,size=m,replace=False,p=pr): a[new,t]=a[t,new]=1
        return Graph(a, name=f'BA({N},{m})')
    @staticmethod
    def watts_strogatz(N, k, p, seed=None):
        rng=np.random.RandomState(seed); a=np.zeros((N,N))
        for i in range(N):
            for j in range(1,k//2+1): a[i,(i+j)%N]=a[(i+j)%N,i]=1
        for i in range(N):
            for j in range(1,k//2+1):
                if rng.random()<p:
                    t=(i+j)%N; a[i,t]=a[t,i]=0
                    nt=rng.randint(0,N)
                    while nt==i or a[i,nt]==1: nt=rng.randint(0,N)
                    a[i,nt]=a[nt,i]=1
        return Graph(a, name=f'WS({N},{k},{p:.2f})')
    @staticmethod
    def stochastic_block(sizes, pw, pb, seed=None):
        rng=np.random.RandomState(seed); N=sum(sizes); a=np.zeros((N,N))
        off=[0]+list(np.cumsum(sizes))
        for bi in range(len(sizes)):
            for bj in range(bi,len(sizes)):
                p=pw if bi==bj else pb
                for i in range(off[bi],off[bi+1]):
                    s=i+1 if bi==bj else off[bj]
                    for j in range(s,off[bj+1]):
                        if rng.random()<p: a[i,j]=a[j,i]=1
        lb=[]
        for bi,sz in enumerate(sizes): lb.extend([f'C{bi}']*sz)
        return Graph(a, labels=lb, name=f'SBM({sizes})')
    @staticmethod
    def star(N):
        a=np.zeros((N,N))
        for i in range(1,N): a[0,i]=a[i,0]=1
        return Graph(a,name=f'Star({N})')
    @staticmethod
    def path(N):
        a=np.zeros((N,N))
        for i in range(N-1): a[i,i+1]=a[i+1,i]=1
        return Graph(a,name=f'Path({N})')
    @staticmethod
    def grid_2d(r,c):
        N=r*c; a=np.zeros((N,N))
        for ri in range(r):
            for ci in range(c):
                i=ri*c+ci
                if ci+1<c: a[i,i+1]=a[i+1,i]=1
                if ri+1<r: a[i,i+c]=a[i+c,i]=1
        return Graph(a,name=f'Grid({r}x{c})')
    @staticmethod
    def bot_farm(nb,nt,nl,seed=None):
        rng=np.random.RandomState(seed); N=nb+nt+nl; a=np.zeros((N,N))
        for b in range(nb):
            for t in range(nb,nb+nt):
                if rng.random()<0.9: a[b,t]=a[t,b]=1
        for b1 in range(nb):
            for b2 in range(b1+1,nb):
                if rng.random()<0.3: a[b1,b2]=a[b2,b1]=1
        for i in range(nb+nt,N):
            for t in rng.choice(N,size=rng.randint(1,min(8,N)),replace=False):
                if t!=i: a[i,t]=a[t,i]=1
        lb=['bot']*nb+['target']*nt+['legit']*nl
        return Graph(a,labels=lb,name=f'BotFarm({nb},{nt},{nl})')

FNAMES=['algebraic_conn','n_components','gap_norm','cheeger','degree_CV','degree_max_ratio','density','spectral_radius','mean_spacing','spacing_CV','level_repulsion','spectral_entropy','n_eigs','partition_bal','cut_ratio','n_near_zero','max_eigengap','eff_resistance','gap_robustness','max_gap_idx','N','E','avg_degree','is_expander','is_ramanujan','small_world','hub_dominance','bipartiteness','health']

def graph_features(G, n_modes=20):
    eigs=G.spectrum(n_modes); n=len(eigs); N=G.N
    if n<3: return np.zeros(29)
    alg=eigs[1] if n>1 else 0; nc=sum(1 for e in eigs if e<1e-8)
    gn=alg/(G.mean_degree+1e-15); ch=alg/2
    dcv=G.degrees.std()/(G.mean_degree+1e-15); dmr=G.degrees.max()/(G.mean_degree+1e-15)
    dens=2*G.total_edges/(N*(N-1)+1e-15); sr=eigs[-1]
    sp=np.diff(eigs[1:])
    if len(sp)>1: ms=sp.mean();ss=sp.std();scv=ss/(ms+1e-15)
    else: ms=ss=scv=0
    if len(sp)>2:
        rats=[min(sp[i],sp[i+1])/(max(sp[i],sp[i+1])+1e-15) for i in range(len(sp)-1)]
        mr=np.mean(rats)
    else: mr=0
    ep=eigs[eigs>1e-10]
    se=-np.sum((ep/ep.sum())*np.log(ep/ep.sum()+1e-15)) if len(ep)>0 else 0
    fi=G.eigenvector(1); np_=np.sum(fi>0); nn=np.sum(fi<0)
    pb=min(np_,nn)/(max(np_,nn)+1e-15)
    ce=sum(1 for i in range(N) for j in range(i+1,N) if G.A[i,j]>0 and fi[i]*fi[j]<0)
    cr=ce/(G.total_edges+1e-15)
    nnz=sum(1 for e in eigs if e<alg*0.1)
    mg=0;mgi=0
    for i in range(1,min(n-1,10)):
        g=eigs[i+1]-eigs[i]
        if g>mg: mg=g;mgi=i
    enz=eigs[eigs>1e-10]
    er=min(N*np.sum(1.0/enz),1e6) if len(enz)>0 else 1e6
    ern=er/(N*N+1e-15); gr=alg/(G.degrees.max()+1e-15)
    ie=float(gn>0.1)
    if G.is_regular:
        d=G.degrees[0]; rb=2*np.sqrt(d-1) if d>1 else 0; ir=float(sr<=d+rb+0.01)
    else: rb=0;ir=0
    sw=gn*pb; hd=sr/(G.mean_degree+1e-15); bi=abs(sr-2*G.mean_degree)/(G.mean_degree+1e-15)
    h=min(alg*pb/(ern+1e-10),1000)
    return np.array([alg,float(nc),gn,ch,dcv,dmr,dens,sr,ms,scv,mr,se,float(n),pb,cr,float(nnz),mg,ern,gr,float(mgi),float(N),float(G.total_edges),G.mean_degree,ie,ir,sw,hd,bi,h])

def classify_graph(v):
    tags=[]
    if v[1]>1.5: tags.append(('DISCONNECTED',f'{int(v[1])} components'))
    if v[2]>0.3: tags.append(('EXPANDER',f'gap/d={v[2]:.3f}'))
    if v[4]>1.5 and v[5]>5: tags.append(('SCALE-FREE',f'CV={v[4]:.2f}'))
    elif v[4]<0.2: tags.append(('REGULAR',f'CV={v[4]:.3f}'))
    if v[26]>3: tags.append(('HUB-DOMINATED',f'hub={v[26]:.2f}'))
    if v[13]<0.3 and v[14]<0.1: tags.append(('STRONGLY-CLUSTERED',f'bal={v[13]:.2f}'))
    elif v[15]>3: tags.append(('MULTI-COMMUNITY',f'{int(v[15])} near-zero'))
    if v[10]>0.5: tags.append(('LEVEL-REPULSION',f'<r>={v[10]:.3f}'))
    if v[17]>0.1: tags.append(('FRAGILE',f'eff_R={v[17]:.4f}'))
    if not tags: tags.append(('GENERIC','No strong signature'))
    return tags

def critical_nodes(G, top_k=5):
    fi=G.eigenvector(1); sc=np.abs(fi)*G.degrees; rk=np.argsort(sc)[::-1]
    return [{'node':int(i),'label':G.labels[i],'degree':int(G.degrees[i]),'fiedler':float(fi[i]),'score':float(sc[i])} for i in rk[:top_k]]

if __name__=='__main__':
    print("="*72)
    print("GRAPH SPECTRAL ENGINE — DEMO")
    print("="*72)
    graphs={'ER sparse':GG.erdos_renyi(60,0.08,42),'ER dense':GG.erdos_renyi(60,0.3,42),'BA scale-free':GG.barabasi_albert(60,2,42),'WS small-world':GG.watts_strogatz(60,6,0.1,42),'SBM 3-comm':GG.stochastic_block([20,20,20],0.3,0.02,42),'Star':GG.star(30),'Path':GG.path(30),'Grid 6x10':GG.grid_2d(6,10),'Bot farm':GG.bot_farm(15,5,40,42)}
    print(f"\n{'─'*72}\n1. CLASSIFICATION\n{'─'*72}")
    results={}
    for name,G in graphs.items():
        vec=graph_features(G); tags=classify_graph(vec); results[name]={'vec':vec,'tags':tags,'graph':G}
        print(f"\n  {name:>16} (N={G.N},E={G.total_edges}): {', '.join(t[0] for t in tags)}")
        for t,d in tags: print(f"    {t:>20}: {d}")
    print(f"\n{'─'*72}\n2. KEY FEATURES\n{'─'*72}")
    kf=['algebraic_conn','gap_norm','degree_CV','spectral_radius','level_repulsion','partition_bal','eff_resistance','hub_dominance','health']
    disp=list(graphs.keys())[:7]
    print(f"\n  {'feature':>18}",end='')
    for n in disp: print(f" {n[:7]:>7}",end='')
    print()
    for fn in kf:
        j=FNAMES.index(fn); print(f"  {fn:>18}",end='')
        for n in disp: print(f" {results[n]['vec'][j]:7.3f}",end='')
        print()
    print(f"\n{'─'*72}\n3. CRITICAL NODES\n{'─'*72}")
    for name in ['BA scale-free','SBM 3-comm','Bot farm']:
        G=graphs[name]; crits=critical_nodes(G)
        print(f"\n  {name}:")
        for i,c in enumerate(crits): print(f"    #{i+1}: node {c['node']} ({c['label']}) deg={c['degree']} score={c['score']:.3f}")
    print(f"\n{'─'*72}\n4. BOT vs ORGANIC\n{'─'*72}")
    org=GG.erdos_renyi(60,0.1,99); vo=graph_features(org); vb=results['Bot farm']['vec']
    print(f"\n  {'feature':>18} {'organic':>10} {'bot':>10} {'diff':>8}")
    for j,fn in enumerate(FNAMES):
        d=abs(vo[j]-vb[j])/(abs(vo[j])+abs(vb[j])+1e-15)*2
        if d>0.3: print(f"  {fn:>18} {vo[j]:10.4f} {vb[j]:10.4f} {d:8.3f} !")
    t0=time.time()
    Gb=GG.erdos_renyi(100,0.1,1)
    for _ in range(100): graph_features(Gb)
    dt=time.time()-t0
    print(f"\n  Throughput (N=100): {100/dt:.0f}/s ({dt/100*1000:.1f}ms)")
    G5=GG.erdos_renyi(500,0.05,2)
    t0=time.time(); graph_features(G5); dt=time.time()-t0
    print(f"  N=500: {dt*1000:.0f}ms")
    print(f"\n{'='*72}\nENGINE READY\n{'='*72}")
