from dataclasses import dataclass
from drafter import *
set_website_title("Traffic analyzer")
set_site_information(
    author="Benjamin Goldberg",
    description="A site to input traffic data for a four way intersection and to analyze the levels of congestion and receive recommendations for green lights.",
    sources="",
    planning=[],
    links=[]
)
hide_debug_information()
@dataclass
class TrafficDirection:
    """Stores a direction, its car count, and eta for each cycle."""
    name: str
    cars: int
    wait_time: int
@dataclass
class State:
    """Stores all teh information for the traffic manager."""
    directions: list[TrafficDirection]
    current_cycle: int
    max_cycles: int
    busiest_direction: str
    traffic_history: list[int]
    random_arrivals: bool
    cars_passing: int
def initial_state() -> State:
    """Creates a new set of data with everything reset."""
    return State( [
            TrafficDirection("North", 0, 0),
            TrafficDirection("South", 0, 0),
            TrafficDirection("East", 0, 0),
            TrafficDirection("West", 0, 0)],0,0,"None",[],False,5)

def total_cars(state: State) -> int:
    """shows the amount of cars waiting"""
    total = 0
    for direction in state.directions:
        total += direction.cars
    return total
def congestion(cars: int) -> str:
    """determines severity of the direction based on # of cars"""
    if cars < 10:
        return "Light"
    elif cars <= 20:
        return "Moderate"
    else:
        return "Heavy"

def update_analysis(state: State) -> None:
    """Update clearance times and find the busiest directions. if remainder is more then 1 it needs another cycle"""
    most_cars = 0
    state.busiest_direction = "None"
    for direction in state.directions:
        direction.wait_time = direction.cars // state.cars_passing  
        if direction.cars % state.cars_passing > 0:
            direction.wait_time = direction.wait_time + 1 
        if direction.cars > most_cars:
            most_cars = direction.cars
            state.busiest_direction = direction.name
        elif direction.cars == most_cars and most_cars > 0:
            state.busiest_direction = (
                state.busiest_direction + ", " + direction.name
            )       
def traffic_summary(state: State) -> list[str]:
    """Make a traffic description for each direction."""
    descriptions = []
    for direction in state.directions:
        name = direction.name
        cars = str(direction.cars)
        level = congestion(direction.cars)
        wait = str(direction.wait_time)

        description = name + ": " + cars + " cars"
        description = description + " / " + level
        description = description + "amount of cycles: " + wait + " cycles"
        descriptions.append(description)
    return descriptions

@route
def index(state: State) -> Page:
    """homepage"""
    return Page(state, [
        "given the traffic counts, the program analyzes congestions and simulatess more traffic.",
        Button("Enter Traffic", "input_traffic"),
        Button("Simulation Setup", "simulation_setup"),
        Button("View summary", "simulation_results"),])

@route
def input_traffic(state: State) -> Page:
    """Display traffic inputs for all four directions."""
    return Page(state, [
        "Enter a  number 0-1000 for each direction.",
        "Saving new counts resets all data.",
        "North:",
        TextBox("north", str(state.directions[0].cars)),
        "South:",
        TextBox("south", str(state.directions[1].cars)),
        "East:",
        TextBox("east", str(state.directions[2].cars)),
        "West:",
        TextBox("west", str(state.directions[3].cars)),
        Button("Analyze Traffic", "analyze_traffic"),
        Button("Home", "index")])
@route
def analyze_traffic(
    state: State, north: int, south: int, east: int, west: int
) -> Page:
    """stores and analyzes traffic counts"""
    counts = [north, south, east, west]
    for count in counts:
        if count < 0 or count > 1000:
            return Page(state, [
                "Every car count must be between 0 and 1000.",
                Button("Back to Traffic Input", "input_traffic")])
    state.directions[0].cars = north
    state.directions[1].cars = south
    state.directions[2].cars = east
    state.directions[3].cars = west
    state.current_cycle = 0
    state.max_cycles = 0
    state.traffic_history = [total_cars(state)]
    update_analysis(state)
    recommendation = "All directions are empty."
    if state.busiest_direction != "None":
        recommendation = (
            "give more green light to: "
            + state.busiest_direction
            + ". if directions are tied then they share the same amount of priority.")
    content = [
        "Total cars: " + str(total_cars(state)),
        "Busiest direction(s): " + state.busiest_direction,
        recommendation,
        "The simulation gives every direction the same passing capacity.",
        "the amount of cars passing is"
        + str(state.cars_passing)
        + " cars pass per direction each cycle."]
    for description in traffic_summary(state):
        content.append(description)
    content.append(Button("Simulation Setup", "simulation_setup"))
    content.append(Button("Edit Traffic", "input_traffic"))
    content.append(Button("Home", "index"))
    return Page(state, content)
@route
def simulation_setup(state: State) -> Page:
    """ choose cycles and  capacity to pass."""
    selected_cycles = "5"
    if state.max_cycles == 10:
        selected_cycles = "10"
    return Page(state, [
        "Number of cycles:",
        SelectBox("cycles", ["5", "10"], selected_cycles),
        "Cars passing for each direction for each cycle (1-100):",
        TextBox("cars_passing", str(state.cars_passing)),
        Button("Start Simulation", "run_cycle"),
        Button("Edit Traffic", "input_traffic"),
        Button("Home", "index")])
@route
def run_cycle(state: State,cycles:str = "",cars_passing:int = 5) -> Page: 
    if cycles!= "":
        if cars_passing < 1 or cars_passing > 100:
            return Page(state, [
                "Cars  must be between 1-100.",
                Button("Back to Setup", "simulation_setup")])
        state.max_cycles = int(cycles)
        state.cars_passing = cars_passing
        state.current_cycle = 0
        state.traffic_history = [total_cars(state)]
    if state.max_cycles == 0:
        return simulation_setup(state)
    if state.current_cycle >= state.max_cycles:
        return simulation_results(state)
    for direction in state.directions:
        direction.cars = direction.cars - state.cars_passing
        if direction.cars < 0:
            direction.cars = 0
    state.current_cycle = state.current_cycle + 1
    state.traffic_history.append(total_cars(state))
    update_analysis(state)
    if state.current_cycle == state.max_cycles:
        return simulation_results(state)
    content = [
        "Cycle " + str(state.current_cycle)
        + " of " + str(state.max_cycles),
        "Total cars waiting: " + str(total_cars(state)),
        "Busiest direction: " + state.busiest_direction]
    for description in traffic_summary(state):
        content.append(description)
    content.append(Button("Next Cycle", "run_cycle"))
    content.append(Button("View Summary", "simulation_results"))
    content.append(Button("Home", "index"))
    return Page(state, content)
@route
def simulation_results(state: State) -> Page:
    """Display the simulation totals and history."""
    if state.max_cycles == 0:
        return Page(state, [
            Header("Simulation Summary"),
            "No simulation yet",
            Button("Simulation Setup", "simulation_setup"),
            Button("Home", "index")])
    starting_total = state.traffic_history[0]
    current_total = total_cars(state)
    cars_cleared = starting_total - current_total
    status = "In progress"
    if state.current_cycle == state.max_cycles:
        status = "Complete"
    content = [
        Header("Simulation Summary"),
        "Status: " + status,
        "Cycles completed: " + str(state.current_cycle),
        "Starting cars: " + str(starting_total),
        "Cars waiting: " + str(current_total),
        "Cars cleared: " + str(cars_cleared),
        "Cycle 0 shows the starting total."]
    cycle_number = 0
    for count in state.traffic_history:
        content.append(
            "Cycle " + str(cycle_number) + ": " + str(count) + " cars")
        cycle_number = cycle_number + 1
    for description in traffic_summary(state):
        content.append(description)
    if state.current_cycle < state.max_cycles:
        content.append(Button("Continue Simulation", "run_cycle"))
    content.append(
        Button("New run from the current liness", "simulation_setup"))
    content.append(Button("Reset Traffic", "reset_simulation"))
    content.append(Button("Home", "index"))
    return Page(state, content)

@route
def reset_simulation(state: State) -> Page:
    """Clear all traffic and bring back original settings."""
    for direction in state.directions:
        direction.cars = 0
        direction.wait_time = 0
    state.current_cycle = 0
    state.max_cycles = 0
    state.busiest_direction = "None"
    state.traffic_history = []
    state.cars_passing = 5
    return input_traffic(state)
start_server(initial_state())
