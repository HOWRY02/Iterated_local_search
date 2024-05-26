import pandas as pd
from src.format_parser import FormatParser
from src.construction_heuristic import IteratedLocalSearch, ConstructionHeuristic
from utils.utility import find_logistic_ratio


if __name__ == '__main__':
    # https://docs.google.com/spreadsheets/d/1ju4BEDdxhUJj7OvcGG2QmLlbmvSknwlIMFrdUS7JNhk/edit#gid=1442154428
    gsheetid = '1ju4BEDdxhUJj7OvcGG2QmLlbmvSknwlIMFrdUS7JNhk'
    forecasted_quantity_sheet = 'forecasted_quantity'
    customers_sheet = 'customers'
    forecasted_quantity_sheet_url = "https://docs.google.com/spreadsheets/d/{}/gviz/tq?tqx=out:csv&sheet={}".format(gsheetid, forecasted_quantity_sheet)
    customers_sheet_url = "https://docs.google.com/spreadsheets/d/{}/gviz/tq?tqx=out:csv&sheet={}".format(gsheetid, customers_sheet)

    customers_df = pd.read_csv(customers_sheet_url)
    forecasted_quantity_df = pd.read_csv(forecasted_quantity_sheet_url)
    
    problem = FormatParser(customers_df, forecasted_quantity_df).get_problem()
    solution, dilivery_quantities, look_ahead, ratio_demand = ConstructionHeuristic(problem).get_solution()

    logistic_ratio, [setup_cost, delivery_cost, delivered_quantity_list, distance_list] = find_logistic_ratio(problem, solution)
    
    print("Solution: ", solution)
    print("Logistic ratio: ", logistic_ratio)
    print("Setup cost: ", setup_cost)
    print("Travelling cost: ", delivery_cost)
    print("Dilivery quantities: \n", dilivery_quantities)
    print("Look ahead - ratio demand: ", look_ahead, ratio_demand)
    print("Total transportation quantity [day, night]: ", delivered_quantity_list)
    # print("Total transportation distance [day, night]: ", distance_list)
