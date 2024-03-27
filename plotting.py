import matplotlib.pyplot as plt
import seaborn as sns
        

def plot_stars(df, header):
    from matplotlib.lines import Line2D
    
    f, a = plt.subplots(1,2, figsize=(8,4), gridspec_kw={'width_ratios':[1,0.6]})
    # thin disk=1, thick disk=2, halo=3, bulge=4

    # List of RGB triplets
    rgb_values = sns.color_palette("husl", 4)[::-1]
    # Map label to RGB
    color_map = sns.color_palette("husl", 4, as_cmap=True)

    handles = [Line2D([0], [0], color=rgb_values[0], marker='o', linestyle='', label='thin disk'),
               Line2D([0], [0], color=rgb_values[1], marker='o', linestyle='', label='thick disk'),
               Line2D([0], [0], color=rgb_values[2], marker='o', linestyle='', label='halo'),
               Line2D([0], [0], color=rgb_values[3], marker='o', linestyle='', label='bulge')]

    a[0].scatter(df['ra'], df['dec'], s=1, c=df['gc'], cmap=color_map, vmin=df['gc'].min()-.5, vmax=df['gc'].max()+.5)
    a[0].plot(header['rightascension'], header['declination'], 'kx', ms=10, markeredgewidth=1)
    a[0].set_xlabel('RA')
    a[0].set_ylabel('Dec')

    a[0].legend(handles=handles, loc='upper left', bbox_to_anchor=(0.95,1))

    a[1].hist(df['magnorm'], histtype='step', label=f'N={len(df)}')
    a[1].set_yscale('log')
    a[1].set_xlabel('$g$ mag')
    a[1].set_ylabel('N')
    a[1].legend(loc='upper left')

    plt.savefig(f'plots/trilegal_stars_{expid}.png', dpi=200, facecolor='w', transparent=False)


def plot_galactic_coord(l, b):
    plt.subplot(111, projection='aitoff')
    plt.grid(True, zorder=2)
    plt.scatter(l.wrap_at('180d').radian, b.radian, s=10, marker='o', zorder=3)
    plt.xlabel('longitude l')
    plt.ylabel('latitude b')
    
    plt.savefig('plots/galactic_coord.png', dpi=150)
    
