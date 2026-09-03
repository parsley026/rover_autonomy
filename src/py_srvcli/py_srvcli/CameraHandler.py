from py_srvcli.ArucoPositionEstimation import ArucoPositionEstimation
from py_srvcli.CamThread import CamThread, getStreamThread
import numpy as np
import cv2
from py_srvcli.geo.angles_module import prosta_b_tylko_kat_ox
import os
import math
import pandas as pd

CONST_MARKER_ID = 50
SIMULATION_MODE = True  # Ustawienie trybu symulacji


"""
TODO:
- uprzadkowac kod ?
"""

class CameraHandler:

    if SIMULATION_MODE:
        markerLength = 0.21  # Długość markera w trybie symulacji
    else:
        markerLength = 0.15  # Długość markera w trybie rzeczywistym

    x_offset_to_rover_torso = 0 # -0.079 
    y_offset_to_rover_torso = 0 # 0.21 
    z_offset_to_rover_torso = 0 # 0.4 

    # WSPÓŁRZĘDNE ROGÓW KODU 3D
    half = markerLength / 2.0
    obj_points = np.array([
        [-half,  half, 0], 
        [ half,  half, 0], 
        [ half, -half, 0], 
        [-half, -half, 0]  
    ], dtype=np.float32)

    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(script_dir, 'metadata/ERC2026.csv')

        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_100)
        
        # Obsługa nowej (>= 4.7) i starej (< 4.7) wersji OpenCV
        if hasattr(cv2.aruco, 'ArucoDetector'):
            self.detector_params = cv2.aruco.DetectorParameters()
            self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.detector_params)
            self.is_new_cv = True
        else:
            self.is_new_cv = False

        # MACIERZ KAMERY
        if SIMULATION_MODE:
            self.camera_matrix = np.array([
                [697.5, 0.0,   960.0], 
                [0.0,   697.5, 540.0], 
                [0.0,   0.0,   1.0]
            ], dtype=np.float32)

            self.dist_coeffs = np.zeros((4, 1), dtype=np.float32)
        else:
            self.camera_matrix = np.array([
                [1156.487675, 0, 945.011582],
                [0, 1163.783105, 525.629859],
                [0, 0,  1]
                ], dtype=np.float32)

            self.dist_coeffs = np.array([
                [-0.317971004, 0.105749378, 0.001182580, -0.003109585, -0.017361084]
                ], dtype=np.float32)


   
        db = pd.read_csv(data_path)
        if db.empty or db is None:  
            print("Blad odczytu pliku CSV z pozycjami markerów.")
            exit(1)

        # Wczytanie pozycji
        self.world_points = {
            int(row['ID'][1:]): [row['X'], row['Y'], row['Z']] 
            for _, row in db.iterrows() if (row['ID'].startswith('S') or row['ID'].startswith('L') or row['ID'].startswith('W') or row['ID'].startswith('P'))
        }
        
        # INICJALIZACJA ESTYMATORA 
        self.aruco_estimator = ArucoPositionEstimation(self.world_points)
        
        self.cached_detected_markers = []
        self.cached_angles = []

        # klasa pomocnicza, gdy są różne wersję openCV
        class DummyDetector:
            def __init__(self, handler):
                self.handler = handler
            def detectMarkers(self, gray):
                return cv2.aruco.detectMarkers(gray, self.handler.aruco_dict)
        
        self.detector = DummyDetector(self)
  
    def setup_camera(self, ip: str, dist_coeffs: np.ndarray, cam_matix: np.ndarray, offset:float, name: str = "") -> CamThread:
        cam = getStreamThread(ip)
        cam.name = name
        cam.dist_coeffs = dist_coeffs
        cam.angle_offset = offset
        cam.cam_matrix = cam_matix
        return cam

    def detect_markers_centre_rover(self, frame) -> bool:
        if frame is None or isinstance(frame, bool) or not isinstance(frame, np.ndarray) or frame.size == 0:
            return False
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # użycie odpowiedniej funkcji w zależności od wersji openCV
        if self.is_new_cv:
            corners, ids, _ = self.detector.detectMarkers(gray)
        else:
            corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict)

        if ids is not None and len(ids) > 0:
            aruco_array = list(zip(corners, ids.flatten().tolist()))
            best_measurements = {}

            # pętla po wszytkich znacznikach
            for single_aruco_corners, marker_id in aruco_array:
                # korekta numeru znacznika (zaczynają się od 51 więc odejmowane jest 50)
                marker_id = marker_id - CONST_MARKER_ID  

                if marker_id not in self.world_points:
                    continue 

                # wymuszenie żeby tablica była jako 1 zwarty blok w RAM
                # img_points - rogi markera na obrazie
                # safe_obj_points - tak jak punkty powinny być ustawione (według podanej wcześniej długości markera)
                img_points = np.ascontiguousarray(single_aruco_corners[0], dtype=np.float32)
                safe_obj_points = np.ascontiguousarray(self.obj_points, dtype=np.float32)

                # bool, wektor rotacji i translajci
                success, rvec, tvec = cv2.solvePnP(
                    safe_obj_points, 
                    img_points, 
                    self.camera_matrix, 
                    self.dist_coeffs
                )
        
                if success:
                    tvec_flat = tvec.flatten()
                    tx, ty, tz = tvec_flat[0], tvec_flat[1], tvec_flat[2]

                    # obliczenie dystansu (bez uwzględnienia Z w odległości -> Z wychodzi dokładniej)
                    distance = np.linalg.norm([tvec[0], tvec[2]])
                    
                    angle3D = math.degrees(math.atan(tx / math.sqrt(tz**2 + ty**2)))
                    angle2D = math.degrees(math.atan2(tx, tz))

                    # Przekształcenie wektora rotacji na macierz rotacji oraz obliczenie pozucji kamery
                    R_matrix, _ = cv2.Rodrigues(rvec) 
                    camera_position = -np.matrix(R_matrix).T * np.matrix(tvec)

                    # otrzymanie pozycji łazika poprzez dodanie offsetów kamery
                    rover_x = camera_position[0, 0] + self.x_offset_to_rover_torso
                    rover_y = camera_position[2, 0] + self.y_offset_to_rover_torso
                    rover_z = camera_position[1, 0] + self.z_offset_to_rover_torso

                    # wybranie najelpszej ścianki znacznika, gdy widać więcej niż jedną
                    if marker_id not in best_measurements or distance < best_measurements[marker_id]['distance']:
                        best_measurements[marker_id] = {
                            'distance': distance,
                            'angle2D': angle2D,
                            'angle3D': angle3D,
                            'rx': rover_x,
                            'ry': rover_y,
                            'rz': rover_z
                        }

            # Przekazanie danych do estymatora
            for m_id, data in best_measurements.items():
                self.cached_angles.append([data['angle2D'], data['angle3D'], self.world_points[m_id][0:3]])
                
                # Format krotki, którego wymaga calculate_position: 
                # (m_id, dist, r_x, r_y, r_z)
                self.cached_detected_markers.append((
                    m_id, 
                    data['distance'], 
                    data['rx'], 
                    data['ry'], 
                    data['rz']
                ))
        
        # self.cached_detected_markers.sort(key=lambda x: x[1])
        # print("Wykryte markery:\n" + "\n".join(f"ID: {m[0]}, dystans: {m[1]:.2f}" for m in self.cached_detected_markers))

        return True

    def choose_smallest_angle(self):
        """
            Funkcja zwraca kąt najbliższy 0 spośród znalezionych markrów (najbardziej na wprost łazika)
        """
        if not self.cached_angles:
            return None
        if len(self.cached_angles) == 1:
                return self.cached_angles[0]
        return min(self.cached_angles, key=lambda x: abs(x[1]))
    
    def estimate_position_for_client(self, frame, prev_position: np.ndarray, reset_cached_data: bool):
        if reset_cached_data:
            self.cached_detected_markers = []
            self.cached_angles = []

        self.detect_markers_centre_rover(frame)
        best_angle = self.choose_smallest_angle()
        
        if len(self.cached_detected_markers) > 0 and best_angle is not None:
            
            # obliczenie pozycji 
            calculated_pos = self.aruco_estimator.calculate_position(self.cached_detected_markers, prev_position)
            
            if calculated_pos is not None:
                rover_x = calculated_pos[0]
                rover_y = calculated_pos[1]
                rover_z = calculated_pos[2]

                # Wyliczenie Z_angle (Yaw angle)
                z_angle = prosta_b_tylko_kat_ox(
                    np.array([rover_x, rover_y]),  
                    best_angle[2][0:2], 
                    best_angle[0], 
                    clockwise=False
                )
                
                rad_angle = np.deg2rad(z_angle)

                # uwzglednienie offestu do kamery na bazie rotacji osi pionowej
                direction_vec = [np.cos(rad_angle), np.sin(rad_angle)]
                rover_x = rover_x + direction_vec[0] * -0.4
                rover_y = rover_y + direction_vec[1] * -0.4

                #print(f"[ESTYMATOR WYNIK] X: {rover_x:.2f}, Y: {rover_y:.2f}, Z: {rover_z:.2f}, Yaw: {z_angle:.2f}°")
                return rover_x, rover_y, rover_z, z_angle, True
            else:
                print(f"Błąd wyliczania pozycji. calculated_pos: {calculated_pos}")
        else:
            print("best angle:", best_angle, '\n', "cached markers:", self.cached_detected_markers)
        return None, None, None, None, False

