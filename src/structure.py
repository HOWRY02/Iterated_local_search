import numpy as np

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
        self.dilivery_quantities = np.zeros_like(forecasted_quantities)
        self.depot: Customer = list(filter(lambda x: x.number == 0, customers))[0]
        self.depot.is_serviced = True

    def __repr__(self):
        return f"Vehicle capacity: {self.vehicle_capacity}\n"

    def obj_func(self, solution):
        return sum(map(lambda routes: sum([route.total_distance for route in routes]), solution))

    def print_canonical(self, solution):
        # return "\n".join(list(map(lambda routes: (route.canonical_view for route in routes), solution)))
        return "\n".join(list(map(lambda routes: ' -- '.join(route.canonical_view for route in routes), solution)))
    
    @property
    def duration(self):
        return len(self.forecasted_quantities[0])


class Route:
    def __init__(self, problem: Problem, customers: list, t_dilivery_quantities):
        self.problem: Problem = problem
        self._customers: list = [self.problem.depot, *customers, self.problem.depot]
        self.t_dilivery_quantities: list = t_dilivery_quantities

    def __repr__(self):
        return " ".join(str(customer.number) for customer in self._customers)

    @property
    def canonical_view(self):
        distance = 0
        result = [0, 0.0]
        for source, target in zip(self._customers, self._customers[1:]):
            # start_time = max([target.ready_time, time + source.distance(target)])
            # time = start_time + target.service_time
            distance += source.distance(target)
            result.append(target.number)
            result.append(distance)

        return " ".join(str(x) for x in result)

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
            total_quantity += self.t_dilivery_quantities[customer.number-1]
        return total_quantity

    @property
    def edges(self):
        return list(zip(self._customers, self._customers[1:]))

    @property
    def is_feasible(self):
        capacity = self.problem.vehicle_capacity
        is_feasible = True
        for source, target in zip(self.customers, self.customers[1:]):
            if source.time_window != target.time_window:
                is_feasible = False
                break

        if self.total_quantity > capacity:
            is_feasible = False

        return is_feasible
