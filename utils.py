import math
import numpy as np

def calculate_angle(a, b, c):
    """
    Tính góc ABC (đơn vị độ)
    
    a, b, c là mediapipe landmarks
    b là đỉnh góc
    """

    # Vector BA
    ba_x = a.x - b.x
    ba_y = a.y - b.y
    ba_z = a.z - b.z

    # Vector BC
    bc_x = c.x - b.x
    bc_y = c.y - b.y
    bc_z = c.z - b.z

    # Dot product
    dot_product = (
        ba_x * bc_x +
        ba_y * bc_y +
        ba_z * bc_z
    )

    # Magnitude BA
    magnitude_ba = math.sqrt(
        ba_x ** 2 +
        ba_y ** 2 +
        ba_z ** 2
    )

    # Magnitude BC
    magnitude_bc = math.sqrt(
        bc_x ** 2 +
        bc_y ** 2 +
        bc_z ** 2
    )

    # Tránh chia cho 0
    if magnitude_ba == 0 or magnitude_bc == 0:
        return 0

    # Cos(theta)
    cos_angle = dot_product / (magnitude_ba * magnitude_bc)

    # Fix floating point
    cos_angle = max(-1, min(1, cos_angle))

    # Radian -> Degree
    angle = round(math.degrees(math.acos(cos_angle)) / 180.0, 2)

    return angle


def calculate_finger_angle(start1, end1, start2, end2):

    # Vector 1
    v1_x = end1.x - start1.x
    v1_y = end1.y - start1.y
    v1_z = end1.z - start1.z

    # Vector 2
    v2_x = end2.x - start2.x
    v2_y = end2.y - start2.y
    v2_z = end2.z - start2.z

    # Dot product
    dot_product = (
        v1_x * v2_x +
        v1_y * v2_y +
        v1_z * v2_z
    )

    # Magnitude
    mag1 = math.sqrt(
        v1_x**2 +
        v1_y**2 +
        v1_z**2
    )

    mag2 = math.sqrt(
        v2_x**2 +
        v2_y**2 +
        v2_z**2
    )

    if mag1 == 0 or mag2 == 0:
        return 0

    cos_angle = dot_product / (mag1 * mag2)

    cos_angle = max(-1, min(1, cos_angle))

    angle = round(math.degrees(math.acos(cos_angle)) / 180.0, 2)
    return angle

def normalize(v):
    norm = np.linalg.norm(v)
    if norm == 0:
       return np.zeros_like(v)
    return v / norm


def compute_palm_orientation(landmarks):
    """
    landmarks: list hoặc array shape (21, 3)
               MediaPipe Hand landmarks
    return:
        dict chứa 3 vector:
        - direction (wrist -> middle MCP)
        - spread (index MCP -> pinky MCP)
        - normal (cross product)
    """

    # ===== Key points =====
    wrist = np.array(landmarks[0])

    index_mcp = np.array(landmarks[5])
    middle_mcp = np.array(landmarks[9])
    pinky_mcp = np.array(landmarks[17])

    # ===== Vector 1: hướng dọc bàn tay =====
    direction = middle_mcp - wrist
    direction = normalize(direction)

    # ===== Vector 2: chiều ngang bàn tay =====
    spread = pinky_mcp - index_mcp
    spread = normalize(spread)

    # ===== Vector 3: pháp tuyến lòng bàn tay =====
    normal = np.cross(direction, spread)
    normal = normalize(normal)

    # (optional) làm trực chuẩn lại spread để đảm bảo orthogonal
    spread = np.cross(normal, direction)
    spread = normalize(spread)

    return {
        "direction": direction,
        "spread": spread,
        "normal": normal
    }