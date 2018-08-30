# watermark_in_STL
Write information into STL file

## main.py
This file is used to test the correctness of 'server.py' and 'solidKit.py'.

## server.py
During the test phase...

Used for receiving and sending STL file.

## solidKit.py
The file contains mostly useful functions about this project, at least in my part.

### Facet & Solid
There are two classes: `Facet` and `Solid` in this file.

The former records information about Facets like vertexs and normal vector. In addition, there is also a funtion called 'serialize', which is used for generating information.

The latter contains the solid attributes like this
```python
self.name:        str         # solid name
self.file:        str         # STL file name
self.Facets:      list        # all facets
self.facetsID:    dict        # 面索引映射
self.vertex:      np.array    # Vertex coordinates
self.eigvec:      np.array    # 3-D feature vectors
self.PCA_vertex:  np.array    # Vertex in PCA space
```

### show_solid(solid: Solid, PCA=False)
Display the current stereo in a normal or PCA perspective.

### get_ref(solid: Solid) -> list
Giving reference sequences (ref) according to the arrangement of triangular polygons in PCA space.

### ref2ord(ref: list, msg: str) -> list
Convert the ref to cipher sequence (ord).

### ord2S(ref: list, ord: list=None) -> str
Decrypts the Ord cipher sequence using the ref sequence.

> The end may have an extra 0, which needs to be truncated.
> Ord is the none expression to extract the watermark.

### watermark(solid: Solid, ord: list, fileName:str=None)
Rearrange triangular faces and write files according to the Ord sequence.
