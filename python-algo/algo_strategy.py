import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))
        
        # Add these instance variables to track wall information
        self.wall_breaches = []  # Walls that were breached in the current turn
        self.low_health_walls = []  # Walls with health below 40%
        self.wall_locations = []  # All wall locations
        self.scored_on_locations = []

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        
        # Initialize default wall locations - customize this for your strategy
        self.start_wall_locations = [[0,13], [27,13], [1,13], [26,13], [2,13], [25,13], [3,13], [24,13],
                                     [4,12], [23,12], [5,11], [22,11], [6,10], [21,10], [7,9], [20,9],
                                     [8,8], [19,8], [9,7], [18,7], [10,6], [17,6], [11,5], [16,5], [13,7], [14,7]]
        self.corner_walls = [[0,13], [27,13], [1,13], [26,13], [2,13], [25,13], [3,13], [24,13], [4,12], [23,12]]
        self.corner_turrets = [[1,12], [26,12], [3,12], [24,12]]
        self.start_turret_locations = [[1,12], [26,12], [3,12], [24,12], [13,6], [14,6]]
        self.second_turret_locations = [[12,7], [15,7]]
        self.corner_attack_wall_locations = [[12,5], [15,5]]
        self.interceptor_wall_locations = [[7,7], [20,7]]
        # self.priority_upgrade_locations = [[0,13], [27,13], [26,13], [1,13], [2,13], [25,13]]
        self.rndm = None
    
    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  # Comment or remove this line to enable warnings.

        # Update our tracking variables at the beginning of each turn
        self.wall_locations = self.get_wall_locations(game_state)
        self.find_low_health_walls(game_state, 0.4)  # Find walls below 40% health
        
        # Print debug information
        gamelib.debug_write(f"Wall breaches from last turn: {self.wall_breaches}")
        gamelib.debug_write(f"Low health walls: {self.low_health_walls}")
        
        # Run our improved strategy
        self.spam_strategy(game_state)

        game_state.submit_turn()

    def get_wall_locations(self, game_state):
        """
        Get all locations where we have walls
        
        Args:
            game_state: The current game state
            
        Returns:
            A list of locations where we have walls
        """
        wall_locations = []
        
        for x in range(game_state.ARENA_SIZE):
            for y in range(game_state.HALF_ARENA):  # Only check our side of the map
                location = [x, y]
                if game_state.contains_stationary_unit(location):
                    unit = game_state.contains_stationary_unit(location)
                    if unit.unit_type == WALL and unit.player_index == 0:  # It's our wall
                        wall_locations.append(location)
        
        return wall_locations

    def find_low_health_walls(self, game_state, health_threshold=0.4):
        """
        Find walls with health below the given threshold (default 40%)
        
        Args:
            game_state: The current game state
            health_threshold: The health threshold as a decimal (0.4 = 40%)
            
        Returns:
            A list of locations of walls with health below the threshold
        """
        self.low_health_walls = []
        
        # Get all locations with walls
        for x in range(game_state.ARENA_SIZE):
            for y in range(game_state.HALF_ARENA):  # Only check our side of the map
                location = [x, y]
                if game_state.contains_stationary_unit(location):
                    unit = game_state.contains_stationary_unit(location)
                    if unit.unit_type == WALL and unit.player_index == 0:  # It's our wall
                        # Get the maximum health of a wall
                        max_health = gamelib.GameUnit(WALL, game_state.config).max_health
                        
                        # Check if health is below threshold
                        if unit.health / max_health < health_threshold:
                            self.low_health_walls.append(location)
                            gamelib.debug_write(f"Low health wall at {location} with {unit.health}/{max_health} health")
        
        return self.low_health_walls

    def repair_walls(self, game_state):
        """
        Repair damaged walls and replace breached walls
        """
        for location in self.corner_walls:
            if game_state.can_spawn(WALL, location):
                game_state.attempt_spawn(WALL, location)
                game_state.attempt_upgrade(location)
            else:
                game_state.attempt_upgrade(location)

        for location in self.corner_turrets:
            if game_state.can_spawn(TURRET, location):
                game_state.attempt_spawn(TURRET, location)
            else:
                game_state.attempt_upgrade(location)
        for location in self.start_wall_locations:
            if game_state.can_spawn(WALL, location):
                game_state.attempt_spawn(WALL, location)
        for location in [[13,8], [14,8], [13,7], [14,7]]:
            if game_state.can_spawn(WALL, location):
                game_state.attempt_spawn(WALL, location)
                game_state.attempt_upgrade(location)
            else:
                game_state.attempt_upgrade(location)
        for location in self.start_turret_locations:
            if game_state.can_spawn(TURRET, location):
                game_state.attempt_spawn(TURRET, location)
            else:
                game_state.attempt_upgrade(location)
        for location in [[13,0], [14,0], [13,1], [14,1]]:
            if game_state.attempt_spawn(SUPPORT, location):
                game_state.attempt_spawn(SUPPORT, location)
            else:
                game_state.attempt_upgrade(location)
        for location in self.second_turret_locations:
            if game_state.attempt_spawn(TURRET, location):
                game_state.attempt_spawn(TURRET, location)
            else:
                game_state.attempt_upgrade(location)
    
    def repair(self, game_state, rndm):
        if rndm == 1:
            for location in [[0,13], [27,13], [26,13], [2,13], [25,13], [3,13], [24,13],
                                     [4,12], [23,12], [5,11], [22,11], [6,10], [21,10], [7,9], [20,9],
                                     [8,8], [19,8], [9,7], [18,7], [10,6], [17,6], [11,5], [16,5], [13,7], [14,7]]:
                if game_state.can_spawn(WALL, location):
                    game_state.attempt_spawn(WALL, location)
                else:
                    game_state.attempt_upgrade(location)
        else:
            for location in [[0,13], [27,13], [1,13], [2,13], [25,13], [3,13], [24,13],
                                     [4,12], [23,12], [5,11], [22,11], [6,10], [21,10], [7,9], [20,9],
                                     [8,8], [19,8], [9,7], [18,7], [10,6], [17,6], [11,5], [16,5], [13,7], [14,7]]:
                if game_state.can_spawn(WALL, location):
                    game_state.attempt_spawn(WALL, location)
                else:
                    game_state.attempt_upgrade(location)
                
                
    
    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        for location in self.start_wall_locations:
            game_state.attempt_spawn(WALL, location)
        # Place turrets that attack enemy units
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, self.start_turret_locations)
        
        # Place walls in front of turrets to soak up damage for them

            
        # Place supports behind turrets
        # support_locations = [[13,0],[14,0]]
        # game_state.attempt_spawn(SUPPORT, support_locations)
        
        # Upgrade walls so they soak more damage
        # Prioritize upgrading walls that are frequently breached
        """"
        for location in self.scored_on_locations:
            wall_loc = [location[0], location[1] + 1]
            if wall_loc in self.wall_locations and wall_loc not in self.priority_upgrade_locations:
                self.priority_upgrade_locations.append(wall_loc)
        """
        game_state.attempt_upgrade(self.corner_walls)
        game_state.attempt_upgrade(self.corner_turrets)
        # game_state.attempt_upgrade(self.default_turret_locations)
        
        # Then upgrade the rest of the walls if we have spare SP (COMMENTED OUT FOR THIS VERISON OF FUNNEL STRAT)
        # other_walls = [loc for loc in self.wall_locations if loc not in priority_upgrade_locations]
        # game_state.attempt_upgrade(other_walls)
        
        # Upgrade turrets
        # game_state.attempt_upgrade(self.default_turret_locations)

    """ 
    def build_reactive_defense(self, game_state):
        
        # This function builds reactive defenses based on where the enemy scored on us from.
        # We can track where the opponent scored by looking at events in action frames
        # as shown in the on_action_frame function
        
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            game_state.attempt_spawn(TURRET, build_location)
    """
    def improved_strategy(self, game_state):
        """
        An improved strategy that uses wall breach and health tracking
        """
        # First, repair any damaged walls
        self.repair_walls(game_state)
        
        # Then build basic defenses
        self.build_defences(game_state)
        
        # Build reactive defenses based on enemy attacks (COMMENTED OUT FOR THIS VERSION OF FUNNEL STRAT)
        # self.build_reactive_defense(game_state)
        
        # In early game, focus on defense
        if game_state.turn_number < 5:
            self.stall_with_interceptors(game_state)
        else:
            # Analyze the enemy base
            enemy_front_units = self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15])
            
            # If they have many units in the front, use demolishers
            if enemy_front_units > 8:
                self.demolisher_line_strategy(game_state)
            else:
                # Otherwise, send scouts to their weak points
                # But only on odd turns to allow for resource buildup
                if game_state.turn_number % 2 == 1:
                    scout_spawn_location_options = [[13, 0], [14, 0]]
                    best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                    scout_count = game_state.number_affordable(SCOUT)
                    game_state.attempt_spawn(SCOUT, best_location, scout_count)
                
                # If we have resources remaining, strengthen our support structure
                support_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
                game_state.attempt_spawn(SUPPORT, support_locations)

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own structures 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining MP to spend let's send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """
    
    def interceptor_defence(self, game_state):
        spawn_int_loc = [[6,7], [21,7]]
        game_state.attempt_spawn(WALL, self.interceptor_wall_locations)
        game_state.attempt_spawn(INTERCEPTOR,spawn_int_loc)
        game_state.attempt_spawn(WALL, self.corner_attack_wall_locations)
        game_state.attempt_remove(self.interceptor_wall_locations)

    def corner_attack(self, game_state):
        game_state.attempt_spawn(WALL, [[3,13]])
        game_state.attempt_spawn(WALL, self.corner_attack_wall_locations)
        game_state.attempt_remove(self.corner_attack_wall_locations)
        game_state.attempt_spawn(INTERCEPTOR, [[4,9],[4,9],[4,9]])
        # game_state.attempt_spawn(WALL,[[21,8]])
        while game_state.get_resource(MP) >= game_state.type_cost(SCOUT)[MP]:
            game_state.attempt_spawn(SCOUT, [[22,8]])
    
    def corner2_attack(self, game_state):
        game_state.attempt_spawn(WALL, [[24,13]])
        game_state.attempt_spawn(WALL, self.corner_attack_wall_locations)
        game_state.attempt_remove(self.corner_attack_wall_locations)
        game_state.attempt_spawn(INTERCEPTOR, [[23,9],[23,9],[23,9]])
        # game_state.attempt_spawn(WALL,[[6,8]])
        while game_state.get_resource(MP) >= game_state.type_cost(SCOUT)[MP]:
            game_state.attempt_spawn(SCOUT, [[5,8]])


    def funnel_strategy(self, game_state):
        if game_state.turn_number==0 or game_state.turn_number == 1:
            self.build_defences(game_state)
            game_state.attempt_spawn(SCOUT, [16,2], num = 5)
        # if game_state.turn_number==2:
            # game_state.attempt_spawn(WALL, [[13,8], [14,8]])
            # game_state.attempt_spawn(INTERCEPTOR, [[10,3],[17,3]], num=2)
        if game_state.turn_number >= 2:
            if (game_state.turn_number + 1)%3 == 1:
                self.repair_walls(game_state)
                self.interceptor_defence(game_state)
            elif (game_state.turn_number + 1)%3 == 2:
                self.rndm = random.randint(1,2)
                self.repair_walls(game_state)
                game_state.attempt_remove(self.interceptor_wall_locations)
                if self.rndm == 1:
                    game_state.attempt_remove([[1,13]])
                    game_state.attempt_remove([[1,12]])
                else:
                    game_state.attempt_remove([[26,13]])
                    game_state.attempt_remove([[26,12]])
                game_state.attempt_spawn(INTERCEPTOR, [[10,3], [17,3]])
            elif (game_state.turn_number + 1)%3 == 0:
                if self.rndm == 1:
                    self.corner_attack(game_state)
                else:
                    self.corner2_attack(game_state)

    def spam_strategy(self, game_state):
        if game_state.turn_number == 0 or game_state.turn_number == 1:
            self.build_defences(game_state)
            game_state.attempt_spawn(SCOUT, [16,2], num = 5)
        if game_state.turn_number >= 2:
            if (game_state.turn_number)%2 == 0:
                self.rndm = random.randint(1,2)
                self.repair_walls(game_state)
                if self.rndm == 1:
                    game_state.attempt_remove([[1,13]])
                    game_state.attempt_remove([[1,12]])
                else:
                    game_state.attempt_remove([[26,13]])
                    game_state.attempt_remove([[26,12]])
                game_state.attempt_spawn(INTERCEPTOR, [[10,3], [17,3]])
            if game_state.turn_number%2 == 1:
                self.repair(game_state, self.rndm)
                if self.rndm == 1:
                    self.corner_attack(game_state)
                else:
                    self.corner2_attack(game_state)

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x=None, valid_y=None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on and track wall breaches
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        
        # Reset wall_breaches for this new action frame
        self.wall_breaches = []
        
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            unit_type = breach[3]
            
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                
            # Check if the breach was a wall
            if unit_type == WALL and unit_owner_self:
                gamelib.debug_write("Wall breach at: {}".format(location))
                self.wall_breaches.append(location)


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
