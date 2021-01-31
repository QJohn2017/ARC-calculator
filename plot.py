import numpy as np
import matplotlib
import matplotlib.pyplot as plt

matplotlib.rc('font', family='Times New Roman', size=10)
matplotlib.rc('axes', labelsize=10, labelpad=2)
matplotlib.rc('xtick', labelsize=8)
matplotlib.rc('ytick', labelsize=8)
matplotlib.rc('lines', linewidth=1.0, markersize=4.0)
matplotlib.rc('image', cmap='jet')

l_notion = ['s', 'p', 'd', 'f']

def plot_absorption_spectra():

    matplotlib.rc('figure', figsize=(3.54, 0.8), dpi=300)
    matplotlib.rc('figure.subplot', left=0.08, bottom=0.25,
                  right=0.99, top=0.96, wspace=0.15, hspace=0)

    data = np.loadtxt("absorption.dat")
    fig = plt.figure()
    ax = plt.axes()

    #### Data format of file "absorption.dat" ####
    # idx 0: n1 | idx 1: l1 | idx 2: j1 | idx 3: mj1
    # idx 4: n2 | idx 5: l2 | idx 6: j2 | idx 7: mj2
    # idx 8: frequency (THz)
    # idx 9: wavelength (nm)
    # idx 10: dipole moment (a0*e)

    for line in data:
        dipole = np.abs(line[10])
        freq = line[8]
        if dipole > 1e-8:
            if freq > 0:
                ax.vlines(np.log10(+freq), 0, dipole, colors='g', lw=0.2)
            else:
                ax.vlines(np.log10(-freq), 0, dipole, colors='g', lw=0.2)

    ax.set_xlim([-0.5228, 0.4771])
    ax.set_ylim([0, 450])
    ax.set_xlabel("Frequency (THz)")
    ax.set_ylabel("Dipole moment (a0*e)")
    plt.show()

def plot_spontaneous_transition_diagram():

    data_spon = np.loadtxt("spontaneous.dat")
    data_levl = np.loadtxt("levels.dat")

    #### Data format of file "spontaneous.dat" ####
    # idx 0: n_upper | idx 1: l_upper | idx 2: j_upper
    # idx 3: n_lower | idx 4: l_lower | idx 5: j_lower
    # idx 6: frequncy (THz)
    # idx 7: wavelength (nm)
    # idx 8: transition rate (a0*e)

    #### Data format of file "levels.dat" ####
    # idx 0: n | idx 1: l | idx 2: j
    # idx 3: energy (eV)
    # idx 4: lifetime (s^-1)

    fig = plt.figure()
    ax = plt.axes()

    # plot energy levels
    for levl in data_levl:
        num_l, energy, lifetime = int(levl[1]), levl[3], levl[4]
        if lifetime > 1e5:
            ax.hlines(energy, num_l-0.2, num_l+0.2, lw=5)
        else:
            ax.hlines(energy, num_l-0.2, num_l+0.2, lw=lifetime/2e3)
        ax.text(num_l+0.0, energy, "(%d%s%3.1f)" % (levl[0], l_notion[num_l], levl[2]))    

    for spon in data_spon:
        n_upper, l_upper, j_upper = spon[0], spon[1], spon[2] 
        n_lower, l_lower, j_lower = spon[3], spon[4], spon[5]
        E_upper = data_levl[(data_levl[:,0]==n_upper) & 
                            (data_levl[:,1]==l_upper) &
                            (data_levl[:,2]==j_upper)][0][3]
        E_lower = data_levl[(data_levl[:,0]==n_lower) & 
                            (data_levl[:,1]==l_lower) &
                            (data_levl[:,2]==j_lower)][0][3]
        rate = spon[8]
        if rate > 1e7:
            ax.plot([l_upper, l_lower], [E_upper, E_lower], lw=8)
        elif rate > 1e6 and rate <= 1e7:
            ax.plot([l_upper, l_lower], [E_upper, E_lower], lw=4)
        else:
            ax.plot([l_upper, l_lower], [E_upper, E_lower], lw=4*rate/1e6)
    ax.set_xlabel("l number")
    ax.set_ylabel("Energy (eV)")
    ax.set_title("Transition diagram of spontaneous radiation")
    plt.show()

# not yet completed - it will recursively visit all lower levels, some of which have already been plotted 
def plot_spontaneous_rate():
    
    data_spon = np.loadtxt("spontaneous.dat")
    data_levl = np.loadtxt("levels.dat")

    fig = plt.figure()
    ax = plt.axes()

    def plot_rate(n, l, j):

        data_upper = data_spon[(data_spon[:,0]==n) & (data_spon[:,1]==l) & (data_spon[:,2]==j)]
        if data_upper.size == 0:
            return

        lower_n_list, lower_l_list, lower_j_list = data_upper[:,3], data_upper[:,4], data_upper[:,5]
        rate_list = data_upper[:,8]

        high_level = data_levl[(data_levl[:,0]==n) & \
                               (data_levl[:,1]==l) & \
                               (data_levl[:,2]==j)][0]

        for i in range(len(data_upper)):
            plot_rate(lower_n_list[i], lower_l_list[i], lower_j_list[i])
            low_level = data_levl[(data_levl[:,0]==lower_n_list[i]) & \
                             (data_levl[:,1]==lower_l_list[i]) & \
                             (data_levl[:,2]==lower_j_list[i])][0]
            life_time = (low_level[4])
            ### plot level
            #if life_time > 1e5:
            #    ax.hlines(low_level[3], low_level[1]-0.2, low_level[1]+0.2, lw=5)
            #else:
            #    ax.hlines(low_level[3], low_level[1]-0.2, low_level[1]+0.2, lw=life_time/2e3)
            #ax.text(low_level[1]+0.2, low_level[3], "(%d, %d, %3.1f)" % (low_level[0], low_level[1], low_level[2]))
            ### plot spontaneous transition
            ax.plot([high_level[1], low_level[1]], [high_level[3], low_level[3]], lw=rate_list[i]/1e6)

        life_time = high_level[4]
        if life_time > 1e5: 
            ax.hlines(high_level[3], high_level[1]-0.2, high_level[1]+0.2, lw=5)
        else:
            ax.hlines(high_level[3], high_level[1]-0.2, high_level[1]+0.2, lw=life_time/2e3)
        ax.text(high_level[1]+0.2, high_level[3], "%d%s%3.1f" % \
            (high_level[0], l_notion[int(high_level[1])], high_level[2]))    

    plot_rate(10, 1, 1.5)
    plt.show()
    



#plot_absorption_spectra()
plot_spontaneous_transition_diagram()

#plot_spontaneous_rate() # not yet done, so don't try - taking long time to run

