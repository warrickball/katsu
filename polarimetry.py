import numpy as np
import polutils as pol
import mueller as mul
import matplotlib.pyplot as plt
from numba import njit

def GenerateStokesArray(svector,npix):

    polarray = np.ones([npix,npix,4])
    polarray[:,:,0] = svector[0]
    polarray[:,:,1] = svector[1]
    polarray[:,:,2] = svector[2]
    polarray[:,:,3] = svector[3]

    return polarray

def GenerateMuellerMatrixArray(mueller,npix):
    """
    npix is raveled npix, for a square grid of side dimension npix. the npix here = npix**2
    """

    marray = np.ones([4,4,npix])
    marray *= mueller

def PropagateThroughMuellerSystem(sarray,Msys):
    sout = Msys @ sarray
    return sout

def StokesAnalyzer(analyzervector,stokes):
    return np.dot(analyzervector,stokes)

def DualTetrahedronPolarizations():

    v1 = np.array([1,1,0,-1/np.sqrt(2)])
    v2 = np.array([1,-1,0,-1/np.sqrt(2)])
    v3 = np.array([1,0,1,1/np.sqrt(2)])
    v4 = np.array([1,0,-1,1/np.sqrt(2)])

    # v1 = np.array([1,1,0,0])
    # v2 = np.array([1,-1/3,2*np.sqrt(3)/3,0])
    # v3 = np.array([1,-1/3,-np.sqrt(2)/3,np.sqrt(2/3)])
    # v4 = np.array([1,-1/3,-np.sqrt(2)/3,-np.sqrt(2/3)])

    # Check uniqueness

    return v1,v2,v3,v4

def StokesSinusoid(nmeas,a0,b2,a4,b4):
    return a0 + b2*np.sin(2*nmeas) + a4*np.cos(4*nmeas) + b4*np.sin(4*nmeas)

def FullStokesPolarimeterMeasurement(Sin,nmeas):

    from scipy.optimize import curve_fit
    import matplotlib.pyplot as plt
    
    # This is a rotating retarder mueller matrix
    Wmat = np.zeros([4,nmeas])
    Pmat = np.zeros([nmeas])
    wcount = 0

    # Retarder needs to rotate 2pi, break up by nmeas
    th = np.linspace(0,2*np.pi,nmeas)
    thp = np.linspace(0,2*np.pi,101)

    for i in range(nmeas):

        # Mueller Matrix of analyzer
        M = mul.LinearPolarizer(0) @ mul.LinearRetarder(th[i],np.pi/2)

        # The top row is the analyzer vector
        analyzer = M[0,0:4]

        # Record the power
        Pmat[i] = np.dot(analyzer,Sin)


    popt,pcov = curve_fit(StokesSinusoid,
                          th,
                          Pmat,
                          p0 = (1,1,1,1))

    a0 = popt[0]
    b2 = popt[1]
    a4 = popt[2]
    b4 = popt[3]

    sineval = StokesSinusoid(thp,a0,b2,a4,b4)

    # plt.figure()
    # plt.title('Flux Measurements')
    # plt.scatter(th,Pmat,label='Irradiance Measurements',marker='*')
    # plt.plot(thp,sineval,linestyle='dashdot',label='Curve-fit Sinusoid')
    # plt.legend()
    # plt.show()

    # Compute the Stokes Vector
    S0 = 2*(a0 - a4)
    S1 = 4*a4
    S2 = 4*b4
    S3 = -2*b2

    return np.array([S0,S1,S2,S3])

def FullStokesPolarimeter(Sarray,nmeas):

    dim = Sarray.shape[0]
    Sout = np.zeros(Sarray.shape)

    for ijk in range(dim):
        for lmn in range(dim):

            Sin = Sarray[ijk,lmn,:]

            Sout[ijk,lmn,:] = FullStokesPolarimeterMeasurement(Sin,nmeas)

    return Sout

def PlotStokesArray(Sarray):

    dim = Sarray.shape[0]

    x = np.linspace(-1,1,dim)
    x,y = np.meshgrid(x,x)

    vmin = -1
    vmax = 1

    plt.figure(figsize=[20,5])
    plt.subplot(141)
    plt.title('S0')
    plt.imshow(Sarray[:,:,0],vmin=vmin,vmax=vmax)
    plt.colorbar()

    plt.subplot(142)
    plt.title('S1')
    plt.imshow(Sarray[:,:,1],vmin=vmin,vmax=vmax)
    plt.colorbar()

    plt.subplot(143)
    plt.title('S2')
    plt.imshow(Sarray[:,:,2],vmin=vmin,vmax=vmax)
    plt.colorbar()

    plt.subplot(144)
    plt.title('S3')
    plt.imshow(Sarray[:,:,3],vmin=vmin,vmax=vmax)
    plt.colorbar()
    plt.tight_layout()
    plt.show()

def AddNoise(fluxmap):
    return




def DualTetrahedronPolarimeter(mueller):

    print('Mueller Matrix to Reconstruct')
    print(mueller)

    v1,v2,v3,v4 = DualTetrahedronPolarizations()

    polstates = [v1,v2,v3,v4]

    # Test np.ravel for mueller matrices
    M00 = mueller[0,0]
    M01 = mueller[0,1]
    M02 = mueller[0,2]
    M03 = mueller[0,3]

    M10 = mueller[1,0]
    M11 = mueller[1,1]
    M12 = mueller[1,2]
    M13 = mueller[1,3]

    M20 = mueller[2,0]
    M21 = mueller[2,1]
    M22 = mueller[2,2]
    M23 = mueller[2,3]

    M30 = mueller[3,0]
    M31 = mueller[3,1]
    M32 = mueller[3,2]
    M33 = mueller[3,3]

    Wmat = np.zeros([16,16])
    Pmat = np.zeros([16])
    wcount = 0

    for ijk in range(4): # the analyzer
        for lmn in range(4): # the source

            # Separate 16 Mueller Elements
            input = polstates[lmn]
            analyzer = polstates[ijk]

            # Generate Final Power Measurement
            P = analyzer @ mueller @ np.transpose(input)

            # Polarimetric Data Reduction Matrix Element
            # Wmat[wcount,0] = M00*input[0]*analyzer[0]
            # Wmat[wcount,1] = M01*input[1]*analyzer[1]
            # Wmat[wcount,2] = M02*input[2]*analyzer[2]
            # Wmat[wcount,3] = M03*input[3]*analyzer[3]

            # Wmat[wcount,4] = M10*input[0]*analyzer[0]
            # Wmat[wcount,5] = M11*input[1]*analyzer[1]
            # Wmat[wcount,6] = M12*input[2]*analyzer[2]
            # Wmat[wcount,7] = M13*input[3]*analyzer[3]

            # Wmat[wcount,8] = M20*input[0]*analyzer[0]
            # Wmat[wcount,9] = M21*input[1]*analyzer[1]
            # Wmat[wcount,10] = M22*input[2]*analyzer[2]
            # Wmat[wcount,11] = M23*input[3]*analyzer[3]

            # Wmat[wcount,12] = M30*input[0]*analyzer[0]
            # Wmat[wcount,13] = M31*input[1]*analyzer[1]
            # Wmat[wcount,14] = M32*input[2]*analyzer[2]
            # Wmat[wcount,15] = M33*input[3]*analyzer[3]

            # Try the Kronecker Product
            Wmat[wcount,:] = np.kron(analyzer,input)

            Pmat[wcount] = P
            wcount += 1

    print('rank=',np.linalg.matrix_rank((Wmat)))
    print(Wmat)
    Mout = np.linalg.pinv(Wmat) @ np.transpose(Pmat)

    return Mout


    

    



    # v1a = v1
    # v2a = v2
    # v3a = v3
    # v4a = v4 

    # v1in = np.transpose(v1)
    # v2in = np.transpose(v2)
    # v3in = np.transpose(v3)
    # v4in = np.transpose(v4)

    # v1out = mueller @ v1in
    # v2out = mueller @ v2in
    # v3out = mueller @ v3in
    # v4out = mueller @ v4in
    
    # P1 = np.dot(v1,v1out)
    # P2 = np.dot(v1,v2out)
    # P3 = np.dot(v1,v3out)
    # P4 = np.dot(v1,v4out)

    # P5 = np.dot(v2,v1out)

def ConstructPolReductionMatrix(measurements):



    return




    