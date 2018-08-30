from math import ceil, floor, factorial, log2
import numpy as np


class __Lazy__:
    """ 惰性求值 """
    def __init__(self, func):
        self.func = func
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = self.func(instance)
        setattr(instance, self.func.__name__, value)
        return value


class Facet:
    """ 记录Facet信息的类 """
    def __init__(self, normal: tuple, v1: tuple, v2: tuple, v3: tuple):
        self.normal = normal  # 三角面的外法向量
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3
    
    @__Lazy__
    def serialize(self) -> str:
        " 序列化 "
        lines, sps = '', '    '
        nx, ny, nz = self.normal
        lines += f"{sps}facet normal {nx:#e} {ny:#e} {nz:#e}\n"
        lines += f"{sps*2}outer loop\n"
        lines += f"{sps*3}vertex {self.v1[0]:#e} {self.v1[1]:#e} {self.v1[2]:#e}\n"
        lines += f"{sps*3}vertex {self.v2[0]:#e} {self.v2[1]:#e} {self.v2[2]:#e}\n"
        lines += f"{sps*3}vertex {self.v3[0]:#e} {self.v3[1]:#e} {self.v3[2]:#e}\n"
        lines += f"{sps*2}endloop\n"
        lines += f"{sps}endfacet\n"
        return lines


class Solid:
    """ 立体类 """
    def __str__(self):
        _ = len(self.Facets)
        info1 = f"'{self.name}' with {_} facets" 
        info2 = f", which can save about {log2(factorial(_)):#.1f} bits."
        return info1 + info2
    
    def __init__(self, STLfile=None):
        self.name = None      # 立体名
        self.file = STLfile   # STL文件
        self.Facets = []      # 三角面
        self.facetsID = {}    # 面索引映射
        self.vertex = None    # 顶点
        self.eigvec = None    # 三维特征向量
        self.PCA_vertex = None  # PCA空间中的顶点

        if STLfile:
            self.read_file(STLfile)

    def get_vertex(self, update=False):
        if not update:
            return self.vertex
        X = []
        for facet in self.Facets:
            X.append((facet.v1[0], facet.v1[1], facet.v1[2]))
            X.append((facet.v2[0], facet.v2[1], facet.v2[2]))
            X.append((facet.v3[0], facet.v3[1], facet.v3[2]))
        self.vertex = np.array(X)

        return self.vertex

    def to_PCA_space(self):
        """ 通过线性变换投射到PCA空间 """
        if self.vertex is None:
            self.get_vertex(update=True)
        cov_data = np.cov(self.vertex.T)
        _, self.eigvec = np.linalg.eig(cov_data)
        self.PCA_vertex = np.dot(self.vertex, self.eigvec)
        return self.PCA_vertex

    def read_file(self, fileName: str):
        """ 从指定文件读取立体的信息 """
        with open(fileName) as f:
            if not f.readable():
                self.file = fileName
                print("Failed to read STL file!")
                return None
            lines = f.readlines()

        normal, vertexs = None, []
        cntf, i, lines_num = 0, 0, len(lines)

        while i < lines_num:
            line = lines[i].strip().split(" ")
            if line[0] == "solid":
                self.name = line[1]
            elif line[0] == "facet":
                normal = (float(line[2]), float(line[3]), float(line[4]))
            elif line[0] == "vertex":
                info = float(line[1]), float(line[2]), float(line[3])
                vertexs.append(info)
            elif line[0] == "endloop":
                if len(vertexs) != 3:
                    print("Oops! One facet not 3 vertexs!")
                    return
            elif line[0] == "endfacet":
                f = Facet(normal, vertexs[0], vertexs[1], vertexs[2])
                self.facetsID[cntf] = f
                self.Facets.append(f)
                cntf += 1
                vertexs = []
            i += 1


def show_solid(solid: Solid, PCA=False):
    """ 以普通或者PCA视角显示当前的立体 """
    if PCA:
        if solid.PCA_vertex is None:
            solid.to_PCA_space()
        data = solid.PCA_vertex
    else:
        if solid.vertex is None:
            solid.get_vertex(True)
        data = solid.vertex
    
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    
    # 所有顶点的(x, y, z) 坐标
    x = data[:, 0:1].reshape(-1)
    y = data[:, 1:2].reshape(-1)
    z = data[:, 2:3].reshape(-1)

    fig = plt.figure()
    ax = fig.gca(projection="3d")
    ax.plot_trisurf(x, y, z)
    plt.show()


def get_ref(solid: Solid) -> list:
    """ 根据三角面在PCA空间中的排列给出ref。O(nlog(n)) """
    if hasattr(solid, 'ref'):
        return solid.ref
    
    if solid.eigvec is None:
        solid.to_PCA_space()

    _facets = []
    for i, facet in enumerate(solid.Facets):
        corex = (facet.v1[0] + facet.v2[0] + facet.v3[0]) / 3
        corey = (facet.v1[1] + facet.v2[1] + facet.v3[1]) / 3
        corez = (facet.v1[2] + facet.v2[2] + facet.v3[2]) / 3
        core = np.array([[corex, corey, corez]])
        # 得到 PCA中的面中心点，格式：(中心坐标，原始面索引)
        _facets.append((np.dot(core, solid.eigvec), i))

    # 根据中心点(x,y,z)升序排列
    _facets.sort(key=lambda f: (f[0][0][0], f[0][0][1], f[0][0][2]))

    ref = [0] * (i+1)
    for i, facet in enumerate(_facets): # 已经排序后的Facets
        ref[i] = facet[1]
    
    solid.ref = ref
    return ref


def ref2ord(ref: list, msg: str) -> list:
    """ ref序列转ord加密序列，若加密数据小于容量，对数据补0。 """
    _ref, _ord = ref.copy(), []
    Id, q = 0, len(_ref)
    # 末尾补‘0’
    for bit in msg + "0"*int(np.log2(len(_ref))):
        if len(_ref) == 1:
            break
        if bit == "1":
            Id, q = Id + ceil(q/2), floor(q/2)
        else:
            q -= floor(q/2)
        if q == 1:
            _ord.append(_ref[Id])
            _ref[Id] = _ref[-1]
            _ref.pop()
            Id = 0
            q = len(_ref)
    _ord.append(_ref[0])
    _ref = _ref[1:]
    if len(_ref):
        _ref.reverse()
        _ord += _ref
    return _ord


def ord2S(ref: list, ord: list=None) -> str:
    """ 使用ref序列解密ord加密序列。注意：结尾可能有多余的0，需要截断。
    ord为None表示提取水印。"""
    if ord is None:
        _ord = [i for i in range(len(ref))]
    else:
        _ord = ord.copy()
    _ref = ref.copy()
    S = ''
    for item in _ord:
        Id, q = _ref.index(item), len(_ref)
        _ref[Id] = _ref[-1]
        _ref.pop()
        while q > 1:
            if Id >= ceil(q / 2):
                S += '1'
                Id -= ceil(q / 2)
                q = floor(q / 2)
            else:
                S += '0'
                q = ceil(q / 2)
    return S


def watermark(solid: Solid, ord: list, fileName:str=None):
    """ 根据ord序列重排列三角面并写入文件 """
    if fileName is None:
        fileName = f"{solid.name}_.txt"
    
    with open(fileName, 'w') as f:
        f.write(f'solid {solid.name}\n')
        for Id in ord:
            facet = solid.facetsID[Id]
            f.writelines(facet.serialize)
        f.write('endsolid')
    
    print('done!')
