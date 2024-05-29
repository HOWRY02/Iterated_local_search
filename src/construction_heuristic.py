import os
import sys
import itertools
import numpy as np

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from src.structure import Problem, Route
from src.utils.utility import find_inventory_levels, check_urgency_degree, nearest_neighbor_insertion_heuristic, find_logistic_ratio

class ConstructionHeuristic:
    def __init__(self, problem: Problem):
        self.problem: Problem = problem

    def get_solution(self):
        """Solution sampled from customer list, sorted by demand"""

        def get_appropriate_route(ratio_demand, look_ahead, t, i, inventory_levels, customer, customers_in_route):
            dilivery_quantity = 0
            levels_condition = inventory_levels[i][t] - customer.safety_level
            if t == 0: current_inventory_value = inventory_levels[i][0]
            else: current_inventory_value = inventory_levels[i][t-1]
            if levels_condition < 0:
                if t == (self.problem.duration-1):
                    dilivery_quantity = min(-levels_condition/100*customer.capacity, self.problem.vehicle_capacity)
                else:
                    dilivery_quantity = min(customer.capacity*(1 - current_inventory_value/100), self.problem.vehicle_capacity)
                customers_in_route.append(customer)
            else:
                if check_urgency_degree(customer, inventory_levels, t, i, look_ahead):
                    dilivery_quantity = min((customer.capacity*(1 - current_inventory_value/100))*ratio_demand, self.problem.vehicle_capacity)
                    customers_in_route.append(customer)
            return customers_in_route, dilivery_quantity


        logistic_ratio_min = 1000000000
        ratio_demand = 1.0
        while ratio_demand > 0:
            look_ahead = 1
            while look_ahead <= (self.problem.duration/2):
                dilivery_quantities = np.zeros_like(self.problem.forecasted_quantities)
                inventory_levels = find_inventory_levels(self.problem.customers,
                                                         self.problem.forecasted_quantities,
                                                         dilivery_quantities)
                solution = []
                for t in range(self.problem.duration):
                    C_day = []
                    C_night = []
                    for i, customer in enumerate(self.problem.customers):
                        dilivery_quantity = 0
                        if customer.time_window == 'night':
                            C_night, dilivery_quantity = get_appropriate_route(ratio_demand, look_ahead, t, i, inventory_levels, customer, C_night)
                        else:
                            C_day, dilivery_quantity = get_appropriate_route(ratio_demand, look_ahead, t, i, inventory_levels, customer, C_day)

                        dilivery_quantities[i][t] = dilivery_quantity

                    t_dilivery_quantities = list(zip(*dilivery_quantities))[t]

                    routes = []
                    routes_day = nearest_neighbor_insertion_heuristic(C_day, t_dilivery_quantities, self.problem.vehicle_capacity)
                    routes_night = nearest_neighbor_insertion_heuristic(C_night, t_dilivery_quantities, self.problem.vehicle_capacity)

                    for route in [*routes_day, *routes_night]:
                        routes.append(Route(self.problem, route, t_dilivery_quantities))

                    solution.append(routes)
                    
                    # update inventory levels
                    inventory_levels = find_inventory_levels(self.problem.customers,
                                                             self.problem.forecasted_quantities,
                                                             dilivery_quantities)

                logistic_ratio, _ = find_logistic_ratio(self.problem, solution)
                if logistic_ratio < logistic_ratio_min:
                    logistic_ratio_min = logistic_ratio
                    best_solution = solution
                    self.problem.dilivery_quantities = dilivery_quantities

                look_ahead += 1
            ratio_demand = round(ratio_demand - 0.1, 1)

        return best_solution


def raw_or_opt(a, i, j):
    if i == 0:
        return a[j:i:-1] + [a[i]] + a[j+1:]
    return a[:i] + a[j:i - 1:-1] + a[j+1:]


def or_opt(problem, solution):
    '''
    transfers k adjacent customers from their current 
    position to another position in the same route
    '''
    new_solution = list(solution)
    for t in range(len(solution)):
        t_dilivery_quantities = list(zip(*problem.dilivery_quantities))[t]
        for i, route in enumerate(new_solution[t]):
            is_stucked = False
            while not is_stucked:
                is_stucked = True
                for k, l in itertools.combinations(range(len(route.customers)), 2):
                    new_route = Route(problem, raw_or_opt(route.customers, k, l), t_dilivery_quantities)
                    if new_route.is_feasible:
                        if new_route.total_distance < new_solution[t][i].total_distance:
                            new_solution[t][i] = new_route
                            is_stucked = False

    return new_solution


def raw_swap(a, b, i, j, num_customer_swap=1):
    if len(a) >= num_customer_swap and len(b) >= num_customer_swap:
        if num_customer_swap == 1:
            a[i], b[j] = b[j], a[i]
        else:
            if len(b[j:j+2]) == 2:
                a, b = a[:i] + b[j:j+2] + a[i+1:], b[:j] + [a[i]] + b[j+2:]
            else:
                if len(b) > 2:
                    a, b = a[:i] + [b[0], b[-1]] + a[i+1:], b[1:j] + [a[i]] + b[j+2:]
                else:
                    return None, None
    else:
        return None, None
        
    return a, b


def swap(problem, solution):
    new_solution = list(solution)
    for t in range(len(solution)):
        t_dilivery_quantities = list(zip(*problem.dilivery_quantities))[t]
        is_stucked = False
        while not is_stucked:
            is_stucked = True
            for i, j in itertools.combinations(range(len(new_solution[t])), 2):
                for k, l in itertools.product(range(len(new_solution[t][i].customers)), range(len(new_solution[t][j].customers))):
                    for num_customer_swap in [1,2]:
                        c1, c2 = raw_swap(new_solution[t][i].customers, new_solution[t][j].customers, k, l, num_customer_swap)

                        if c1 is None:
                            break

                        r1, r2 = Route(problem, c1, t_dilivery_quantities), Route(problem, c2, t_dilivery_quantities)
                        if r1.is_feasible and r2.is_feasible:
                            if r1.total_distance + r2.total_distance < new_solution[t][i].total_distance + new_solution[t][j].total_distance:
                                new_solution[t][i] = r1
                                new_solution[t][j] = r2
                                is_stucked = False

    return new_solution


def raw_shift(a, b, i):
    if len(b) - 1 - i >= 0:
        j = i
    else:
        j = i - len(b)
        a, b = b, a

    a = a + b[:j+1]
    b = b[j+1:]

    return a, b


def shift(problem, solution):
    new_solution = list(solution)
    for t in range(len(solution)):
        t_dilivery_quantities = list(zip(*problem.dilivery_quantities))[t]
        is_stucked = False
        while not is_stucked:
            is_stucked = True
            for i, j in itertools.combinations(range(len(new_solution[t])), 2):
                for k in range(len(new_solution[t][i].customers)+len(new_solution[t][j].customers)-1):
                    is_break = False
                    c1, c2 = raw_shift(new_solution[t][i].customers, new_solution[t][j].customers, k)
                    r1, r2 = Route(problem, c1, t_dilivery_quantities), Route(problem, c2, t_dilivery_quantities)
                    if r1.is_feasible and r2.is_feasible:
                        if r1.total_distance + r2.total_distance < new_solution[t][i].total_distance + new_solution[t][j].total_distance:
                            if c1 and c2:
                                new_solution[t][i] = r1
                                new_solution[t][j] = r2
                            elif not c1:
                                new_solution[t][j] = r2
                                new_solution[t].remove(new_solution[t][i])
                                is_break = True
                                break
                            elif not c2:
                                new_solution[t][i] = r1
                                new_solution[t].remove(new_solution[t][j])
                                is_break = True
                                break
                            
                            is_stucked = False

                if is_break:
                    break

    return new_solution


def raw_transfer(problem, solution, t, route, i, j):
    t_dq_1 = list(list(zip(*problem.dilivery_quantities))[t])
    a = route.customers
    time_period_2 = t
    if len(solution[t-1]) - 1 - j >= 0:
        time_period_2 = t-1
        idx = j
        b = solution[t-1][idx].customers
        t_dq_2 = list(list(zip(*problem.dilivery_quantities))[t-1])
    else:
        time_period_2 = t+1
        idx = j - len(solution[t-1])
        b = solution[t+1][idx].customers
        t_dq_2 = list(list(zip(*problem.dilivery_quantities))[t+1])

    if a[i] in b:
        a, b = None, None
    else:
        t_dq_1[a[i].number-1], t_dq_2[a[i].number-1] = t_dq_2[a[i].number-1], t_dq_1[a[i].number-1]
        a, b = a[:i] + a[i+1:], b + [a[i]]

    return a, b, time_period_2, idx, t_dq_1, t_dq_2


def transfer(problem, solution):
    new_solution = list(solution)
    for t in range(len(solution)):
        is_stucked = False
        while not is_stucked:
            is_stucked = True
            for route in new_solution[t]:
                for i, customer in enumerate(route.customers):
                    is_break = False

                    if t > 0 and t < problem.duration-1:
                        for j in range(len(new_solution[t-1])+len(new_solution[t+1])-1):
                            c1, c2, time_period_2, idx, t_dq_1, t_dq_2 = raw_transfer(problem, new_solution, t, route, i, j)

                            if c1 is None:
                                break

                            r1, r2 = Route(problem, c1, t_dq_1), Route(problem, c2, t_dq_2)
                            
                            if r1.is_feasible and r2.is_feasible:
                                if c1 and c2:
                                    problem.dilivery_quantities[t][customer.number-1] = t_dq_1[customer.number-1]
                                    problem.dilivery_quantities[time_period_2][customer.number-1] = t_dq_2[customer.number-1]
                                    new_solution[t][i] = r1
                                    new_solution[time_period_2][idx] = r2
                                elif not c1:
                                    problem.dilivery_quantities[customer.number-1][t] = t_dq_1[customer.number-1]
                                    problem.dilivery_quantities[customer.number-1][time_period_2] = t_dq_2[customer.number-1]
                                    new_solution[time_period_2][idx] = r2
                                    new_solution[t].remove(route)
                                    is_break = True
                                    break
                                
                                is_stucked = False
                    if is_break:
                        break

    return new_solution


def raw_insertion(a, b, i, j):
    if len(a) == 0:
        return a, b
    while i >= len(a):
        i -= len(a)
    return a[:i] + a[i + 1:], b[:j] + [a[i]] + b[j:]


def raw_split(a, b, i, j):
    return a[:i] + b[j:], b[:j] + a[i:]


class LocalSearch:
    def __init__(self, problem: Problem):
        self.problem: Problem = problem

    def optimize(self, solution: list) -> list:
        initial_logistic_ratio, _ = find_logistic_ratio(self.problem, solution)
        set_ls_operators = [or_opt, swap, shift, transfer]
        while set_ls_operators:
            for operator in set_ls_operators:
                new_solution = operator(self.problem, solution)
                logistic_ratio, _ = find_logistic_ratio(self.problem, new_solution)
                if logistic_ratio < initial_logistic_ratio:
                    initial_logistic_ratio = logistic_ratio
                    set_ls_operators = [or_opt, swap, shift, transfer]
                else:
                    set_ls_operators.remove(operator)

        return new_solution


class IteratedLocalSearch(LocalSearch):
    def __init__(self, problem: Problem):
        super().__init__(problem)
        self.initial_solution = ConstructionHeuristic(problem).get_solution()

    def perturbation(self, solution: list) -> list:
        new_solution = list(solution)
        for t in range(len(solution)):
            t_dilivery_quantities = list(zip(*self.problem.dilivery_quantities))[t]
            is_stucked = False
            while not is_stucked:
                is_stucked = True
                # For all possible pairs of routes
                for i, j in itertools.combinations(range(len(new_solution[t])), 2):
                    # For all possible indexes in two routes
                    for k, l in itertools.product(range(len(new_solution[t][i].customers)), range(len(new_solution[t][j].customers))):
                        for func in [raw_split, raw_insertion, raw_swap]:
                            c1, c2 = func(new_solution[t][i].customers, new_solution[t][j].customers, k, l)
                            r1, r2 = Route(self.problem, c1, t_dilivery_quantities), Route(self.problem, c2, t_dilivery_quantities)
                            if r1.is_feasible and r2.is_feasible:
                                if r1.total_distance + r2.total_distance < new_solution[t][i].total_distance + new_solution[t][j].total_distance:
                                    new_solution[t][i] = r1
                                    new_solution[t][j] = r2
                                    is_stucked = False

        return new_solution

    def execute(self):
        logistic_ratio, _ = find_logistic_ratio(self.problem, self.initial_solution)
        # print("Initial Solution:\n", self.initial_solution)
        # print("Logistic ratio: ", logistic_ratio)

        best_solution = self.optimize(self.initial_solution)
        best_logistic_ratio, _ = find_logistic_ratio(self.problem, best_solution)

        is_stucked = False
        while not is_stucked:
            is_stucked = True
            new_solution = self.perturbation(best_solution)
            new_solution = self.optimize(new_solution)
            logistic_ratio, _ = find_logistic_ratio(self.problem, new_solution)
            if logistic_ratio < best_logistic_ratio:
                best_logistic_ratio = logistic_ratio
                is_stucked = False
                best_solution = new_solution
                print("ILS step")
                print(self.problem.print_canonical(best_solution))

        return best_solution
