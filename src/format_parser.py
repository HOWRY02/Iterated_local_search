import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from src.structure import Problem, Customer

class FormatParser:
    def __init__(self, customers_df, forecasted_quantity_df):
        self.customers_df = customers_df
        self.forecasted_quantity_df = forecasted_quantity_df

    def get_problem(self) -> Problem:
        delivery_unit_cost = 50000         # VND/km
        setup_cost_for_one_trip = 300000    # VND/ship
        vehicle_capacity = 30000            # kg

        self.forecasted_quantity_df.set_index('Date', inplace=True)
        forecasted_quantity_df = self.forecasted_quantity_df.T
        forecasted_quantity = forecasted_quantity_df.to_numpy()

        customers = []
        for i in range(0,len(self.customers_df)):
            customers.append(Customer(self.customers_df.iloc[i, :]))

        return Problem(customers, forecasted_quantity, delivery_unit_cost, setup_cost_for_one_trip, vehicle_capacity)
    