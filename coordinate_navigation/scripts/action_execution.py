#!/usr/bin/env python
import math
from waypoints_dict import waypoints
from world_state import *

import rospy

from geometry_msgs.msg import Twist, PoseWithCovarianceStamped
from std_srvs.srv import Trigger
from coffee_bot_srvs.srv import Move, Plan

class PlanExecutor():

    global agents
    global doors
    global rooms
    global desks
    
    def __init__(self):

        '''
        Initializes action_execution node.
        '''

        # Initialize node
        rospy.init_node("action_execution", anonymous=False)
        rospy.loginfo("action_execution node active")

        # Initialize velocit publisher
        self.cmd_vel = rospy.Publisher('mobile_base/commands/velocity', Twist, queue_size=10) 
        self.rate = rospy.Rate(10)

        # Initialize service
        self.plan_executor_srv = rospy.Service("/action_executor", Plan, self.execute_plan) 
        rospy.loginfo("action_executor service active")

        # Wait for action services
        rospy.loginfo("Waiting for undock service")
        rospy.wait_for_service("undock")
        rospy.loginfo("Waiting for dock service")
        rospy.wait_for_service("dock")
        rospy.loginfo("Waiting for move service")
        rospy.wait_for_service("move")
        rospy.loginfo("Waiting for open_door service")
        rospy.wait_for_service("/open_door")
        rospy.loginfo("Waiting for amcl")
        rospy.wait_for_message("/amcl_pose", PoseWithCovarianceStamped, timeout=10)

        rospy.loginfo("All services running")

        self.undock(["lab", "charger_1"])
        self.approach_door(["lab_door", "lab", "kitchen"])
        self.approach_charger(["lab", "charger_1"])
        self.dock(["lab", "charger_1"])

        while not rospy.is_shutdown():
            rospy.spin()
        
    def execute_plan(self, req):

        '''
        Executes pddl plan.
        req: Plan() object containing pddl plan as a list of strings
        returns: None
        '''
        
        # Loop over actions 
        for action in req.plan:

            # Split action by space 
            action = action.split()

            if action[0] == 'approach_door':
                self.approach_door(action)
            # elif action[0] == 'open_door':
                # pass
            elif action[0] == 'exit_room':
                self.go_through_door(action)
            # elif action[0] == 'approach_desk':
                # pass
            # elif action[0] == 'make_coffee':
                # pass
            elif action[0] == 'approach_desk_refill':
                self.approach_desk_refill(action)
            # elif action[0] == 'refill':
                # pass
            elif action[0] == 'approach_charger':
                pass
            elif action[0] == 'dock':
                self.dock(action)
            elif action[0] == 'undock':
                self.undock(action)
            elif action[0] == 'charge':
                pass

    def approach_door(self, action):

        '''
        approach_door action executor, checks pre and post conditions of action.
        Calls move_action to move the turtlebot.
        action: list of strings expressing the pddl approach door action
        returns: boolean representing success/failure of action
        '''
    
        door = action[1]
        room1 = action[2]
        room2 = action[3]

        # Precondition checking
        if (doors.has_key(door) and 
        room1 in door["connect"] and room2 in door["connect"] and 
        agents["turtlebot"]["at"] == room1 and 
        not self.turtlebot["docked"]):

            # Call move action
            status = self.move_action(door + "_" + room1)

            # Update world state
            if status:
                agents["turtlebot"]["facing"] = door

            # Return status
            return status

        return False

    def go_through_door(self, action):

        '''
        go_through_door action executor, checks pre and post conditions of action.
        Calls move_action to move the turtlebot.
        action: list of strings expressing the pddl approach door action
        returns: boolean representing success/failure of action
        '''

        room1 = action[1]
        room2 = action[2]
        door = action[3]

        # Precondition checking
        if doors.has_key(door):
            if ( room1 in doors[door]["connect"] and room2 in doors[door]["connect"] and
            agents["turtlebot"]["at"] == room1 and
            doors[door]["open"]):

                # Call move action
                status = self.move_action(door + "_" + room2)

                # Update world state
                if status:
                    agents["turtlebot"]["at"] == room2
                
                return status
        '''
        approach_desk_refill action executor, checks pre and post conditions of action.
        Calls move_action to move the turtlebot.
        action: list of strings expressing the pddl approach door action
        returns: boolean representing success/failure of action
        '''

        room1 = action[1]
        desk1 = action[2]

        # Precondition checking
        if (rooms.has_key(room1) and 
        desks.has_key(desk1)):
            if (desks[desk1]["in"] == room1 and 
            agents["turtlebot"]["at"] == room1 and
            not agents["turtlebot"]["docked"]):

                # Call move action
                status = self.move_action(desk1)

                # Update world state
                if status:
                    agents["turtlebot"]["facing"] == desk1
                
                return status

        return False

    def dock(self, action):

        '''
        dock action executor, checks pre and post conditions of action.
        Calls dock_action to dock the turtlebot.
        action: list of strings expressing the pddl approach door action
        returns: boolean representing success/failure of action
        '''

        room1 = action[1]
        charger1 = action[2]

        # Precondition checking
        if (rooms.has_key(room1) and 
        chargers.has_key(charger1)):
            if (agents["turtlebot"]["facing"] == "charger_1" and
            agents["turtlebot"]["at"] == room1 and 
            chargers[charger1]["inside"] == room1):

                status = self.dock_action()

                if status:
                    agents["turtlebot"]["docked"] == True
                    agents["turtlebot"]["facing"] == charger1

                return status

        return False

    def undock(self, action):

        '''
        undock action executor, checks pre and post conditions of action.
        Calls undock_action to move the turtlebot.
        action: list of strings expressing the pddl approach door action
        returns: boolean representing success/failure of action
        '''

        room1 = action[1]
        charger1 = action[2]

        if (rooms.has_key(room1) and 
        chargers.has_key(charger1)):
            if (agents["turtlebot"]["facing"] == "charger_1" and
            agents["turtlebot"]["at"] == room1 and 
            chargers[charger1]["inside"] == room1):

                status = self.undock_action()

                if status:
                    agents["turtlebot"]["docked"] == False
                    agents["turtlebot"]["facing"] == charger1

                return status
    
        return False
    
    def approach_charger(self, action):

        '''
        approach_charger action executor, checks pre and post conditions of action.
        Calls move_action to move the turtlebot.
        action: list of strings expressing the pddl approach door action
        returns: boolean representing success/failure of action
        '''
        
        room1 = action[1]
        charger1 = action[2]

        if (rooms.has_key(room1) and 
        chargers.has_key(charger1)):
            if (agents["turtlebot"]["at"] == room1 and 
            chargers[charger1]["inside"] == room1):

                status = self.move_action("dock_approach")

                if status:
                    agents["turtlebot"]["facing"] == charger1

                return status
                
            return False

    def undock_action(self):

        '''
        Service call to undock.
        returns: none
        '''

        # Call to service
        try:
            move_to_start = rospy.ServiceProxy("undock", Trigger)
            response = move_to_start()
            rospy.loginfo(response.message)
        except rospy.ServiceException as e:
            rospy.logerr(e)
        
    def dock_action(self):

        '''
        Service call to dock.
        returns: none
        '''

        # Call to service
        try:
            dock = rospy.ServiceProxy("dock", Trigger)
            response = dock()
            rospy.loginfo(response.message)
        except rospy.ServiceException as e:
            rospy.logerr(e)

        return response.success

    def open_door_action(self):

        '''
        Service call to open_door.
        returns: none.
        '''

        # Call to service
        try:
            open_door = rospy.ServiceProxy("open_door", Trigger)
            response = open_door()
            rospy.loginfo(response.message)
        except rospy.ServiceException as e:
            rospy.logerr(e)

    def move_action(self, loc):

        '''
        Service call to move_action.
        returns: none.
        '''

        # Call to service
        try:
            move_tb = rospy.ServiceProxy("move", Move)
            response = move_tb(waypoints[loc][0], waypoints[loc][1])
            rospy.loginfo(response.message)
        except rospy.ServiceException as e:
            rospy.logerr(e)

            return response.success

    def move_forward_point_five(self):

        '''
        Primative move action. Moves forward 0.5 meters.
        returns: none.
        '''

        vel = Twist()
        vel.linear.x = 0.25

        # Publish 20 times (2 seconds total)
        for i in range(20):
            self.cmd_vel.publish(vel)
            self.rate.sleep()
        
        # Stop turtlebot
        self.cmd_vel.publish(Twist())
        self.rate.sleep()

    def move_forward_one(self):

        '''
        Primative move action. Moves forward 1 meters.
        returns: none.
        '''

        vel = Twist()
        vel.linear.x = 0.25

        # Publish 40 times (4 seconds total)
        for i in range(40):
            self.cmd_vel.publish(vel)
            self.rate.sleep()
        
        # Stop turtlebot
        self.cmd_vel.publish(Twist())
        self.rate.sleep()

    def move_backward_point_five(self):

        '''
        Primative move action. Moves backward 0.5 meters.
        returns: none.
        '''

        vel = Twist()
        vel.linear.x = -0.25

        # Publish 20 times (2 seconds total)
        for i in range(20):
            self.cmd_vel.publish(vel)
            self.rate.sleep()
        
        # Stop turtlebot
        self.cmd_vel.publish(Twist())
        self.rate.sleep()

    def move_backward_one(self):

        '''
        Primative move action. Moves backward 1 meters.
        returns: none.
        '''

        vel = Twist()
        vel.linear.x = -0.25

        # Publish 40 times (4 seconds total)
        for i in range(40):
            self.cmd_vel.publish(vel)
            self.rate.sleep()
        
        # Stop turtlebot
        self.cmd_vel.publish(Twist())
        self.rate.sleep()

    def turn_cc_pi_over_four(self):

        '''
        Primative turn action. Turns pi/4 meters counter clockwise.
        returns: none.
        '''

        vel = Twist()
        vel.angular.z = math.pi / 4

        # Publish 10 times (1 second total)
        for i in range(10):
            self.cmd_vel.publish(vel)
            self.rate.sleep()
        
        # Stop turtlebot
        self.cmd_vel.publish(Twist())
        self.rate.sleep()


    def turn_cc_pi_over_two(self):

        '''
        Primative turn action. Turns pi/2 meters counter clockwise.
        returns: none.
        '''

        vel = Twist()
        vel.angular.z = math.pi / 4

        # Publish 20 times (2 second total)
        for i in range(20):
            self.cmd_vel.publish(vel)
            self.rate.sleep()
        
        # Stop turtlebot
        self.cmd_vel.publish(Twist())
        self.rate.sleep()

    def turn_c_pi_over_four(self):

        '''
        Primative turn action. Turns pi/4 meters clockwise.
        returns: none.
        '''

        vel = Twist()
        vel.angular.z = - math.pi / 4

        # Publish 10 times (1 second total)
        for i in range(10):
            self.cmd_vel.publish(vel)
            self.rate.sleep()
        
        # Stop turtlebot
        self.cmd_vel.publish(Twist())
        self.rate.sleep()


    def turn_cc_pi_over_two(self):

        '''
        Primative turn action. Turns pi/2 meters clockwise.
        returns: none.
        '''

        vel = Twist()
        vel.angular.z = - math.pi / 4

        # Publish 20 times (2 second total)
        for i in range(20):
            self.cmd_vel.publish(vel)
            self.rate.sleep()
        
        # Stop turtlebot
        self.cmd_vel.publish(Twist())
        self.rate.sleep()

    def shutdown(self):

        '''
        Runs on node shutdown.
        returns: none
        '''

        rospy.loginfo("Stopping plan_executor node")
        
        # Stop the turtlebot
        self.cmd_vel.publish(Twist())
        rospy.sleep(1)

if __name__ == "__main__":
    
    try:
        PlanExecutor()
    except:
        rospy.logerr("PlanExecutor failed")