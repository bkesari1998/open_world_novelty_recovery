#!/usr/bin/env python

# ON TURTLEBOT
# roslaunch coordinate_navigation turtlebot.launch
# roslaunch coordinate_navigation plan_1_start.launch waypoints_file:=plan_1_curtain_novelty_waypoints.yaml

# ON REMOTE
# roslaunch coordinate_navigation remote.launch

# ON TURTLEBOT
# rosrun coordinate_navigation manager.py

import pickle
import rospy
import os
import numpy as np
from coffee_bot_srvs.srv import Action, Goal, Move, PrimitiveAction
from geometry_msgs.msg import PoseWithCovarianceStamped, PoseStamped

from kobuki_msgs.msg import BumperEvent

from nav_msgs.srv import GetPlan
from std_msgs.msg import Bool
from std_srvs.srv import Trigger

from tf.transformations import quaternion_multiply, quaternion_inverse

from learn_exec import *

class Manager(object):
    
    def __init__(self):
        
        rospy.init_node("manager")
        
        rospy.wait_for_service("/action_executor")
        rospy.wait_for_service("/move_base/make_plan")
        rospy.loginfo("action_executor service active")
        
        self.object_list = rospy.get_param("object_list")
        self.waypoint_list = rospy.get_param("waypoint_list")
        self.waypoint_loc = rospy.get_param("waypoints")

        # Get agent high level state information
        self.agent_state = rospy.get_param("agents/turtlebot")
        self.update_state_subscriber = rospy.Subscriber("update_state", Bool, self.update_state_handler)

        # Get plan from plan file
        self.plan_file_path = rospy.get_param("plan_file")
        plan = self.read_plan(self.plan_file_path)

        self.action_executor_client = rospy.ServiceProxy("action_executor", Action)
        self.pddl_problem_gen_client = rospy.ServiceProxy("problem_gen", Goal)
        self.pddl_goal = ["facing desk_1"]
        self.make_plan_client = rospy.ServiceProxy("move_base/make_plan", GetPlan)
        self.move_client = rospy.ServiceProxy("move", Move)
        self.primitive_move_client = rospy.ServiceProxy("primitive_move_actions", PrimitiveAction)
        self.state_confirmer = rospy.ServiceProxy("confirm_state", Trigger)

        self.primitive_moves = {"forward": 0, "turn_cc": 1, "turn_c": 2}
        self.primitive_moves_list = [["move", "forward"], ["move", "turn_cc"], ["move", "turn_c"]]
        
        # # Bumper
         # Instantiate bumper listner
        bumper_listner = rospy.Subscriber("/mobile_base/events/bumper", BumperEvent, self.bumper_handler)
        # self.bumper_pressed = 0
        # self.bumper_time = rospy.Time.now()
        # find the file for loading
        self.load_model_flag = False
        self.episodes = 0
        file_names = os.listdir("/home/mulip/catkin_ws/src/coffee-bot/coordinate_navigation/scripts/models")
        ep_nums = []
        if file_names:
            for file_name in file_names:
                ep_num = file_name.split(".")[0].split("_")[-1] # episode number
                ep_nums.append(int(ep_num))
                print ("Episode numbers", ep_nums)
            self.episodes = 0 + (max(ep_nums))
            self.load_model_flag = True
        self.steps = 0
        actions_list = []
        states_list = []
        failed_operator_name = "approach_charger_1_doorway_1_lab"
        self.update_state_handler((Bool(True)))
        init_obs = np.array(self.build_learner_state())
        print ("self.episodes = ", self.episodes)
        learner = Learner(failed_operator_name, init_obs, self.primitive_moves, episode_num = self.episodes, load_model_flag= self.load_model_flag)
        learner.agent.set_explore_epsilon(params.MAX_EPSILON)
        for episode in range(params.MAX_EPISODES):
            action_list = []
            state_list = []
            ready = "n"

            while ready != "y":
                ready = raw_input("Ready for next episode? (y/n)")
                self.state_confirmer()
                self.update_state_handler((Bool(True)))

            
            obs = np.array(self.build_learner_state())
            self.episodes+=1
            print ("Episodes -->>", self.episodes)
            self.timesteps = 0
            while True:
                action_ = raw_input("Action number: ")
                print(action_)
                while action_ not in ["0", "1", "2"]:
                    action_ = raw_input("Action number: ")
                learner_action = learner.get_action(obs, False, int(action_))
                # learner_action = learner.get_action(obs)
                print("Learner action:" + str(learner_action))
                self.action_executor_client(self.primitive_moves_list[learner_action])
                self.timesteps += 1
                print ("timestep -->>", self.timesteps)
                self.update_state_handler((Bool(True)))
                obs = np.array(self.build_learner_state())
                # print (obs.shape)
                state_list.append(obs)
                # print ("obs = ", obs)
                action_list.append(learner_action)

                if "hallway" in self.agent_state["at"] and "nothing" in self.agent_state["facing"]: # done is True
                    print ("Goal state reached!")
                    learner.agent.update_parameters()
                    learner.agent.update_parameters()
                    self.move_client("exploration_reset") # reset to begin state
                    break
            actions_list += action_list
            states_list += state_list
        actions_list = np.array(actions_list)
        states_list = np.array(states_list)
        learner.agent.save_model(failed_operator_name, episode_num=self.episodes)
        
        path = "/home/mulip/catkin_ws/src/coffee-bot/coordinate_navigation/scripts/data/data" +str(self.episodes)+ ".pickle"
        memory = {'states': states_list, 'actions': actions_list}
        f = open(path, 'wb')
        pickle.dump(memory, f)
        f.close()

    def bumper_handler(self, msg):
        if msg.state == BumperEvent.PRESSED:
            rospy.loginfo("Oops, hit something!")
            self.primitive_move_client("backward")

    def execute_plan(self, plan):

        for action in plan:
            res = self.action_executor_client(action)

            if not res.success:
                rospy.loginfo(action[0])
                rospy.loginfo(res.message)
                return [False, action]
        
        return [True, []]

    def read_plan(self, plan_file_path):

        f = open(plan_file_path, "r")

        # Get lines of file
        lines = f.readlines()


        # Only get plan lines
        plan_lines = lines[3: -3]

        # Remove timestamp from plan lines
        for i in range(len(plan_lines)):

            plan_lines[i] = plan_lines[i][plan_lines[i].index("(") + 1: plan_lines[i].index(")")]

        # Return plan, with each action split by space char
        plan = []
        for line in plan_lines:
            plan.append(line.split(" "))

        f.close()

        return plan

    def build_learner_state(self):

        learner_state = [0] * 3

        if "lab" in self.agent_state["at"]:
            learner_state[0] = 1
        elif "hallway" in self.agent_state["at"]:
            learner_state[1] = 1
        else:
            learner_state[2] = 1
        
        facing_indecies = dict(zip(self.object_list, np.arange(len(self.object_list))))
        facing_index = facing_indecies[self.agent_state["facing"][0]]
        facing_state = [0] * len(self.object_list)
        facing_state[facing_index] = 1

        learner_state = learner_state + facing_state

        # Add distances and orientation to all static objects, add true false for 
        odom_pose_with_cov_stamped = rospy.wait_for_message("amcl_pose", PoseWithCovarianceStamped, rospy.Duration(1))
        odom_pose = odom_pose_with_cov_stamped.pose.pose

        for waypoint in self.waypoint_list:
            pose = self.waypoint_loc[waypoint]

            dxdy = []
            # append x and y dist to list 
            dxdy.append(pose[0][0] - odom_pose.position.x)
            dxdy.append(pose[0][1] - odom_pose.position.y)

            rot = []
            # append orientation info
            q_1_inverse = quaternion_inverse(pose[1])
            q_0 = [odom_pose.orientation.x, odom_pose.orientation.y, odom_pose.orientation.z, odom_pose.orientation.w]
            rel_orientation = quaternion_multiply(q_0, q_1_inverse)
            rot.append(rel_orientation[2])
            rot.append(rel_orientation[3])

            # Add dxdy and rot to learner state
            learner_state = learner_state + dxdy + rot
            if waypoint != "novel_object": # Don't need plan_exists to novel object
                odom_pose_stamped = self.pose_with_covariance_stamed_to_pose_stamped(odom_pose_with_cov_stamped)
                waypoint_pose_stamped = self.waypoint_to_pose_stamped(pose)

                plan = self.make_plan_client(odom_pose_stamped, waypoint_pose_stamped, 0.25)
                
                if len(plan.plan.poses) > 0:
                    learner_state.append(1)
                else:
                    learner_state.append(0)

        return learner_state


    def pose_with_covariance_stamed_to_pose_stamped(self, pose):
        if not isinstance(pose, PoseWithCovarianceStamped):
            return PoseStamped()
        
        pose_stamped = PoseStamped()
        pose_stamped.header = pose.header
        pose_stamped.pose = pose.pose.pose

        return pose_stamped

    def waypoint_to_pose_stamped(self, waypoint):
    
        pose_stamped = PoseStamped()
        pose_stamped.header.frame_id = "map"
        pose_stamped.header.stamp = rospy.Time.now()

        pose_stamped.pose.position.x = waypoint[0][0]
        pose_stamped.pose.position.y = waypoint[0][1]

        pose_stamped.pose.orientation.z = waypoint[1][2]
        pose_stamped.pose.orientation.w = waypoint[1][3]

        return pose_stamped

    def generate_plan(self, goal_state):

        pass

    def instantiate_learner(self, learner_state, action):

        pass
        
    def update_state_handler(self, msg):
        if msg.data == True:
            self.agent_state = rospy.get_param("agents/turtlebot")
            rospy.loginfo(self.agent_state["at"])
            rospy.loginfo(self.agent_state["facing"])




if __name__ == "__main__":
    Manager()