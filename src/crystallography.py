
import itertools, math
import numpy as np
def parse_matrix(text):
    rows=[]
    for line in str(text).strip().splitlines():
        nums=[float(x) for x in line.replace(',',' ').split()]
        if nums: rows.append(nums)
    M=np.array(rows,dtype=float)
    if M.shape!=(3,3): raise ValueError('Expected a 3x3 matrix: three rows and three columns.')
    return M
def normalize_rotation(R):
    U,_,Vt=np.linalg.svd(np.asarray(R,dtype=float)); M=U@Vt
    if np.linalg.det(M)<0: U[:,-1]*=-1; M=U@Vt
    return M
def axis_angle_from_rotation(R):
    R=normalize_rotation(R); c=max(-1.0,min(1.0,(np.trace(R)-1)/2)); angle=math.degrees(math.acos(c))
    if abs(angle)<1e-8: return 0.0, np.array([1.,0.,0.])
    axis=np.array([R[2,1]-R[1,2],R[0,2]-R[2,0],R[1,0]-R[0,1]]); norm=np.linalg.norm(axis)
    if norm<1e-12:
        vals,vecs=np.linalg.eig(R); idx=np.argmin(np.abs(vals-1)); axis=np.real(vecs[:,idx]); axis=axis/np.linalg.norm(axis)
    else: axis=axis/norm
    return angle, axis
def cubic_symmetry_operators():
    ops=[]
    for perm in itertools.permutations(range(3)):
        P=np.zeros((3,3))
        for i,j in enumerate(perm): P[i,j]=1
        for signs in itertools.product([-1,1], repeat=3):
            S=np.diag(signs)@P
            if round(np.linalg.det(S))==1: ops.append(S)
    unique=[]
    for S in ops:
        if not any(np.allclose(S,U) for U in unique): unique.append(S)
    return unique
def misorientation(g1,g2,sym_ops=None):
    g1=normalize_rotation(g1); g2=normalize_rotation(g2); sym_ops=sym_ops or [np.eye(3)]
    best=(999.,np.array([1.,0.,0.]))
    for S1 in sym_ops:
        for S2 in sym_ops:
            angle,axis=axis_angle_from_rotation(S1@g2@np.linalg.inv(g1)@S2)
            if angle<best[0]: best=(angle,axis)
    return best
def generate_variants(OR,parent_sym=None,daughter_sym=None,max_variants=48):
    OR=normalize_rotation(OR); parent_sym=parent_sym or cubic_symmetry_operators(); daughter_sym=daughter_sym or [np.eye(3)]; variants=[]
    for P in parent_sym:
        V=normalize_rotation(P@OR)
        if not any(any(np.allclose(D@V,E,atol=1e-6) for D in daughter_sym) for E in variants): variants.append(V)
        if len(variants)>=max_variants: break
    return variants
def matrix_to_markdown(M, precision=4):
    return '\n'.join(['| c1 | c2 | c3 |','|---:|---:|---:|']+['| '+' | '.join(f'{x:.{precision}f}' for x in row)+' |' for row in M])
def rotation_matrix_from_axis_angle(axis, angle_deg):
    a=np.array(axis,dtype=float); a=a/np.linalg.norm(a); x,y,z=a; t=math.radians(angle_deg); c=math.cos(t); s=math.sin(t); C=1-c
    return np.array([[c+x*x*C,x*y*C-z*s,x*z*C+y*s],[y*x*C+z*s,c+y*y*C,y*z*C-x*s],[z*x*C-y*s,z*y*C+x*s,c+z*z*C]])
