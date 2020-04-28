import math
import numpy as np
import networkx as nx
from scipy import sparse
from tqdm import tqdm

class FEATHER:
    def __init__(self, theta_max=2.5, eval_points=25, order=5):
        self.theta_max = theta_max
        self.eval_points = eval_points
        self.order = order

    def _create_D_inverse(self, graph):
        """
        Creating a sparse inverse degree matrix.
        Arg types:
            * **graph** *(NetworkX graph)* - The graph to be embedded.
        Return types:
            * **D_inverse** *(Scipy array)* - Diagonal inverse degree matrix.
        """
        index = np.arange(graph.number_of_nodes())
        values = np.array([1.0/graph.degree[node] for node in range(graph.number_of_nodes())])
        shape = (graph.number_of_nodes(), graph.number_of_nodes())
        D_inverse = sparse.coo_matrix((values, (index, index)), shape=shape)
        return D_inverse

    def _create_A_tilde(self, graph):
        """
        """
        A = nx.adjacency_matrix(graph, nodelist = range(graph.number_of_nodes()))
        D_inverse = self._create_D_inverse(graph) 
        A_tilde = D_inverse.dot(A)
        return A_tilde

    def fit(self, graph, X):
        theta = np.linspace(0.01, self.theta_max, self.eval_points)
        A_tilde = self._create_A_tilde(graph)
        X = np.outer(X, theta)
        X = X.reshape(graph.number_of_nodes(), -1)
        X = np.concatenate([np.cos(X), np.sin(X)], axis=1)
        feature_blocks = []
        for _ in range(self.order):
            X = A_tilde.dot(X)
            feature_blocks.append(X)
        self._X = np.concatenate(feature_blocks, axis=1)


    def get_embedding(self):
        return self._X


class FEATHER_G:
    def __init__(self, theta_max=2.5, eval_points=25, order=5, pooling="mean"):
        self.theta_max = theta_max
        self.eval_points = eval_points
        self.order = order
        self.pooling = pooling


    def _pooling(self, features):
        if self.pooling == "min":
            graph_embedding = np.min(features, axis=0)
        elif self.pooling == "max":
            graph_embedding = np.max(features, axis=0)
        else:
            graph_embedding = np.mean(features, axis=0)
        return graph_embedding

    def _fit_a_FEATHER(self, graph):
        sub_model = FEATHER(self.theta_max, self.eval_points, self.order)
        feature = np.array([math.log(graph.degree(node)+1) for node in range(graph.number_of_nodes())])
        feature = feature.reshape(-1, 1)
        sub_model.fit(graph, feature)
        features = sub_model.get_embedding()
        graph_embedding = self._pooling(features)
        return graph_embedding
    
    def fit(self, graphs):
        self._X = np.array([self._fit_a_FEATHER(graph) for graph in tqdm(graphs)])

    def get_embedding(self):
        return self._X