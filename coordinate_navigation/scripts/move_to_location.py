#!/usr/bin/env python 

from http import client
import rospy
import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from actionlib_msgs.msg import GoalStatus
from coffee_bot_srvs.srv import Move
from std_srvs.srv import Trigger

class MoveTB():
    def __init__(self):

        rospy.init_node("move_tb", anonymous=False)

        self.move_tb_srv = rospy.Service("/move", Move, self.move_tb)

        # Create a SimpleActionClient of a move_base action type and wait for server
        self.simple_action_client = actionlib.SimpleActionClient("move_base", MoveBaseAction)
        self.simple_action_client.wait_for_server()

        while not rospy.is_shutdown():
            rospy.spin()

    def assign_goal(self, pose, orientation):
        
        # Create MoveBaseGoal object from input
        goal_pose = MoveBaseGoal()
        goal_pose.target_pose.header.frame_id = 'map'
        goal_pose.target_pose.pose.position.x = pose[0]
        goal_pose.target_pose.pose.position.y = pose[1]
        goal_pose.target_pose.pose.position.z = pose[2]
        goal_pose.target_pose.pose.orientation.x = orientation[0]
        goal_pose.target_pose.pose.orientation.y = orientation[1]
        goal_pose.target_pose.pose.orientation.z = orientation[2]
        goal_pose.target_pose.pose.orientation.w = orientation[3]

        return goal_pose

    def move_tb(self, req):

        # Assign the turtlebot's goal
        tb_goal = self.assign_goal(req.final_pose, req.final_orientation)
        self.simple_action_client.send_goal(tb_goal)
        self.simple_action_client.wait_for_result()

        if (self.simple_action_client.get_state() == GoalStatus.SUCCEEDED):
            return True, "Turtlebot successfully navigated to goal position"
        else:
            return False, "Turtlebot unable to navigate to goal position"

if __name__ == "__main__":
    try:
        MoveTB()
    except:
        rospy.logerr("MoveTB failed")