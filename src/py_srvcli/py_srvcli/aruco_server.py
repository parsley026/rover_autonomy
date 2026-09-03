import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image       # Wiadomość z obrazem z symulacji
from cv_bridge import CvBridge          # Tłumacz ROS <-> OpenCV
import os
import numpy as np
from tutorial_interfaces.srv import ArucoEstimate
import cv2
from py_srvcli.CameraHandler import CameraHandler 

class ArucoPositionServer(Node):
    def __init__(self):
        super().__init__('aruco_position_server')
        
        # Inicjalizacja narzędzia do konwersji obrazu
        self.bridge = CvBridge()
        self.latest_frame = None

        self.image_counter = 0
        
        # Inicjalizacja CameraHandler, który będzie przetwarzał obrazy i wyliczał pozycję
        self.handler = CameraHandler()
        
        # SUBSKRYPCJA KAMERY Z SYMULACJI
        # self.image_subscriber = self.create_subscription(
        #     Image,
        #     '/hivision/camera/image_raw', 
        #     self.image_callback,
        #     10
        # )
        
        self.subscription = self.create_subscription(
            Image,
            '/camera_publisher/image_raw',  # Zmień, jeśli CameraNode działa z inną przestrzenią nazw
            self.image_callback,
            qos_profile_sensor_data # Ważne dla strumieni wideo, zapobiega zatykaniu kolejki
        )
        self.subscription

        self.pose_publisher = self.create_publisher(ArucoEstimate, '/aruco/estimated_pose', 10)
        self.get_logger().info("Gotowy do pracy. Publikuję pozycję!")

    def image_callback(self, msg: Image):
        """
        Ta funkcja działa cały czas i odbiera obraz z symulatora.
        """
        try:
            # Konwersja obrazu ROS na OpenCV
            self.latest_frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            
            # Tworzenie kopii do wyświetlenia na żywo
            display_frame = self.latest_frame.copy()
            
            # rysowanie wykrytego ArUco na żywo na podglądzie
            gray = cv2.cvtColor(display_frame, cv2.COLOR_BGR2GRAY)
            corners, ids, _ = self.handler.detector.detectMarkers(gray)
            if ids is not None and len(ids) > 0:
                cv2.aruco.drawDetectedMarkers(display_frame, corners, ids)
                
            # Wyświetlenie informacji na ekranie podglądu
            cv2.putText(display_frame, "Nacisnij 't', aby policzyc pozycje!", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # wyswietlenie okna podglądu
            cv2.imshow("Sterowanie i Podglad - Symulacja Gazebo", display_frame)
            
            # NASŁUCHIWANIE KLAWISZA (1 milisekunda oczekiwania)
            # Sprawdzamy, czy wciśnięto klawisz 't' lub 'T'
            key = cv2.waitKey(1) & 0xFF
            if key == ord('t') or key == ord('T'):
                self.get_logger().info("--> Wciśnięto 't'! Analizuję aktualną klatkę...")
                #cv2.imwrite(f"/home/dudziu/Pictures/arucos//frameForAnalysis{len(os.listdir('/home/dudziu/Pictures/arucos/'))}.png", self.latest_frame)  # prowizoryzcne zapisanie klatlki do pliku do pozniejszej analizy
                #print("Zapisano aktualną klatkę do pliku 'frameForAnalysis.png'.")
                #self.perform_manual_analysis()
                fake_request = type('FakeRequest', (object,), {
                    'prev_x': 0.0,
                    'prev_y': 0.0,
                    'prev_z': 1.1,
                    'reset_cached_data': True
                })()
                fake_response = type('FakeResponse', (object,), {})()
                self.estimate_callback(fake_request, fake_response)
                if fake_response.total_success:
                    print(f"\n[INFO] Wyniki analizy z klatki:\n  Pozycja X: {fake_response.x:.3f} m\n  Pozycja Y: {fake_response.y:.3f} m\n  Wysokość Z: {fake_response.z:.3f} m\n  Kąt łazika (Yaw): {fake_response.z_angle:.2f}°\n Kąt łazika (Pitch): {fake_response.y_angle:.2f}°\n  Kąt łazika (Roll): {fake_response.x_angle:.2f}°\n Liczba wykrytych ArUco w bazie: {fake_response.arucos}\n  Sukces analizy: {'TAK' if fake_response.total_success else 'NIE'}\n")
                else:
                    print("\n[INFO] Nie udało się wyliczyć pozycji (za mało widocznych znaczników w bazie).\n")

        except Exception as e:
            self.get_logger().error(f"Błąd w callbacku obrazu: {e}")

    def perform_manual_analysis(self):
        """
        Funkcja wywoływana po wciśnięciu klawisza 't'. 
        Przetwarza ostatnią zapamiętaną klatkę.
        """
        if self.latest_frame is None:
            self.get_logger().warn("Brak zapamiętanej klatki z kamery!")
            return

        # Przykładowa poprzednia pozycja
        prev_pos = np.array([0.0, 0.0, 1.1]) 
        
        # Wywołanie algorytmu z CameraHandler
        x, y, z, angle, success = self.handler.estimate_position_for_client(
            self.latest_frame, 
            prev_pos, 
            reset_cached_data=True
        )
        
        if success:
            print("\n==============================")
            #print(f"Wykryto znaczników: {len(self.)}")
            print(f" SUKCES ANALIZY Z KAMERY!")
            print(f" Pozycja X: {x:.3f} m")
            print(f" Pozycja Y: {y:.3f} m")
            print(f" Wysokość Z: {z:.3f} m")
            print(f" Kąt łazika (Yaw): {angle:.2f}°")
            print("==============================\n")
        else:
            print("\n[!] Nie udało się wyliczyć pozycji (za mało widocznych znaczników w bazie).\n")

    def estimate_callback(self, request, response):
        """
        Ta funkcja odpala się, gdy Klient poprosi o pozycję.
        """
        if self.latest_frame is None:
            self.get_logger().warn("Jeszcze nie otrzymałem żadnej klatki!")
            response.total_success = False
            return response

        # Przygotowanie poprzedniej pozycji (z requestu Klienta)
        prev_pos = np.array([request.prev_x, request.prev_y, request.prev_z])
        
        # Wywołanie funkcji na najnowszej klatce z symulacji
        x, y, z, angle, success = self.handler.estimate_position_for_client(
            self.latest_frame, 
            prev_pos, 
            request.reset_cached_data
        )

        if not success:
            self.get_logger().warn("Nie udało się wyliczyć pozycji (za mało widocznych znaczników w bazie).")
            response.x = np.nan
            response.y = np.nan
            response.z = np.nan
            response.x_angle = np.nan
            response.y_angle = np.nan
            response.z_angle = np.nan
            response.arucos = np.nan
            response.total_success = False
            return response

        folder_name = os.path.expanduser("~/arucos")
        os.makedirs(folder_name, exist_ok=True)  
        file_path = os.path.join(folder_name, f"aruco_{self.image_counter}.jpg")

        success = cv2.imwrite(file_path, self.latest_frame)
    
        if not success:
            print(f"BŁĄD: Nie udało się zapisać zdjęcia {file_path}")
        else:
            print(f"[INFO] Zapisano zdjęcie z wykrytymi ArUco do pliku: {file_path}")
            self.image_counter += 1
        
        
        # Zapisanie wyników do odpowiedzi serwisu
        response.x = float(x) if x is not None else 0.0
        response.y = float(y) if y is not None else 0.0
        response.z = float(z) if z is not None else 0.0
        response.x_angle = np.nan
        response.y_angle = np.nan
        response.z_angle = float(angle) if angle is not None else 0.0
        response.arucos = len(self.handler.cached_detected_markers) if self.handler.cached_detected_markers is not None else 0

        response.total_success = success
        
        return response

def main(args=None):
    rclpy.init(args=args)
    node = ArucoPositionServer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()