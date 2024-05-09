import os
import sys
import itertools
import numpy as np

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from src.structure import Problem, Route
from utils.utility import find_inventory_levels, check_urgency_degree, find_logistic_ratio

class ConstructionHeuristic:
    def __init__(self, problem: Problem):
        self.problem: Problem = problem

    def get_solution(self):
        """Solution sampled from customer list, sorted by demand"""

        def get_appropriate_route(ratio_demand, look_ahead, t, i, temp_inventory_levels, customer, route):
            dilivery_quantity = 0
            levels_condition = temp_inventory_levels[i][t] - customer.safety_level
            if levels_condition < 0:
                if t == (self.problem.duration-1):
                    dilivery_quantity = min(-levels_condition/100*customer.capacity, self.problem.vehicle_capacity)
                else:
                    dilivery_quantity = min(customer.capacity*(1 - temp_inventory_levels[i][t-1]/100), self.problem.vehicle_capacity)
                route.append(customer)
            else:
                if check_urgency_degree(i, temp_inventory_levels, t, look_ahead):
                    dilivery_quantity = min((customer.capacity*(1 - temp_inventory_levels[i][t-1]/100))*ratio_demand, self.problem.vehicle_capacity)
                    route.append(customer)
            return route, dilivery_quantity

        solution_list = []
        logistic_ratio_list = []
        ratio_demand = 1.0
        while ratio_demand > 0:
            look_ahead = 1
            while look_ahead <= (self.problem.duration/2):
                inventory_levels = find_inventory_levels(self.problem.customers,
                                                         self.problem.forecasted_quantities)

                temp_forecasted_quantities = self.problem.forecasted_quantities.copy()
                dilivery_quantities = np.zeros_like(temp_forecasted_quantities)
                solution = []
                for t in range(0, self.problem.duration):
                    route_day = []
                    route_night = []
                    for i, customer in enumerate(self.problem.customers):
                        dilivery_quantity = 0
                        if customer.time_window == 'night':
                            route_night, dilivery_quantity = get_appropriate_route(ratio_demand, look_ahead, t, i, inventory_levels, customer, route_night)
                        else:
                            route_day, dilivery_quantity = get_appropriate_route(ratio_demand, look_ahead, t, i, inventory_levels, customer, route_day)

                        if dilivery_quantity != 0:
                            dilivery_quantities[i][t] = dilivery_quantity
                            temp_forecasted_quantities[i][t] -= dilivery_quantity

                    t_dilivery_quantities = list(zip(*dilivery_quantities))[t]
                    solution.append([Route(self.problem, route_day, t_dilivery_quantities),
                                     Route(self.problem, route_night, t_dilivery_quantities)])
                    
                    # update inventory levels
                    inventory_levels = find_inventory_levels(self.problem.customers,
                                                             temp_forecasted_quantities)

                solution_list.append(solution)
                logistic_ratio, _ = find_logistic_ratio(self.problem, solution)
                logistic_ratio_list.append(logistic_ratio)

                look_ahead += 1
            ratio_demand = round(ratio_demand - 0.1, 1)

        best_logistic_ratio = min(logistic_ratio_list)
        best_solution = solution_list[logistic_ratio_list.index(best_logistic_ratio)]

        return best_solution


def two_opt(a, i, j):
    if i == 0:
        return a[j:i:-1] + [a[i]] + a[j + 1:]
    return a[:i] + a[j:i - 1:-1] + a[j + 1:]


def cross(a, b, i, j):
    return a[:i] + b[j:], b[:j] + a[i:]


def insertion(a, b, i, j):
    # print(a, b, i, j)
    if len(a) == 0:
        return a, b
    while i >= len(a):
        i -= len(a)
    return a[:i] + a[i + 1:], b[:j] + [a[i]] + b[j:]


def swap(a, b, i, j):
    # print(a, b, i, j)
    if i >= len(a) or j >= len(b):
        return a, b
    a, b = a.copy(), b.copy()
    a[i], b[j] = b[j], a[i]
    return a, b


class LocalSearch:
    def __init__(self, problem: Problem):
        self.problem: Problem = problem

    def optimize(self, solution: list) -> list:
        new_solution = list(solution)
        for i in range(len(new_solution)):
            is_stucked = False
            while not is_stucked:
                route = new_solution[i]
                is_stucked = True
                for k, j in itertools.combinations(range(len(route.customers)), 2):
                    new_route = Route(self.problem, two_opt(route.customers, k, j))
                    if new_route.is_feasible:
                        if new_route.total_distance < route.total_distance:
                            new_solution[i] = new_route
                            is_stucked = False
        return new_solution


class IteratedLocalSearch(LocalSearch):
    def __init__(self, problem: Problem, obj_func=None):
        super().__init__(problem)
        if not obj_func:
            obj_func = self.problem.obj_func
        self.obj_func = obj_func
        self.initial_solution = ConstructionHeuristic(problem).get_solution()

    def perturbation(self, routes: list) -> list:
        best = [Route(self.problem, route.customers) for route in routes]
        is_stucked = False
        while not is_stucked:
            is_stucked = True
            # Для всех возможных пар маршрутов
            for i, j in itertools.combinations(range(len(best)), 2):
                # Для всех возможных индексов в двух маршрутах
                for k, l in itertools.product(range(len(best[i].customers) + 2), range(len(best[j].customers) + 2)):
                    for func in [cross, insertion, swap]:
                        c1, c2 = func(best[i].customers, best[j].customers, k, l)
                        r1, r2 = Route(self.problem, c1), Route(self.problem, c2)
                        if r1.is_feasible and r2.is_feasible:
                            if r1.total_distance + r2.total_distance < best[i].total_distance + best[j].total_distance:
                                best[i] = r1
                                best[j] = r2
                                is_stucked = False
            best = list(filter(lambda x: len(x.customers) != 0, best))
        return best

    def execute(self):
        best = self.optimize(self.initial_solution)
        print("Local search solution:")
        print(self.problem.print_canonical(best))
        print("Total distance", self.obj_func(best))

        is_stucked = False
        while not is_stucked:
            is_stucked = True
            new_solution = self.perturbation(best)
            new_solution = self.optimize(new_solution)
            if self.obj_func(new_solution) < self.obj_func(best):
                is_stucked = False
                best = list(filter(lambda x: len(x.customers) != 0, new_solution))
                print("ILS step")
                print(self.problem.print_canonical(best))
                print("Total distance", self.obj_func(best))
        return best
