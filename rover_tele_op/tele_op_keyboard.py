#!/usr/bin/env python3
import sys
import threading
import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32MultiArray
import termios
import tty

GRANULARITY = 10
TIMEOUT = 5.0 # In seconds

def getKey(settings):
        tty.setraw(sys.stdin.fileno())
        key = sys.stdin.read(1)
        if key == '\x1b':
            key += sys.stdin.read(2)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        return key

instructions = """
Teleop node started (continuous drive mode).
Use the arrow keys to drive:
    Up Arrow    : move forward
    Down Arrow  : move backward
    Left Arrow  : turn left
    Right Arrow : turn right

's' : Stop (set drive commands to zero)
O   : Increase global speed (linear and angular)
P   : Decrease global speed
1-7 : Increment arm motor
QWERTYU : Decrement arm motor

CTRL-C to quit.
"""

class Teleop(Node):
    def __init__(self):
        super().__init__('teleop_twist_keyboard')
        self.speed = 0.35
        self.motors = [0] * 7
        self.x = 0.0
        self.th = 0.0
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.motor_pub = self.create_publisher(Int32MultiArray, '/joint_states', 10)
        self.last_keypress_time = time.time()
        self.create_timer(0.05, self.timer_callback)

    def timer_callback(self):
        current_time = time.time()
        if current_time - self.last_keypress_time > TIMEOUT:
            self.x = 0.0
            self.th = 0.0
        twist = Twist()
        twist.linear.x = self.x * self.speed
        twist.angular.z = self.th * self.speed
        self.cmd_pub.publish(twist)

        motor_msg = Int32MultiArray()
        motor_msg.data = self.motors
        self.motor_pub.publish(motor_msg)

def main():
    settings = termios.tcgetattr(sys.stdin)
    rclpy.init()
    teleop = Teleop()
    spinner = threading.Thread(target=rclpy.spin, args=(teleop,))
    spinner.start()

    print(instructions)

    try:
        while True:
            key = getKey(settings)
            teleop.last_keypress_time = time.time()
            if key == '\x1b[A': 
                teleop.x = 1.0
                teleop.th = 0.0
            elif key == '\x1b[B':
                teleop.x = -1.0
                teleop.th = 0.0
            elif key == '\x1b[C':
                teleop.th = -1.0
                teleop.x = 0.0
            elif key == '\x1b[D':
                teleop.th = 1.0
                teleop.x = 0.0
            elif key.lower() == 's':
                teleop.x = 0.0
                teleop.th = 0.0
                print("Stop command issued.")
            elif key.lower() == 'o':
                teleop.speed *= 1.1
                print(f"Speed increased: {teleop.speed:.3f}")
            elif key.lower() == 'p':
                teleop.speed *= 0.9
                print(f"Speed decreased: {teleop.speed:.3f}")
            elif key in "12345":
                idx = int(key) - 1
                teleop.motors[idx] += GRANULARITY
                print(f"Motor {idx+1} increased to {teleop.motors[idx]}")
            elif key == "6":
                teleop.motors[5] += GRANULARITY
                teleop.motors[6] += GRANULARITY
                print(f"Motors 5, 6 increased to {teleop.motors[5]}, {teleop.motors[6]}")
            elif key == "7":
                teleop.motors[5] += GRANULARITY
                teleop.motors[6] -= GRANULARITY
                print(f"Motors 5, 6 changed to {teleop.motors[5]}, {teleop.motors[6]}")
            elif key.upper() in "QWERT":
                idx = "QWERT".index(key.upper())
                teleop.motors[idx] -= GRANULARITY
                print(f"Motor {idx+1} decreased to {teleop.motors[idx]}")
            elif key.upper() == 'Y':
                teleop.motors[5] -= GRANULARITY
                teleop.motors[6] -= GRANULARITY
                print(f"Motors 5, 6 decreased to {teleop.motors[5]}, {teleop.motors[6]}")
            elif key.upper() == 'U':
                teleop.motors[5] -= GRANULARITY
                teleop.motors[6] += GRANULARITY
                print(f"Motors 5, 6 changed to {teleop.motors[5]}, {teleop.motors[6]}")
            elif key == '\x03':  # CTRL-C
                break
    except Exception as e:
        print(e)
    finally:
        teleop.x = 0.0
        teleop.th = 0.0
        time.sleep(0.1)
        rclpy.shutdown()
        spinner.join()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

if __name__ == '__main__':
    main()

# #!/usr/bin/env python3
# import rclpy
# from rclpy.node import Node
# from geometry_msgs.msg import Twist
# from std_msgs.msg import Int32MultiArray
# from pynput.keyboard import Key, Listener

# GRANULARITY = 10

# class Teleop(Node):
#     def __init__(self):
#         super().__init__("pynput_teleop_twist_keyboard_node")

#         self.speed = 0.35
#         self.motors = [0] * 7
#         self.x = 0.0
#         self.th = 0.0
#         self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
#         self.motor_pub = self.create_publisher(Int32MultiArray, '/joint_states', 10)
#         timer_period = 0.05
#         self.timer = self.create_timer(timer_period, self.publish_commands)

#         self.listener = Listener(on_press=self.on_press, suppress=True)
#         self.listener.start()

#         self.get_logger().info("Teleop node started (continuous drive mode).")
#         self.get_logger().info("Use arrow keys to drive, 's' to stop.")
#         self.get_logger().info("Press O (or o) to speed up, P (or p) to slow down.")
#         self.get_logger().info("Use keys 1–7 to increment motors and QWERTYU to decrement them.")

#     def publish_commands(self):
#         twist = Twist()
#         twist.linear.x = self.x * self.speed
#         twist.angular.z = self.th * self.speed
#         self.cmd_pub.publish(twist)

#         motor_msg = Int32MultiArray()
#         motor_msg.data = self.motors
#         self.motor_pub.publish(motor_msg)

#     def on_press(self, key):
#         self.get_logger().info("Detected press.")

#         try:
#             if hasattr(key, 'char') and key.char is not None:
#                 char = key.char
#                 if char in ['O', 'o']:
#                     self.speed *= 1.1
#                     self.get_logger().info(f"Speed increased: {self.speed:.3f}")
#                 elif char in ['P', 'p']:
#                     self.speed *= 0.9
#                     self.get_logger().info(f"Speed decreased: {self.speed:.3f}")
#                 elif char in "1234567":
#                     index = int(char) - 1
#                     self.motors[index] += GRANULARITY
#                     self.get_logger().info(f"Motor {index+1} increased to {self.motors[index]}")
#                 elif char.upper() in "QWERTYU":
#                     index = "QWERTYU".index(char.upper())
#                     self.motors[index] -= GRANULARITY
#                     self.get_logger().info(f"Motor {index+1} decreased to {self.motors[index]}")
#                 elif char in ['s', 'S']:
#                     self.x = 0.0
#                     self.th = 0.0
#                     self.get_logger().info("Stop command issued.")
#             else:
#                 if key == Key.up:
#                     self.x = 1.0
#                     self.th = 0.0
#                 elif key == Key.down:
#                     self.x = -1.0
#                     self.th = 0.0
#                 elif key == Key.left:
#                     self.th = 1.0
#                     self.x = 0.0
#                 elif key == Key.right:
#                     self.th = -1.0
#                     self.x = 0.0
#         except Exception as e:
#             self.get_logger().error(f"Error processing key: {e}")

# def main(args=None):
#     rclpy.init(args=args)
#     teleop = Teleop()
#     rclpy.spin(teleop)
#     teleop.destroy_node()
#     rclpy.shutdown()

# if __name__ == '__main__':
#     main()
