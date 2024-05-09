import math
import numpy as np
import pandas as pd

class Customer:
    def __init__(self, customer_info):
        self.number = customer_info.name
        self.name = customer_info.loc["Name"]
        self.x = customer_info.loc["Latitude"]
        self.y = customer_info.loc["Longtitude"]
        self.capacity = customer_info.loc["Capacity"]
        self.near_safety_level = customer_info.loc["Near safety level"]
        self.safety_level = customer_info.loc["Safety level"]
        self.init_quantity = customer_info.loc["Initial tank quantity"]
        self.time_window = customer_info.loc["Time window"]
        self.is_serviced = False

    def __repr__(self):
        return f"C_{self.name}"

    def distance(self, target):
        # return math.sqrt(math.pow(self.x - target.x, 2) + math.pow(target.y - self.y, 2))
    
        # Convert degrees to radians
        lat1, lon1, lat2, lon2 = map(np.radians, [self.x, self.y, target.x, target.y])

        # Earth radius in kilometers
        earth_radius = 6371

        # Distance formula for flat Earth (ignoring Earth's curvature)
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = np.sin(dlat / 2) * np.sin(dlat / 2) + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) * np.sin(dlon / 2)
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

        return earth_radius * c


class Problem:
    def __init__(self, customers: list, forecasted_quantities, delivery_unit_cost, setup_cost_for_one_trip, vehicle_capacity):
        self.delivery_unit_cost = delivery_unit_cost
        self.setup_cost_for_one_trip = setup_cost_for_one_trip
        self.vehicle_capacity = vehicle_capacity

        self.customers = list(filter(lambda x: x.number != 0, customers))
        self.forecasted_quantities = forecasted_quantities
        self.depot: Customer = list(filter(lambda x: x.number == 0, customers))[0]
        self.depot.is_serviced = True

    def __repr__(self):
        return f"Vehicle capacity: {self.vehicle_capacity}\n"

    def obj_func(self, routes):
        return sum(map(lambda x: x.total_distance, routes))

    def print_canonical(self, routes):
        return "\n".join(list(map(lambda x: x.canonical_view, routes)))
    
    @property
    def duration(self):
        return len(self.forecasted_quantities[0])


class Route:
    def __init__(self, problem: Problem, customers: list, dilivery_quantities):
        self.problem: Problem = problem
        self._customers: list = [self.problem.depot, *customers, self.problem.depot]
        self._dilivery_quantities = dilivery_quantities

    def __repr__(self):
        return " ".join(str(customer.number) for customer in self._customers)

    # @property
    # def canonical_view(self):
    #     time = 0
    #     result = [0, 0.0]
    #     for source, target in zip(self._customers, self._customers[1:]):
    #         start_time = max([target.ready_time, time + source.distance(target)])
    #         time = start_time + target.service_time
    #         result.append(target.number)
    #         result.append(start_time)
    #     return " ".join(str(x) for x in result)

    # @property
    # def dilivery_quantities(self):
    #         self._dilivery_quantities
    #     return 

    @property
    def customers(self):
        return self._customers[1:-1]

    @property
    def total_distance(self):
        '''
        Find the total distance in a route
        '''
        total_distance = 0
        for source, target in zip(self._customers, self._customers[1:]):
            total_distance += source.distance(target)
        return total_distance
    
    @property
    def total_quantity(self):
        '''
        Find the total dilivery quantity in a route
        '''
        total_quantity = 0
        for customer in self.customers:
            total_quantity += self._dilivery_quantities[customer.number-1]
        return total_quantity

    # @property
    # def edges(self):
    #     return list(zip(self._customers, self._customers[1:]))

    # @property
    # def is_feasible(self):
    #     time = 0
    #     capacity = self.problem.vehicle_capacity
    #     is_feasible = True
    #     for source, target in zip(self._customers, self._customers[1:]):
    #         start_service_time = max([target.ready_time, time + source.distance(target)])
    #         if start_service_time >= target.due_date:
    #             is_feasible = False
    #         time = start_service_time + target.service_time
    #         capacity -= target.demand
    #     if time >= self.problem.depot.due_date or capacity < 0:
    #         is_feasible = False
    #     return is_feasible
    

# class Customer:
#     def __init__(self, number, x, y, demand, ready_time, due_date, service_time):
#         self.number = number
#         self.x = x
#         self.y = y
#         self.demand = demand
#         self.ready_time = ready_time
#         self.due_date = due_date
#         self.service_time = service_time
#         self.is_serviced = False

#     def __repr__(self):
#         return f"C_{self.number}"

#     def distance(self, target):
#         return math.sqrt(math.pow(self.x - target.x, 2) + math.pow(target.y - self.y, 2))


# class Problem:
#     def __init__(self, name, customers: list, vehicle_number, vehicle_capacity):
#         self.name = name
#         self.customers = customers
#         self.vehicle_number = vehicle_number
#         self.vehicle_capacity = vehicle_capacity
#         self.depot: Customer = list(filter(lambda x: x.number == 0, customers))[0]
#         self.depot.is_serviced = True

#     def __repr__(self):
#         return f"Instance: {self.name}\n" \
#                f"Vehicle number: {self.vehicle_number}\n" \
#                f"Vehicle capacity: {self.vehicle_capacity}\n"

#     def obj_func(self, routes):
#         return sum(map(lambda x: x.total_distance, routes))

#     def print_canonical(self, routes):
#         return "\n".join(list(map(lambda x: x.canonical_view, routes)))


# class Route:
#     def __init__(self, problem: Problem, customers: list):
#         self.problem: Problem = problem
#         self._customers: list = [self.problem.depot, *customers, self.problem.depot]

#     def __repr__(self):
#         return " ".join(str(customer.number) for customer in self._customers)

#     @property
#     def canonical_view(self):
#         time = 0
#         result = [0, 0.0]
#         for source, target in zip(self._customers, self._customers[1:]):
#             start_time = max([target.ready_time, time + source.distance(target)])
#             time = start_time + target.service_time
#             result.append(target.number)
#             result.append(start_time)
#         return " ".join(str(x) for x in result)

#     @property
#     def customers(self):
#         return self._customers[1:-1]

#     @property
#     def total_distance(self):
#         time = 0
#         for source, target in zip(self._customers, self._customers[1:]):
#             start_time = max([target.ready_time, time + source.distance(target)])
#             time = start_time + target.service_time
#         return time

#     @property
#     def edges(self):
#         return list(zip(self._customers, self._customers[1:]))

#     @property
#     def is_feasible(self):
#         time = 0
#         capacity = self.problem.vehicle_capacity
#         is_feasible = True
#         for source, target in zip(self._customers, self._customers[1:]):
#             start_service_time = max([target.ready_time, time + source.distance(target)])
#             if start_service_time >= target.due_date:
#                 is_feasible = False
#             time = start_service_time + target.service_time
#             capacity -= target.demand
#         if time >= self.problem.depot.due_date or capacity < 0:
#             is_feasible = False
#         return is_feasible
