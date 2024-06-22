import numpy as np


def find_inventory_levels(customers, forecasted_quantities, dilivery_quantities):
    inventory_levels = np.zeros_like(forecasted_quantities)
    for i in range(len(forecasted_quantities)):
        current_value = customers[i].init_quantity
        scaling_factor = 100 / customers[i].capacity
        for t in range(len(forecasted_quantities[0])):
            current_value -= scaling_factor*(forecasted_quantities[i][t] - dilivery_quantities[i][t])
            inventory_levels[i][t] = round(current_value,0)

    return inventory_levels


def check_urgency_degree(customer, inventory_levels, t, i, look_ahead):
    urgency_degree = False
    for time in range(t+1, t+look_ahead):
        if time > len(inventory_levels[i])-1:
            break
        levels_condition = inventory_levels[i][time] - customer.safety_level
        # print("check_urgency_degree: ", time, levels_condition)
        if levels_condition < 0:
            urgency_degree = True

    return urgency_degree


def nearest_neighbor_insertion_heuristic(customers_in_route, t_dilivery_quantities, vehicle_capacity):
    customer_dilivery = []
    for customer in customers_in_route:
        customer_dilivery.append([customer, t_dilivery_quantities[customer.number-1]])

    routes = []
    current_subroute = []
    current_sum = 0
    for customer, dilivery_quantity in customer_dilivery:
        if current_sum + dilivery_quantity <= vehicle_capacity:
            current_subroute.append(customer)
            current_sum += dilivery_quantity
        else:
            routes.append(current_subroute)
            current_subroute = [customer]
            current_sum = dilivery_quantity
        
    if current_subroute:
        routes.append(current_subroute)

    return routes


def zeros_like_list(input_list):
    return [[0 for _ in range(len(sublist2))] for sublist2 in input_list]


def find_logistic_ratio(problem, solution):
    setup_cost = 0
    delivery_cost = 0
    total_delivered_quantity = 0

    delivered_quantity_list = zeros_like_list(solution)
    distance_list = zeros_like_list(solution)

    for i in range(0,len(solution)):
        for j, route in enumerate(solution[i]):
            delivered_quantity_list[i][j] = route.total_quantity
            distance_list[i][j] = route.total_distance
            
            number_vehicle = np.ceil(route.total_quantity/problem.vehicle_capacity)
            setup_cost += number_vehicle*problem.setup_cost_for_one_trip
            delivery_cost += number_vehicle*route.total_distance*problem.delivery_unit_cost

    total_delivered_quantity = sum(sum(sublist) for sublist in delivered_quantity_list if sublist) 
    logistic_ratio = (setup_cost + delivery_cost)/total_delivered_quantity
    
    return logistic_ratio, [setup_cost, delivery_cost, delivered_quantity_list, distance_list]
