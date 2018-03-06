import numpy as np
import sqaod
from sqaod.common import checkers
import formulas
import cpu_bg_annealer as cext


class BipartiteGraphAnnealer :

    _cext = cext;
    
    def __init__(self, b0, b1, W, optimize, dtype, prefdict) : # n_trotters
        self.dtype = dtype
        self._cobj = cext.new_annealer(dtype)
        if not W is None :
            self.set_problem(b0, b1, W, optimize)
        self.set_preferences(prefdict)
            
    def __del__(self) :
        cext.delete_annealer(self._cobj, self.dtype)
        
    def seed(self, seed) :
        cext.seed(self._cobj, seed, self.dtype)
            
    def set_problem(self, b0, b1, W, optimize = sqaod.minimize) :
        checkers.bipartite_graph.qubo(b0, b1, W)
        b0, b1, W = sqaod.clone_as_ndarray_from_vars([b0, b1, W], self.dtype)
        cext.set_problem(self._cobj, b0, b1, W, optimize, self.dtype);
        self._optimize = optimize

    def get_optimize_dir(self) :
        return self._optimize

    def get_problem_size(self) :
        return cext.get_problem_size(self._cobj, self.dtype)

    def set_preferences(self, prefdict=None, **prefs) :
        if not prefdict is None :
            cext.set_preferences(self._cobj, prefdict, self.dtype)
        cext.set_preferences(self._cobj, prefs, self.dtype)

    def get_preferences(self) :
        return cext.get_preferences(self._cobj, self.dtype)
        
    def get_E(self) :
        return self._E

    def get_x(self) :
        return cext.get_x(self._cobj, self.dtype)

    def set_x(self, x0, x1) :
        cext.set_x(self._cobj, x0, x1, self.dtype)

    # Ising model / spins
    
    def get_hJc(self) :
        N0, N1 = self.get_problem_size()
        h0 = np.ndarray((N0), self.dtype);
        h1 = np.ndarray((N1), self.dtype);
        J = np.ndarray((N1, N0), self.dtype);
        c = np.ndarray((1), self.dtype)
        cext.get_hJc(self._cobj, h0, h1, J, c, self.dtype)
        return h0, h1, J, c[0]
            
    def get_q(self) :
        return cext.get_q(self._cobj, self.dtype)

    def randomize_q(self) :
        cext.randomize_q(self._cobj, self.dtype)

    def calculate_E(self) :
        cext.calculate_E(self._cobj, self.dtype)

    def init_anneal(self) :
        cext.init_anneal(self._cobj, self.dtype)
        
    def anneal_one_step(self, G, kT) :
        cext.anneal_one_step(self._cobj, G, kT, self.dtype)

    def fin_anneal(self) :
        cext.fin_anneal(self._cobj, self.dtype)
        N0, N1 = self.get_problem_size()
        prefs = self.get_preferences()
        m = prefs['n_trotters']
        self._E = np.empty((m), self.dtype)
        cext.get_E(self._cobj, self._E, self.dtype)

        
def bipartite_graph_annealer(b0 = None, b1 = None, W = None, \
                             optimize = sqaod.minimize, \
                             dtype = np.float64, **prefs) :
    return BipartiteGraphAnnealer(b0, b1, W, optimize, dtype, prefs)


if __name__ == '__main__' :
    N0 = 40
    N1 = 40
    m = 20
    
    np.random.seed(0)
            
    W = np.random.random((N1, N0)) - 0.5
    b0 = np.random.random((N0)) - 0.5
    b1 = np.random.random((N1)) - 0.5

    an = bipartite_graph_annealer(b0, b1, W, sqaod.minimize, n_trotters=m)
    
    Ginit = 5
    Gfin = 0.01
    kT = 0.02
    tau = 0.99
    n_repeat = 10

    for loop in range(0, n_repeat) :
        an.init_anneal()
        an.randomize_q()
        G = Ginit
        while Gfin < G :
            an.anneal_one_step(G, kT)
            G = G * tau
        an.fin_anneal()

        E = an.get_E()
        x = an.get_x()
        print E.shape, E
        print x