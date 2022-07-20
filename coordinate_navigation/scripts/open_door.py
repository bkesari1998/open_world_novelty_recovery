#!/usr/bin/env python

import rospy
import os
from std_msgs.msg import Bool
from std_srvs.srv import Trigger

import world_state

class OpenDoor(object):

    def __init__(self):

        # Initialize node
        rospy.init_node("open_door", anonymous=False)
        rospy.loginfo("open_door node active")
        rospy.on_shutdown(self.shutdown)

        # Initialize service
        self.open_door_srv = rospy.Service("/open_door", Trigger, self.open_door)
        rospy.loginfo("open_door service active")

        self.door_open = False

        while not rospy.is_shutdown():
            rospy.spin()

    def set_door_open(self, msg):
        """
        Setter for door_open
        returns: none
        """
        rospy.loginfo("recieved at msg")
        self.door_open = msg.data

    def open_door(self, req):
        """
        Service request handler.
        req: Trigger object.
        returns: Service response.
        """

        door_sub = rospy.Subscriber("at1", Bool, self.set_door_open)
        rospy.loginfo(self.door_open)

        while not self.door_open:

            os.system("roslaunch coordinate_navigation open_door.launch")
            # Sleep for 5 seconds after asking to open door
            rospy.sleep(5)
            
            rospy.loginfo(self.door_open)
    
        door_sub.unregister()
        return True, "Door is open"

    def shutdown(self):
        """
        Called on node shutdown.
        """

        rospy.loginfo("Stopping open_door node")

if __name__ == "__main__":
    try:
        OpenDoor()
    except:
        rospy.logerr("OpenDoor failed")
