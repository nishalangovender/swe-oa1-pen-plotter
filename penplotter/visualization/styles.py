"""
Monumental-branded color scheme and styling utilities for matplotlib visualizations.
"""

from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt

# Monumental Brand Colors
MONUMENTAL_ORANGE = "#f74823"
MONUMENTAL_BLUE = "#2374f7"
MONUMENTAL_CREAM = "#fffdee"
MONUMENTAL_TAUPE = "#686a5f"
MONUMENTAL_YELLOW_ORANGE = "#ffa726"
MONUMENTAL_DARK_BLUE = "#0d1b2a"

# Custom colormap for time-gradient visualizations
MONUMENTAL_CMAP = LinearSegmentedColormap.from_list(
    "monumental", [MONUMENTAL_ORANGE, MONUMENTAL_BLUE]
)


def apply_dark_style(ax, apply_grid=True):
    """
    Apply Monumental dark mode styling to a matplotlib axis.

    Args:
        ax: Matplotlib axis object
        apply_grid: If True, adds a subtle grid overlay
    """
    # Set background colors
    ax.set_facecolor(MONUMENTAL_DARK_BLUE)

    # Style spines (axis borders)
    for spine in ax.spines.values():
        spine.set_color(MONUMENTAL_CREAM)
        spine.set_linewidth(1.0)

    # Style tick labels and tick marks
    ax.tick_params(
        colors=MONUMENTAL_CREAM,
        which="both",
        direction="out",
        length=4,
        width=1
    )

    # Style axis labels
    ax.xaxis.label.set_color(MONUMENTAL_CREAM)
    ax.yaxis.label.set_color(MONUMENTAL_CREAM)

    # Add subtle grid if requested
    if apply_grid:
        ax.grid(
            True,
            color=MONUMENTAL_CREAM,
            alpha=0.2,
            linestyle="--",
            linewidth=0.5
        )


def apply_dark_style_to_figure(fig):
    """
    Apply Monumental dark mode styling to entire figure.

    Args:
        fig: Matplotlib figure object
    """
    fig.patch.set_facecolor(MONUMENTAL_DARK_BLUE)

    # Apply to all axes in the figure
    for ax in fig.get_axes():
        apply_dark_style(ax)


def style_legend(legend, framealpha=0.9):
    """
    Apply Monumental styling to a legend.

    Args:
        legend: Matplotlib legend object
        framealpha: Transparency of legend background (0-1)
    """
    if legend:
        frame = legend.get_frame()
        frame.set_facecolor(MONUMENTAL_DARK_BLUE)
        frame.set_edgecolor(MONUMENTAL_TAUPE)
        frame.set_alpha(framealpha)
        frame.set_linewidth(1.0)

        # Style legend text
        for text in legend.get_texts():
            text.set_color(MONUMENTAL_CREAM)


def create_dark_figure(figsize=(12, 8), nrows=1, ncols=1):
    """
    Create a new figure with Monumental dark mode styling applied.

    Args:
        figsize: Figure size as (width, height) in inches
        nrows: Number of subplot rows
        ncols: Number of subplot columns

    Returns:
        fig, ax (or axes array if nrows*ncols > 1)
    """
    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=figsize,
        facecolor=MONUMENTAL_DARK_BLUE
    )

    # Apply styling to all axes
    if nrows * ncols == 1:
        apply_dark_style(axes)
        return fig, axes
    else:
        # Flatten axes array for iteration
        axes_flat = axes.flatten() if hasattr(axes, 'flatten') else [axes]
        for ax in axes_flat:
            apply_dark_style(ax)
        return fig, axes


def format_time_label(seconds):
    """
    Format time in seconds to a readable string.

    Args:
        seconds: Time value in seconds

    Returns:
        Formatted string (e.g., "1.5s", "1m 30s", "1h 5m")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
