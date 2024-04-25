import pandas as pd

class ConstructionHeuristic:
    def __init__(self):
        # Capacity of tank vessel (kg)
        self.Q = 30000

    def compute_inventory_level(self, C, T):
        """
        Convert a sheet of sample writing input to a custom directory structure of PNGs.

        Parameters
        ----------
        C : list
            Set of customers C = {1,..., N}.
        T : list
            Set of time periods T = {1,...,T}.
        """
        for customer in C:
            for time_period in T:
                inventory =  initial_inventory[customer] - 
        
    def test():
        pass

    def run(self, ):

        S_star = []
        ratio_demand = 1.0

        while ratio_demand > 0:
            inventory_level = self.compute_inventory_level()




if __name__ == "__main__":
    df = pd.read_csv('data/order_data.csv')
    