import numpy as np
from .katsu_math import broadcast_outer


def _empty_stokes(shape):
    """Returns an empty array to populate with Stokes vector elements.

    Parameters
    ----------
    shape : list
        shape to prepend to the stokes array. shape = [32,32] returns
        an array of shape [32,32,4,1] where the vector is assumed to be in the
        last indices. Defaults to None, which returns a 4x1 array.

    Returns
    -------
    numpy.ndarray
        The zero array of specified shape

    Notes
    -----
    The structure of this function was taken from prysm.x.polarization,
    which was written by Jaren Ashcraft
    """

    if shape is None:

        shape = (4, 1)

    else:

        shape = (*shape, 4, 1)

    return np.zeros(shape)


def stokes_from_parameters(I, Q, U, V, shape=None):
    """Generates a stokes vector array from the stokes parameters

    Parameters
    ----------
    I : float or numpy.ndarray
        Stokes parameter corresponding to intensity, must be float
        or numpy.ndarray with shape == `shape`
    Q : float or numpy.ndarray
        Stokes parameter corresponding to H/V polarization, must be float
        or numpy.ndarray with shape == `shape`
    U : float or numpy.ndarray
        Stokes parameter corresponding to +45/-45 polarization, must be float
        or numpy.ndarray with shape == `shape`
    V : float or numpy.ndarray
        Stokes parameter corresponding to RHC/LHC polarization, must be float
        or numpy.ndarray with shape == `shape`
    shape : list
        shape to prepend to the stokes array. shape = [32,32] returns
        an array of shape [32,32,4,1] where the vector is assumed to be in the
        last indices. Defaults to None, which returns a 4x1 array.

    Returns
    -------
    numpy.ndarray
        array of stokes vectors
    """

    stokes = _empty_stokes(shape)
    stokes[..., 0, 0] = I
    stokes[..., 1, 0] = Q
    stokes[..., 2, 0] = U
    stokes[..., 3, 0] = V

    return stokes


def _empty_mueller(shape):
    """Returns an empty array to populate with Mueller matrix elements.

    Parameters
    ----------
    shape : list
        shape to prepend to the mueller matrix array. shape = [32,32] returns
        an array of shape [32,32,4,4] where the matrix is assumed to be in the
        last indices. Defaults to None, which returns a 4x4 array.

    Returns
    -------
    numpy.ndarray
        The zero array of specified shape

    Notes
    -----
    The structure of this function was taken from prysm.x.polarization,
    which was written by Jaren Ashcraft
    """

    if shape is None:

        shape = (4, 4)

    else:

        shape = (*shape, 4, 4)

    return np.zeros(shape)


def mueller_rotation(angle, shape=None):
    """returns a Mueller rotation matrix

    Parameters
    ----------
    angle : float, or numpy.darray
        angle of the rotation w.r.t. horizontal in radians. If numpy
        array, must be the same shape as `shape`
    shape : list, optional
        shape to prepend to the mueller matrix array, see `_empty_mueller`. by
        default None

    Returns
    -------
    numpy.ndarray
        Mueller rotation matrix
    """

    M = _empty_mueller(shape)
    cos2theta = np.cos(2 * angle)
    sin2theta = np.sin(2 * angle)

    if M.ndim > 2:
        cos2theta = np.broadcast_to(cos2theta, [*M.shape[:-2]])
        sin2theta = np.broadcast_to(sin2theta, [*M.shape[:-2]])

    M[..., 0, 0] = 1
    M[..., -1, -1] = 1

    M[..., 1, 1] = cos2theta
    M[..., 2, 2] = cos2theta

    M[..., 1, 2] = sin2theta
    M[..., 2, 1] = -sin2theta

    return M


def linear_polarizer(a, shape=None):
    """returns a homogenous linear polarizer

    Parameters
    ----------
    a : float, or numpy.darray
        angle of the transmission axis w.r.t. horizontal in radians. If numpy
        array, must be the same shape as `shape`
    shape : list, optional
        shape to prepend to the mueller matrix array, see `_empty_mueller`. by
        default None

    Returns
    -------
    numpy.ndarray
        linear polarizer array
    """

    # returns zeros
    M = _empty_mueller(shape)

    ones = np.ones_like(a)
    cos2a = np.cos(2 * a)
    sin2a = np.sin(2 * a)

    # fist row
    M[..., 0, 0] = ones
    M[..., 0, 1] = cos2a
    M[..., 0, 2] = sin2a

    # second row
    M[..., 1, 0] = cos2a
    M[..., 1, 1] = cos2a**2
    M[..., 1, 2] = cos2a * sin2a

    # third row
    M[..., 2, 0] = sin2a
    M[..., 2, 1] = cos2a * sin2a
    M[..., 2, 2] = sin2a**2

    M /= 2

    return M


def linear_retarder(a, r, shape=None):
    """returns a homogenous linear retarder

    Parameters
    ----------
    a : float, or numpy.ndarray
        angle of the fast axis w.r.t. horizontal in radians. If numpy array,
        must be 1D
    r : float, or numpy.ndarray
        retardance in radians. If numpy array, must be the same shape as
        `shape`
    shape : list, optional
        shape to prepend to the mueller matrix array, see `_empty_mueller`.
        by default None

    Returns
    -------
    numpy.ndarray
        linear retarder array
    """

    # returns zeros
    M = _empty_mueller(shape)

    # make sure everything is the right size
    if M.ndim > 2:
        if isinstance(a, np.ndarray):
            a = a  # leave it alone
        else:
            a = np.broadcast_to(a, [*M.shape[:-2]])

        r = np.broadcast_to(r, [*M.shape[:-2]])

    # First row
    M[..., 0, 0] = 1.

    # second row
    M[..., 1, 1] = np.cos(2*a)**2 + np.cos(r)*np.sin(2*a)**2
    M[..., 1, 2] = (1-np.cos(r))*np.cos(2*a)*np.sin(2*a)
    M[..., 1, 3] = -np.sin(r)*np.sin(2*a)

    # third row
    M[..., 2, 1] = M[..., 1, 2]
    M[..., 2, 2] = np.cos(r)*np.cos(2*a)**2 + np.sin(2*a)**2
    M[..., 2, 3] = np.cos(2*a)*np.sin(r)

    M[..., 3, 1] = -1 * M[..., 1, 3]
    M[..., 3, 2] = -1 * M[..., 2, 3]
    M[..., 3, 3] = np.cos(r)

    return M


def linear_diattenuator(a, Tmin, Tmax=1, shape=None):
    """returns a homogenous linear diattenuator

    CLY 6.54

    Parameters
    ----------
    a : float, or numpy.ndarray
        angle of the transmission axis w.r.t. horizontal in radians. If numpy
        array, must be the same shape as `shape`
    Tmin : float, or numpy.ndarray
        Minimum transmission of the state orthogonal to maximum transmission. 
        If numpy array, must be the same shape as `shape`
    shape : list, optional
        shape to prepend to the mueller matrix array, see `_empty_mueller`. 
        By default None

    Returns
    -------
    numpy.ndarray
        linear diattenuator array
    """

    # returns zeros
    M = _empty_mueller(shape)

    # make sure everything is the right size
    if M.ndim > 2:
        a = np.broadcast_to(a, [*M.shape[:-2]])
        Tmin = np.broadcast_to(Tmin, [*M.shape[:-2]])

    A = Tmax + Tmin
    B = Tmax - Tmin
    C = 2 * np.sqrt(Tmax * Tmin)
    cos2a = np.cos(2 * a)
    sin2a = np.sin(2 * a)

    # first row
    M[..., 0, 0] = A
    M[..., 0, 1] = B*cos2a
    M[..., 0, 2] = B*sin2a

    # second row
    M[..., 1, 0] = M[..., 0, 1]
    M[..., 1, 1] = (A * cos2a**2) + (C * sin2a**2)
    M[..., 1, 2] = (A - C) * cos2a * sin2a

    # third row
    M[..., 2, 0] = M[..., 0, 2]
    M[..., 2, 1] = M[..., 1, 2]
    M[..., 2, 2] = (C * cos2a**2) + (A * sin2a**2)

    # fourth row
    M[..., 3, 3] = C

    # Apply Malus' law directly to the forehead
    M /= 2

    return M


def depolarizer(angle, a, b, c, shape=None):
    """returns a diagonal depolarizer

    Parameters
    ----------
    angle : float, or numpy.ndarray
        angle of the transmission axis w.r.t. horizontal in radians. If numpy
        array, must be the same shape as `shape`
    a : float or numpy.ndarray
        depolarization of Q
    a : float or numpy.ndarray
        depolarization of U
    a : float or numpy.ndarray
        depolarization of V
    shape : list, optional
        shape to prepend to the mueller matrix array, see `_empty_mueller`.
        By default None

    Returns
    -------
    _type_
        _description_
    """

    M = _empty_mueller(shape)
    M_rot_in = mueller_rotation(-angle, shape=shape)
    M_rot_out = mueller_rotation(angle, shape=shape)

    # make sure everything is the right size
    if M.ndim > 2:
        a = np.broadcast_to(a, [*M.shape[:-2]])
        b = np.broadcast_to(b, [*M.shape[:-2]])
        c = np.broadcast_to(c, [*M.shape[:-2]])

    M[..., 0, 0] = 1
    M[..., 1, 1] = a
    M[..., 2, 2] = b
    M[..., 3, 3] = c

    M = M_rot_out @ M @ M_rot_in

    return M


def decompose_diattenuator(M):
    """Decompose M into a diattenuator using the Polar decomposition

    from Lu & Chipman 1996 https://doi.org/10.1364/JOSAA.13.001106

    Parameters
    ----------
    M : numpy.ndarray
        Mueller Matrix to decompose

    Returns
    -------
    numpy.ndarray
        Diattenuator component of mueller matrix
    """

    # First, determine the diattenuator
    T = M[..., 0, 0]

    if M.ndim > 2:
        diattenuation_vector = M[..., 0, 1:] / T[..., np.newaxis]
    else:
        diattenuation_vector = M[..., 0, 1:] / T

    D = np.sqrt(np.sum(diattenuation_vector * diattenuation_vector, axis=-1))
    mD = np.sqrt(1 - D**2)

    if M.ndim > 2:
        diattenutation_norm = diattenuation_vector / D[..., np.newaxis]
    else:
        diattenutation_norm = diattenuation_vector / D

    DD = broadcast_outer(diattenutation_norm, diattenutation_norm)

    # create diattenuator
    I = np.identity(3)

    if M.ndim > 2:
        I = np.broadcast_to(I, [*M.shape[:-2], 3, 3])
        mD = mD[..., np.newaxis, np.newaxis]

    inner_diattenuator = mD * I + (1 - mD) * DD  # Eq. 19 Lu & Chipman

    Md = _empty_mueller(M.shape[:-2])

    # Eq 18 Lu & Chipman
    Md[..., 0, 0] = 1.
    Md[..., 0, 1:] = diattenuation_vector
    Md[..., 1:, 0] = diattenuation_vector
    Md[..., 1:, 1:] = inner_diattenuator

    if M.ndim > 2:
        Md = Md * T[..., np.newaxis, np.newaxis]
    else:
        Md = Md * T

    return Md


def decompose_retarder(M, return_all=False):
    """Decompose M into a retarder using the Polar decomposition

    from Lu & Chipman 1996 https://doi.org/10.1364/JOSAA.13.001106

    Note: this doesn't work if the diattenuation can be described by a pure
    polarizer, because the matrix is singular and therefore non-invertible

    Parameters
    ----------
    M : numpy.ndarray
        Mueller Matrix to decompose
    return_all : bool
        Whether to return the retarder and diattenuator vs just the retarder.
        Defaults to False, which returns both

    Returns
    -------
    numpy.ndarray
        Retarder component of mueller matrix
    """

    Md = decompose_diattenuator(M)

    # Then, derive the retarder
    Mr = M @ np.linalg.inv(Md)

    if return_all:
        return Mr, Md
    else:
        return Mr


def decompose_depolarizer(M, return_all=False):
    """Decompose M into a depolarizer using the Polar decomposition

    from Lu & Chipman 1996 https://doi.org/10.1364/JOSAA.13.001106

    Parameters
    ----------
     M : numpy.ndarray
        Mueller Matrix to decompose
    return_all : bool
        Whether to return the depolaarizer, retarder and diattenuator
        vs just the retarder. Defaults to False, which returns just the
        depolarizer

    Returns
    -------
    numpy.ndarray or arrays
        Decomposed mueller matrix
    """

    # NOTE: The result is not a pure retarder, but uses the same operation
    if return_all:
        Mp, M_diattenuator = decompose_retarder(M, return_all=return_all)

    else:
        Mp = decompose_retarder(M, return_all=return_all)

    Pdelta = Mp[..., 1:, 0]
    mp = Mp[..., 1:, 1:]

    # Eq 52 Lu & Chipman
    mm = mp @ np.swapaxes(mp, -2, -1)
    det_mm = np.linalg.det(mm)

    # TODO: Need way of efficiently computing the eigenvalues of mm
    evals = np.linalg.eigvals(mm)

    e1 = np.sqrt(evals[..., 0])
    e2 = np.sqrt(evals[..., 1])
    e3 = np.sqrt(evals[..., 2])

    if M.ndim > 2:
        e1 = e1[..., np.newaxis, np.newaxis]
        e2 = e2[..., np.newaxis, np.newaxis]
        e3 = e3[..., np.newaxis, np.newaxis]

    e1e2 = e1 * e2
    e2e3 = e2 * e3
    e3e1 = e3 * e1
    e1e2e3 = e1 * e2 * e3

    # create an identity
    I = np.eye(3)
    I = np.broadcast_to(I, [*mm.shape[:-2], *I.shape])

    lhs = mm + (e1e2 + e2e3 + e3e1)*I
    rhs = (e1 + e2 + e3)*mm + e1e2e3*I

    # Cases for postitive / negative determinant
    md = np.zeros_like(mm)
    md[det_mm < 0.] = (-np.linalg.inv(lhs) @ rhs)[det_mm < 0.]
    md[det_mm > 0.] = (np.linalg.inv(lhs) @ rhs)[det_mm > 0.]

    # populate the depolarizer
    M_depolarizer = np.zeros_like(M)
    M_depolarizer[..., 1:, 0] = Pdelta
    M_depolarizer[..., 1:, 1:] = md
    M_depolarizer[..., 0, 0,] = 1.

    if return_all:

        # compute the retarder
        M_retarder = np.linalg.inv(M_depolarizer) @ Mp

        return M_depolarizer, M_retarder, M_diattenuator

    else:
        return M_depolarizer


def mueller_to_jones(M):
    """Converts Mueller matrix to a relative Jones matrix. Phase aberration is
    relative to the Pxx component.

    Returns
    -------
    J : 2x2 ndarray
        Jones matrix from Mueller matrix calculation
    """

    "CLY Eq. 6.112"
    "Untested"

    pxx = np.sqrt((M[0, 0] + M[0, 1] + M[1, 0] + M[1, 1]) / 2)
    pxy = np.sqrt((M[0, 0] - M[0, 1] + M[1, 0] - M[1, 1]) / 2)
    pyx = np.sqrt((M[0, 0] + M[0, 1] - M[1, 0] - M[1, 1]) / 2)
    pyy = np.sqrt((M[0, 0] - M[0, 1] - M[1, 0] + M[1, 1]) / 2)

    txx = 0  # This phase is not determined
    txy = -np.arctan2((M[0, 3] + M[1, 3]), (M[0, 2] + M[1, 2]))
    tyx = np.arctan2((M[3, 0] + M[3, 1]), (M[2, 0] + M[2, 1]))
    tyy = np.arctan2((M[3, 2] - M[2, 3]), (M[2, 2] + M[3, 3]))

    J = np.array(
        [
            [pxx * np.exp(-1j * txx), pxy * np.exp(-1j * txy)],
            [pyx * np.exp(-1j * tyx), pyy * np.exp(-1j * tyy)],
        ]
    )

    return J


# The depreciated parent functions from when katsu was Observatory-Polarimetry
def _linear_polarizer(a):
    """generates an ideal polarizer, depreciated

    CLY Eq 6.37
    checked!

    Parameters
    ----------
    a : float
       angle of transmission axis w.r.t. horizontal in radians

    Returns
    -------
    numpy.ndarray
        Mueller Matrix for the linear polarizer
    """

    ones = np.ones_like(a)
    zeros = np.zeros_like(a)

    M01 = np.cos(2*a)
    M02 = np.sin(2*a)

    M10 = np.cos(2*a)
    M11 = np.cos(2*a)**2
    M12 = np.cos(2*a)*np.sin(2*a)
    
    M20 = np.sin(2*a)
    M21 = np.cos(2*a)*np.sin(2*a)
    M22 = np.sin(2*a)**2

    M = 0.5*np.array([[ones,M01,M02,zeros],
                    [M10,M11,M12,zeros],
                    [M20,M21,M22,zeros],
                    [zeros,zeros,zeros,zeros]])
    
    if M.ndim > 2:
        for _ in range(M.ndim - 2):
            M = np.moveaxis(M,-1,0)

    return M 

def _linear_retarder(a,r):
    """Generates an ideal retarder

    Parameters
    ----------
    a : float
        angle of fast axis w.r.t. horizontal in radians
    r : float
        retardance in radians

    Returns
    -------
    numpy.ndarray
        Mueller Matrix for Linear Retarder
    """

    ones = np.ones_like(a)
    zeros = np.zeros_like(a)
    r = np.full_like(a,r)

    M11 = np.cos(2*a)**2 + np.cos(r)*np.sin(2*a)**2 # checked
    M12 = (1-np.cos(r))*np.cos(2*a)*np.sin(2*a) # checked
    M13 = -np.sin(r)*np.sin(2*a) # checked

    M21 = M12 # checked but uncertain
    M22 = np.cos(r)*np.cos(2*a)**2 + np.sin(2*a)**2 # checked
    M23 = np.cos(2*a)*np.sin(r) # checked

    M31 = -M13 # checked
    M32 = -M23 # checked
    M33 = np.cos(r) # checked

    M = np.array([[ones,zeros,zeros,zeros],
                [zeros,M11,M12,M13],
                [zeros,M21,M22,M23],
                [zeros,M31,M32,M33]])

    if M.ndim > 2:
        for _ in range(M.ndim - 2):
            M = np.moveaxis(M,-1,0)

    return M

def _linear_diattenuator(a,Tmin):
    """Generates an ideal diattenuator

    Parameters
    ----------
    a : float
        angle of the high-transmission axis w.r.t. horizontal in radians
    Tmin : float
        fractional transmission of the low-transmission axis

    Returns
    -------
    numpy.ndarray
        Mueller Matrix for Linear Diattenuator
    """

    A = 1 + Tmin
    B = 1 - Tmin
    C = 2*np.sqrt(Tmin)

    zeros = np.zeros_like(a)

    M01 = B*np.cos(2*a)
    M02 = B*np.sin(2*a)

    M10 = M01
    M11 = A*np.cos(2*a)**2 + C*np.sin(2*a)**2
    M12 = (A-C) * np.cos(2*a) * np.sin(2*a)
    
    M20 = M02 
    M21 = M12
    M22 = C*np.cos(2*a)**2 + A*np.sin(2*a)**2

    M = np.array([[A,M01,M02,zeros],
                  [M10,M11,M12,zeros],
                  [M20,M21,M22,zeros],
                  [zeros,zeros,zeros,C]]) / 2
    
    if M.ndim > 2:
        for _ in range(M.ndim-2):
            M = np.moveaxis(M,-1,0)

    return M



