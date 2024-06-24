from collections import defaultdict, deque
import sys
import threading
import math
import time
from copy import deepcopy

# Router Class that contains all relevant information about a router instance
#
class Router:
    # Constructor
    def __init__(self, name) -> None:
        # Unique name for the router
        self.name = name

        # Shared queue
        self.queue = deque()

        # Lock for shared queue
        self.queue_lock = threading.Lock()

        # Number of iterations
        self.iterations = 0

        # List of neighbour routers
        self.neighbours = []

        # Map that stores router name as key and iteration number when it was appended as value
        self.appended_at = defaultdict(lambda: None)

        # Routing Table, a defaultdict that maps a dest router to its [<cost>, <path>] value
        # If missing key, it gives default value of [math.inf, '[no path]']
        self.table = defaultdict(lambda: [math.inf, '[no path]'])
        self.table[name] = 0, 'None' # Distance to itself is 0


    # Method to print Router object as a String
    def __str__(self) -> str:
        s = [
            "Router Object",      # String indicating the type of object
            f"Name: {self.name}",  # Name of the router
            f"Neighbours: {self.neighbours}",  # List of neighboring routers
            "Routing Table: {",  # Start of the routing table section
        ]

        for router_name in sorted(routers):
            # Generates all default values for whatever doesn't exist (since we use defaultdict)
            _, _ = self.table[router_name]
        
        # Iterate over the keys of the routing table and append router information to the string
        for router_name in sorted(self.table.keys()):
            cost = self.table[router_name][0]     # Cost to reach the router
            x = "   "                             # Indentation string
            # Add "*" if the router was appended in the current iteration, else add " "
            x += "*" if self.appended_at[router_name] == self.iterations else " "
            # Append router information to the string
            s.append(f"{x}{router_name}: {cost:<10} via: {self.table[router_name][1]}")

        s.append("}")    # End of the routing table section
        return "\n".join(s)   # Join the lines with newline characters and return the string

    
    # Method to append names of neigbouring routers into instance variable neighbours
    def add_neighbours(self, name):
        self.neighbours.append(name)


# Method that parses the input.txt file and populates the routers dict
def input_parser(filename):
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()  # Read all lines from the input file

            no_of_routers = int(lines[0])  # Extract the number of routers from the first line

            routerNames = lines[1].split()  # Extract the names of routers from the second line
            # Create Router objects for each router name and add them to the routers dictionary
            for name in routerNames:
                routers[name] = Router(name)
            
            lines = lines[2:]  # Remove the first two lines (number of routers and router names)
            # Remove the last line if it contains "EOF" (not necessary for parsing)
            lines.pop() if "EOF" in lines[-1] else None

            # Iterate over the remaining lines to parse connections and costs between routers
            for line in lines:
                # Split the line by whitespace and extract source, destination, and cost
                src, dest, cost = map(
                    lambda x: int(x[1]) if x[0] == 2 else x[1], enumerate(line.split())
                )

                # Add the destination as a neighbor of the source router
                routers[src].add_neighbours(dest)
                # Update the routing table of the source router with the cost and next hop for the destination
                routers[src].table[dest][0] = cost
                routers[src].table[dest][1] = dest

                # Add the source as a neighbor of the destination router
                routers[dest].add_neighbours(src)
                # Update the routing table of the destination router with the cost and next hop for the source
                routers[dest].table[src][0] = cost
                routers[dest].table[src][1] = src
    except:
        # Raise a SyntaxError if there is an issue with the input file
        raise SyntaxError('Check input file for Syntax error.')
    

# Method to run after creating a thread
def threaded(router_name):
    # Get the router object corresponding to the given router_name
    router = routers[router_name]
    # Add the routing table and router name of each neighbor to the queue of the router
    add_to_queue(router_name)

    # Wait until the queue has messages for all neighbors
    while True:
        if len(router.queue) == len(router.neighbours):
            break
    
    # Implementing the Bellman-Ford Equation

    # Increase the iteration value for the router
    router.iterations += 1

    # Create a deepcopy of the router's routing table
    table_copy = deepcopy(router.table)

    # Iterate over messages in the router's queue
    for table, name in router.queue:
        # Iterate over all routers in the network
        for eachRouter in routers:
            # Calculate the new cost to reach each router based on received message
            val = table[eachRouter][0] + router.table[name][0]
            # Update the least-costly path if a better path is found
            if val < table_copy[eachRouter][0]:
                table_copy[eachRouter][0] = val
                table_copy[eachRouter][1] = table_copy[name][1]

    # Update the router's routing table and appended_at values if changes were made
    for key, value in table_copy.items():
        if router.table[key] != value:
            router.table[key] = value
            router.appended_at[key] = router.iterations

    # Clear the router's queue
    router.queue.clear()

    # Sleep for 2 seconds before exiting the thread
    time.sleep(2)

# Append router table, router name of each neighbour in the queue of the router
def add_to_queue(router_name):
    # Iterate over the neighbors of the router specified by router_name
    for nhbr in routers[router_name].neighbours:
        # Acquire the lock for the queue of the neighbor router
        with routers[nhbr].queue_lock:
            # Append a message to the neighbor's queue
            # The message consists of a deepcopy of the routing table of the router_name's router
            # and the name of the router_name
            routers[nhbr].queue.append((deepcopy(routers[router_name].table), router_name))

# Map containing name of router as key and the router object as value
routers = dict()

# Main function
if __name__ == '__main__':
    try:
        _, filename = sys.argv
    except:
        print('Error! Usage: python dvr.py filename')
    else:
        # parsing input.txt
        input_parser(filename)

        # Printing routers before updation
        print(f'\n******** Iteration 0 *********\n')
        for key, value in routers.items():
            print(f'{key} => {value}\n')

        
        # Printing 4 iterations of updation
        for itr in range(1, 5):
            threads = []
            for router_name in routers:
                thread = threading.Thread(target = threaded, args = (router_name, ))
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join()
            
            print(f'\n******** Iteration {itr} *********\n')
            for key, value in routers.items():
                print(f'{key} => {value}\n')