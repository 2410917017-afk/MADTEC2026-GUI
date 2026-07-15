AXIS_TEXT_COLOR = "#dddcde"
PLOT_BACKGROUND = "#1e1e1e"


def style_axis(axis, xlabel: str, ylabel: str):
    axis.set_xlabel(xlabel, color=AXIS_TEXT_COLOR)
    axis.set_ylabel(ylabel, color=AXIS_TEXT_COLOR)
    axis.set_facecolor(PLOT_BACKGROUND)
    axis.spines["bottom"].set_color(AXIS_TEXT_COLOR)
    axis.spines["left"].set_color(AXIS_TEXT_COLOR)
    axis.tick_params(axis="x", colors=AXIS_TEXT_COLOR)
    axis.tick_params(axis="y", colors=AXIS_TEXT_COLOR)
