import mesa

from .model import EpsteinCivilViolence
from .agent import Citizen, Cop, Media
from mesa.visualization.UserParam import Slider
from mesa.visualization.modules import ChartModule, TextElement


COP_COLOR = "#000000"
AGENT_QUIET_COLOR = "#4daf4a"
AGENT_REBEL_COLOR = "#FF0000"
JAIL_COLOR = "#808080"
MEDIA_COLOR = "#984ea3"


class JailChart(TextElement):
    """Display the current jail population."""

    def render(self, model):
        return f"Jail Population: {model.jail_population}"


class ActiveChart(TextElement):
    """Display the current active population."""

    def render(self, model):
        return f"Active Population: {model.active_population}"


chart = ChartModule(
    [
        {"Label": "Quiescent", "Color": "Green"},
        {"Label": "Active", "Color": "Red"},
        {"Label": "Jailed", "Color": "Grey"},
    ],
    data_collector_name="datacollector",
)


def citizen_cop_portrayal(agent):
    if agent is None:
        return

    portrayal = {
        "Shape": "circle",
        "x": agent.pos[0],
        "y": agent.pos[1],
        "Filled": "true",
    }

    if type(agent) is Citizen:
        color = (
            AGENT_QUIET_COLOR if agent.condition == "Quiescent" else AGENT_REBEL_COLOR
        )
        color = JAIL_COLOR if agent.jail_sentence else color
        portrayal["Color"] = color
        portrayal["r"] = 0.8
        portrayal["Layer"] = 0

    elif type(agent) is Cop:
        portrayal["Color"] = COP_COLOR
        portrayal["r"] = 0.8
        portrayal["Layer"] = 1

    elif type(agent) is Media:
        portrayal["Color"] = MEDIA_COLOR
        portrayal["r"] = 0.5
        portrayal["Layer"] = 1

    return portrayal


model_params = dict(
    height=40,
    width=40,
    citizen_density=0.7,
    cop_density=Slider("Cop Density", 0.074, 0.0, 0.1, 0.01),
    # cop_density=0.074,
    media_density=Slider("Media Density", 0.01, 0.0, 0.1, 0.01),
    citizen_vision=7,
    cop_vision=7,
    legitimacy=Slider("Legitimacy", 0.8, 0.0, 1.0, 0.1),
    # legitimacy=0.8,
    max_jail_term=1000,
)

canvas_element = mesa.visualization.CanvasGrid(citizen_cop_portrayal, 40, 40, 480, 480)
server = mesa.visualization.ModularServer(
    EpsteinCivilViolence,
    [canvas_element, chart],
    "Epstein Civil Violence",
    model_params,
)
