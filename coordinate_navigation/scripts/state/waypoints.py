
waypoints = {
    "lab_door_lab_lab": [[-0.484, -3.657, 0], [ 0, 0, -0.637, 0.771]],
    "lab_door_lab_kitchen": [[-0.484, -3.657, 0], [ 0, 0, 0.765, 0.644]],
    "lab_door_kitchen_kitchen": [[0.114, -5.891, 0], [ 0, 0, 0.765, 0.644]],
    "lab_door_kitchen_lab": [[0.114, -5.891, 0], [ 0, 0, -0.637, 0.771]],
    "desk_refill": [[-2.900, -8.369, 0], [0, 0, 0.769, 0.639]],
    "dock_approach": [[-0.570, 1.119, 0], [ 0, 0, 0, 1]]
}

state_check = {
    "at_lab_door_lab_lab": {"tag": "at3", "distance": 3},
    "at_lab_door_lab_kitchen": {"tag": "at15", "distance": 3},
    "at_lab_door_kitchen_kitchen": {"tag": "at4", "distance": 1.5},
    "at_lab_door_kitchen_lab": {"tag": "at4", "distance": 1.5},
    "at_dock_approach": {"tag": "at0", "distance": 2},
    "at_desk_refill": {"tag": "at9", "distance": 2},
    "lab_door_lab_open": {"tag": "at4", "in_view": True},
    "lab_door_kitchen_open": {"tag": "at15", "in_view": True},
}