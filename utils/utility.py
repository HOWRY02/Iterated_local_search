import numpy as np


def find_inventory_levels(customers, forecasted_quantities):
    inventory_levels = np.zeros_like(forecasted_quantities)
    for i, forecasted_quantity in enumerate(forecasted_quantities):
        current_value = customers[i].init_quantity
        scaling_factor = 100 / customers[i].capacity
        for j, value in enumerate(forecasted_quantity):
            current_value -= value*scaling_factor
            inventory_levels[i][j] = round(current_value,0)

    return inventory_levels


def check_urgency_degree(customer, inventory_levels, t, look_ahead):
    urgency_degree = False
    for time in range(t, t+look_ahead):
        if time > 14:
            break
        levels_condition = inventory_levels[customer.number-1][time] - customer.safety_level
        if levels_condition < 0:
            urgency_degree = True

    return urgency_degree


def find_logistic_ratio(problem, solution):
    setup_cost = 0
    delivery_cost = 0
    total_delivered_quantity = 0

    delivered_quantity_list = np.zeros_like(solution)
    distance_list = np.zeros_like(solution)

    for i in range(0,len(solution)):
        for j, route in enumerate(solution[i]):
            delivered_quantity_list[i][j] = route.total_quantity
            distance_list[i][j] = route.total_distance

            setup_cost += np.ceil(route.total_quantity/problem.vehicle_capacity)*problem.setup_cost_for_one_trip
            delivery_cost += route.total_distance*problem.delivery_unit_cost
    
    total_delivered_quantity = np.sum(np.array(delivered_quantity_list))
    logistic_ratio = (setup_cost + delivery_cost)/total_delivered_quantity
    
    return logistic_ratio, [setup_cost, delivery_cost, delivered_quantity_list, distance_list]
