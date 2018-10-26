# coding=utf-8
import matplotlib.pyplot as plt
import numpy as np


def plot_stokes_noise(resid, fig=None, title=None):
    """

    Parameters
    ----------
    resid : DataArray
        The residuals of the fit to estimate the noise in the measured
        Stokes signal. is returned by ds.variance_stokes
    fig : Figurehandle, optional
    title : str, optional
        Adds a title to the plot

    Returns
    -------
    fig : Figurehandle

    """
    # Set up the axes with gridspec
    if fig is None:
        fig = plt.figure(figsize=(8, 6))

    if title:
        fig.suptitle('Residuals in ' + title)

    grid = plt.GridSpec(10, 10, hspace=0.2, wspace=0.2)
    main_ax = fig.add_subplot(grid[2:, 2:-1])
    y_hist = fig.add_subplot(grid[2:, :2])  # xticklabels=[],
    x_hist = fig.add_subplot(grid[:2, 2:-1])  # , sharex=main_ax
    legend_ax = fig.add_subplot(grid[:2, :2], xticklabels=[], yticklabels=[])
    cbar_ax = fig.add_subplot(grid[2:, -1], xticklabels=[], yticklabels=[])

    resid.plot(ax=main_ax, cbar_ax=cbar_ax, cbar_kwargs={'aspect': 20})

    # x_hist
    x_hist2 = x_hist.twinx()
    resid.std(dim='x').plot(ax=x_hist2, c='blue')
    resid.mean(dim='x').plot(ax=x_hist2, c='orange')
    x_hist2.axhline(0, linestyle='--', c='orange')
    x_hist.set_xticklabels([])
    x_hist.set_yticklabels([])
    x_hist.set_xlim(main_ax.get_xlim())

    # y_hist
    dp = resid.std(dim='time')
    x = dp.values
    y = dp.x
    y_hist.plot(x, y, c='blue')
    dp = resid.mean(dim='time')
    x = dp.values
    y = dp.x
    y_hist.plot(x, y, c='orange')
    y_hist.set_ylim(main_ax.get_ylim())

    y_hist.axvline(0, linestyle='--', c='orange')
    # reverse axis
    y_hist.set_xlim(y_hist.get_xlim()[::-1])

    # legend
    legend_ax.fill_between([], [], facecolor='blue', label='STD')
    legend_ax.fill_between([], [], facecolor='orange', label='MEAN')
    legend_ax.legend(loc='center')
    legend_ax.axis('off')
    return fig


def plot_sigma_report(ds, temp_label, temp_var_label, itimes=None):
    assert 'CI' not in ds[temp_label].dims, 'use other plot report function'

    fig, (ax1, ax2) = plt.subplots(nrows=2, sharex=True, figsize=(12, 8))

    colors = ['#ffeda0', '#feb24c', '#f03b20']

    line_kwargs = dict(linewidth=0.7)

    temp = ds[temp_label].mean(dim='time').compute()
    stds = np.sqrt(ds[temp_var_label]).mean(dim='time')

    for l, c in zip([2., 1.], colors):
        y1 = temp - l * stds
        y2 = temp + l * stds
        label_str = f'{0:2.2f}'.format(l) + r'$\sigma$ confidence interval'
        ax1.fill_between(y1.x, y1, y2,
                         facecolor=c, label=label_str, alpha=0.9,
                         linewidth=0.7, edgecolor=c)

    if itimes:
        for iitimes in itimes:
            ds[temp_label].isel(time=iitimes).plot(
                ax=ax1, c='grey', label='DTS single', **line_kwargs)

    temp.plot(ax=ax1, linewidth=0.8, c='black', label='DTS avg')

    sigma_est = ds.ufunc_per_section(label=temp_label,
                                     func=np.std,
                                     temp_err=True,
                                     calc_per='stretch')

    for (k, v), (k_se, v_se) in zip(ds.sections.items(),
                                    sigma_est.items()):
        for vi, v_sei in zip(v, v_se):
            val = ds[k].mean(dim='time')
            ax1.plot(
                [vi.start, vi.stop], [val, val],
                linewidth=0.8, c='blue', linestyle='--')
            sig_dts = stds.sel(x=vi).mean()
            tbx, tby = (vi.start + vi.stop) / 2, val
            tbt = r"$\sigma_{Est}$ = " + f"{0:2.3f}".format(sig_dts.data) + r"$^\circ$C\n" + \
                  r"$\sigma_{DTS}$ = " + f"{0:2.3f}".format(v_sei) + r"$^\circ$C"
            ax1.annotate(
                tbt,
                xy=(tbx, tby),
                ha='center',
                fontsize=8,
                xytext=(0, 16),
                textcoords='offset points',
                bbox=dict(fc='white', alpha=0.4, color='none'))

    ax1.set_title('Temperature and standard deviation averaged over '
                  'time per reference section')
    ax1.legend()
    ax1.set_ylabel(r'Temperature [$^\circ$C]')

    err_ref = ds.ufunc_per_section(label=temp_label,
                                   func=None,
                                   temp_err=True,
                                   calc_per='stretch')
    x_ref = ds.ufunc_per_section(label='x', calc_per='stretch')

    for (k, v), (k_se, v_se), (kx, vx) in zip(ds.sections.items(),
                                              err_ref.items(),
                                              x_ref.items()):
        for vi, v_sei, vxi in zip(v, v_se, vx):
            var_temp_t = np.std(v_sei, axis=1)
            ax2.plot(vxi, var_temp_t, label=k, **line_kwargs)

    stds.plot(ax=ax2, c='black', **line_kwargs)
    ax2.set_ylim([0., 1.05 * stds.max()])
    ax2.set_title('Measured and projected standard deviation averaged over time')
    ax2.legend()
    ax2.set_ylabel(r'Temperature [$^\circ$C]')

    plt.tight_layout()
