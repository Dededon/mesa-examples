import mesa
import math

from .agent import Cop, Citizen


class EpsteinCivilViolence(mesa.Model):
    """
    Model 1 from "Modeling civil violence: An agent-based computational
    approach," by Joshua Epstein.
    http://www.pnas.org/content/99/suppl_3/7243.full
    Attributes:
        height: grid height
        width: grid width
        citizen_density: approximate % of cells occupied by citizens.
        cop_density: approximate % of cells occupied by cops.
        citizen_vision: number of cells in each direction (N, S, E and W) that
            citizen can inspect
        cop_vision: number of cells in each direction (N, S, E and W) that cop
            can inspect
        legitimacy:  (L) citizens' perception of regime legitimacy, equal
            across all citizens
        max_jail_term: (J_max)
        active_threshold: if (grievance - (risk_aversion * arrest_probability))
            > threshold, citizen rebels
        arrest_prob_constant: set to ensure agents make plausible arrest
            probability estimates
        movement: binary, whether agents try to move at step end
        max_iters: model may not have a natural stopping point, so we set a
            max.
    """

    def __init__(
        self,
        width=40,
        height=40,
        citizen_density=0.7,
        cop_density=0.074,
        citizen_vision=7,
        cop_vision=7,
        legitimacy=0.8,
        citizen_network_size=20,
        max_jail_term=1000,
        active_threshold=0.1,
        arrest_prob_constant=2.3,
        network_discount_factor=0.5,
        movement=True,
        max_iters=1000,
        seed=None,
    ):
        super().__init__()
        self.reset_randomizer(seed)
        print(f"Running EpsteinCivilViolence with seed {self._seed}")
        self.width = width
        self.height = height
        self.citizen_density = citizen_density
        self.cop_density = cop_density
        self.citizen_vision = citizen_vision
        self.cop_vision = cop_vision
        self.legitimacy = legitimacy
        self.citizen_network_size = citizen_network_size
        self.max_jail_term = max_jail_term
        self.network_discount_factor = network_discount_factor
        self.active_threshold = active_threshold
        self.arrest_prob_constant = arrest_prob_constant
        self.movement = movement
        self.max_iters = max_iters
        self.iteration = 0
        self.schedule = mesa.time.RandomActivation(self)
        self.grid = mesa.space.Grid(width, height, torus=True)

        # agent counts
        self.citizen_count = 0
        self.cop_count = 0
        self.jail_count = 0
        self.active_count = 0
        self.quiescent_count = 0
        self.average_jail_term = 0

        self.running = True

        unique_id = 0
        if self.cop_density + self.citizen_density > 1:
            raise ValueError("Cop density + citizen density must be less than 1")
        for (contents, x, y) in self.grid.coord_iter():
            if self.random.random() < self.cop_density:
                cop = Cop(unique_id, self, (x, y), vision=self.cop_vision)
                unique_id += 1
                self.grid[x][y] = cop
                self.schedule.add(cop)
            elif self.random.random() < (self.cop_density + self.citizen_density):
                citizen = Citizen(
                    unique_id,
                    self,
                    (x, y),
                    hardship=self.random.random(),
                    regime_legitimacy=self.legitimacy,
                    risk_aversion=self.random.random(),
                    threshold=self.active_threshold,
                    vision=self.citizen_vision,
                )
                unique_id += 1
                self.grid[x][y] = citizen
                self.schedule.add(citizen)

        self.citizen_count = self.count_citizens(self)
        self.cop_count = self.count_cops(self)
        self.jail_count = self.count_jailed(self)
        self.active_count = self.count_active(self)
        self.quiescent_count = self.count_quiescent(self)

        model_reporters = {
            "Quiescent": self.count_quiescent,
            "Active": self.count_active,
            "Jailed": self.count_jailed,
            "Speed of Rebellion Transmission": self.speed_of_rebellion_calculation,
        }
        agent_reporters = {
            "x": lambda a: a.pos[0],
            "y": lambda a: a.pos[1],
            "breed": lambda a: a.breed,
            "jail_sentence": lambda a: getattr(a, "jail_sentence", None),
            "condition": lambda a: getattr(a, "condition", None),
            "arrest_probability": lambda a: getattr(a, "arrest_probability", None),
        }
        self.datacollector = mesa.DataCollector(
            model_reporters=model_reporters, agent_reporters=agent_reporters
        )

        self.datacollector.collect(self)

        # intializing the agent network
        for agent in self.schedule.agents:
            # create a list of tuples of (agent, distance to agent) distances
            # from this agent to all other agents
            if agent.breed == "citizen":
                distances = []
                for other_agent in self.schedule.agents:
                    if agent is not other_agent:
                        distances.append(
                            (other_agent, self.distance_calculation(agent, other_agent))
                        )
                        # assign max distance
                max_distance = max(distances, key=lambda x: x[1])[1]
                # normalise all distances to be between 0 and 1 and replace
                # the distance with the normalised distance
                distances = [
                    (agent, distance / max_distance) for agent, distance in distances
                ]
                # assign network as a list to agent.network as a random
                # distribution of up to 20 agents preferring but not
                # limited to agents that are closer
                agent.network = self.random.choices(
                    [agent for agent, distance in distances],
                    weights=[distance for agent, distance in distances],
                    k=self.citizen_network_size,
                )

    def step(self):
        """
        Advance the model by one step and collect data.
        """
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)
        # update agent counts
        self.active_count = self.count_active(self)
        self.quiescent_count = self.count_quiescent(self)
        self.jail_count = self.count_jailed(self)

        # update iteration
        self.iteration += 1
        if self.iteration > self.max_iters:
            self.running = False


    @staticmethod
    def count_quiescent(model):
        """
        Helper method to count quiescent agents.
        """
        return len(
            [
                agent
                for agent in model.schedule.agents
                if agent.breed == "citizen" and agent.condition == "Quiescent"
            ]
        )

    @staticmethod
    def count_active(model):
        """
        Helper method to count active agents.
        """
        return len(
            [
                agent
                for agent in model.schedule.agents
                if agent.breed == "citizen" and agent.condition == "Active"
            ]
        )

    @staticmethod
    def count_jailed(model):
        """
        Helper method to count jailed agents.
        """
        return len(
            [
                agent
                for agent in model.schedule.agents
                if agent.breed == "citizen" and agent.jail_sentence > 0
            ]
        )

    @staticmethod
    def count_citizens(model):
        """
        Helper method to count citizens.
        """
        return len(
            [agent for agent in model.schedule.agents if agent.breed == "citizen"]
        )

    @staticmethod
    def count_cops(model):
        """
        Helper method to count cops.
        """
        return len([agent for agent in model.schedule.agents if agent.breed == "cop"])

    # combine all agent counts into one method
    @staticmethod
    def count_agents(model):
        """
        combines the various count methods into one
        """
        return (
            model.count_quiescent(model)
            + model.count_active(model)
            + model.count_jailed(model)
        )

    @staticmethod
    def speed_of_rebellion_calculation(model):
        """
        Calculates the speed of transmission of the rebellion.
        """
        if model.citizen_count == 0:
            return 0
        count = 0
        for agent in model.schedule.agents:
            if agent.breed == "citizen" and agent.flipped == True:
                count += 1
        return count / model.citizen_count

    def distance_calculation(self, agent1, agent2):
        """
        Helper method to calculate distance between two agents.
        """
        return math.sqrt(
            (agent1.pos[0] - agent2.pos[0]) ** 2 + (agent1.pos[1] - agent2.pos[1]) ** 2
        )
