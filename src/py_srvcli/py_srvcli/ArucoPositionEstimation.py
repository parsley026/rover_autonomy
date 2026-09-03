import os
import numpy as np
import pandas as pd
from scipy.optimize import minimize


class ArucoPositionEstimation:

    minimal_radius: float = 0.5  # minimalna odległość w metrach

    def __init__(self, marker_database):
        # script_dir = os.path.dirname(os.path.abspath(__file__))
        # relative_path = os.path.join(script_dir, 'metadata', 'positions2020_test.csv')
        # absolute_path = 'home/dudziu/Desktop/Raptors/arucoERC26/src/py_srvcli/py_srvcli/metadata/positions2020_test.csv'

        # csv_path = relative_path if os.path.exists(relative_path) else absolute_path

        # if not os.path.exists(csv_path):
        #     print(f"BŁĄD: Nie znaleziono pliku bazy punktów: {csv_path}")
        #     exit(1)

        # db = pd.read_csv(csv_path)
        # db.columns = db.columns.str.strip() # Usuwa przypadkowe spacje z nazw kolumn w pliku CSV
        # if db.empty:
        #     print("BŁĄD: Baza punktów jest pusta.")
        #     exit(1)

        # zaincijalizowanie bazy markerów
        self.world_points = marker_database

        # Wczytanie danych z CSV do słownika world_points
        # self.world_points = {}
        # for _, row in db.iterrows():
        #     if str(row['ID']).startswith('L'):
        #         marker_id = int(str(row['ID'])[1:])
                
        #         # Pozycja XYZ
        #         x_val = row['X'] if 'X' in row else 0.0
        #         y_val = row['Y'] if 'Y' in row else 0.0
        #         z_val = row['Z'] if 'Z' in row else 0.0
                
        #         # Orientacja / Kąty (fallback na 0.0, jeśli CSV ich nie zawiera)
        #         rx_val = row['Roll'] if 'Roll' in row else 0.0
        #         ry_val = row['Pitch'] if 'Pitch' in row else 0.0
        #         rz_val = row['Yaw'] if 'Yaw' in row else 0.0
            
        #         # Zapisujemy wszystko do jednego, 6-elementowego wektora
        #         self.world_points[marker_id] = np.array([
        #             x_val, y_val, z_val, 
        #             rx_val, ry_val, rz_val
        #         ], dtype=float)

    def calculate_position(self, marker_data: list[tuple[int, float, float, float, float]], prev_position: np.ndarray = None) -> np.ndarray:
        """
        Wyznacza pozycję łazika.
        :param marker_data: Lista krotek z funkcji detect_markes_cnetre_rover: [(id, distance, rover_x, rover_y, rover_z), ...]
        :param prev_position: Opcjonalnie poprzednia znana pozycja np.array([x, y, z])
        """
        # Filtrowanie markerów (musi być w bazie markerów i promieniu >= minimal_radius)
        valid_pylons = [
            data for data in marker_data
            if data[0] in self.world_points and data[1] >= self.minimal_radius
        ]

        ilosc_znacznikow = len(valid_pylons)
        print(f"[INFO] Liczba wykrytych znaczników w bazie: {ilosc_znacznikow}")

        if ilosc_znacznikow == 0:
            return None

        # Tylko 1 znaczniki lub mniej 
        elif ilosc_znacznikow <= 1:
            # # Rozpakowujemy dane wyliczone z solvePnP 
            # m_id, dist, r_x, r_y, r_z = valid_pylons[0]
            
            # # Pobieramy pozycję znacznika z mapy [x, y, z, rx, ry, rz]
            # marker_map_data = self.world_points[m_id]
            # marker_global_pos = marker_map_data[0:3]
            
            # # Wektor przesunięcia łazika względem znacznika
            # relative_offset = np.array([r_x, r_y, r_z])
            
            # # Jeśli znaczniki na arenie stoją idealnie równolegle do siatki X/Y mapy, 
            # # to globalna pozycja to po prostu pozycja znacznika + przesunięcie.
            # # (Gdyby znaczniki były pod kątem, trzeba by tu dodać macierz obrotu).
            # estimated_pos = marker_global_pos + relative_offset
            # return estimated_pos
            return None
            
        # 2 znaczniki lub więcej
        else:
            keys = [data[0] for data in valid_pylons]
            radiuses = [data[1] for data in valid_pylons]
            # Bierzemy tylko XYZ (pierwsze 3 elementy z 6-elementowej tablicy)
            centers = [self.world_points[k][0:3] for k in keys]

            def total_error_3d(pos):
                err = 0.0
                for center, r in zip(centers, radiuses):
                    dist = np.linalg.norm(pos - center)
                    err += (dist - r) ** 2
                return err

            # Punkt poprzedniej znanej lokacji, ułatiwa znalezienie poprawnej pozycji
            if prev_position is not None:
                x0 = np.array(prev_position, dtype=float)
            else:
                x0 = np.mean(centers, axis=0)

            # Optymalizacja nieliniowa
            result = minimize(total_error_3d, x0, method='BFGS')

            if result.success:
                return result.x
            else:
                return None