import math
import numpy as np

def przeciecie_i_kat(p1, p2):
    """
    Oblicza punkt przecięcia prostej przechodzącej przez punkty p1,p2 z osią X (y=0)
    oraz kąt między tą prostą a osią X.
    
    p1, p2 - krotki (x, y)
    Zwraca: ((x_przec, 0), kat_stopnie)
    """
    x1, y1 = p1
    x2, y2 = p2
    
    # sprawdzenie, czy prosta pionowa
    if x1 == x2:
        # prosta pionowa: x = c
        punkt = (x1, 0)
        kat = 90.0
        return punkt, kat
    
    # prosta niepionowa
    m_a = (y2 - y1) / (x2 - x1)
    b_a = y1 - m_a * x1
    
    # punkt przecięcia z osią X (y=0)
    if m_a != 0:
        x_int = -b_a / m_a
    else:
        # prosta równoległa do osi X: albo pokrywa się z osią X, albo jej nie przecina
        if b_a == 0:
            return None, 0.0  # prosta = oś X
        else:
            return None, 0.0  # prosta równoległa, brak przecięcia
    
    punkt = (x_int, 0)
    
    # kąt między prostą a osią X
    kat = math.degrees(math.atan(abs(m_a)))
    
    return punkt, kat

# Przykłady:
# print(przeciecie_i_kat((0, 1), (1, 2)))   # prosta rosnąca
# print(przeciecie_i_kat((2, 1), (2, 5)))   # prosta pionowa
# print(przeciecie_i_kat((0, 2), (1, 2)))   # prosta pozioma

import math

import math

def prosta_b(p1, p2, kat_stopnie, clockwise=True):
    """
    Wyznacza prostą b nachyloną pod kątem c względem prostej a.
    Prosta a zdefiniowana przez dwa punkty p1, p2.
    Zwraca: jedna prosta b przechodząca przez p1.
    
    Parametry:
    - p1, p2: krotki (x, y) - punkty na prostej a
    - p1 -punkt wspólny dla prostej a i b (łazik)
    - p2 - drugi punkt na prostej a (aruco)
    - kat_stopnie: kąt między prostymi w stopniach
    - clockwise: jeśli True → obrót zgodnie z ruchem wskazówek zegara
                 jeśli False → obrót przeciwnie do ruchu wskazówek zegara
                 
    Wynik:
    - (m_b, b_b) dla prostych niepionowych
    - ("vert", x0) dla prostych pionowych
    """
    x1, y1 = p1
    x2, y2 = p2
    c = math.radians(kat_stopnie)
    
    # przypadek: prosta a pionowa
    if x1 == x2:
        # kąt nachylenia prostej a = 90 stopni
        alpha = math.pi/2
        # obrót w prawo → zmniejszamy kąt
        beta = alpha - c if clockwise else alpha + c
        # normalizacja kąta do [-pi/2, pi/2] dla tangensa
        # jeżeli prosta b pionowa → kat = ±90 stopnFalsei
        beta_deg = math.degrees(beta) % 180
        if abs(beta_deg - 90) < 1e-9:
            return ("vert", x1)
        else:
            m_b = math.tan(beta)
            b_b = y1 - m_b * x1
            return (m_b, b_b)
    
    # prosta niepionowa
    m_a = (y2 - y1) / (x2 - x1)
    alpha = math.atan(m_a)
    beta = alpha - c if clockwise else alpha + c
    
    # jeśli nowa prosta pionowa
    beta_deg = math.degrees(beta) % 180
    if abs(beta_deg - 90 ) < 0.5:
        return ("vert", x1)
    
    # zwykła prosta
    m_b = math.tan(beta)
    if abs(m_b) < 0.4:
        m_b = 0.0
    b_b = y1 - m_b * x1
    return (m_b, b_b)

# --- PRZYKŁAD ---
# Prosta a przez (0,0) i (1,1)
# Kąt = 45 stopni

def prosta_b_tylko_kat_ox(p1, p2, kat_stopnie, clockwise=True):
    """
    Wyznacza prostą b nachyloną pod kątem c względem prostej a.
    Prosta a zdefiniowana przez dwa punkty p1, p2.
    Zwraca: jedna prosta b przechodząca przez p1.
    
    Parametry:
    - p1, p2: krotki (x, y) - punkty na prostej a
    - p1 -punkt wspólny dla prostej a i b (łazik)
    - p2 - drugi punkt na prostej a (aruco)
    - kat_stopnie: kąt między prostymi w stopniach
    - clockwise: jeśli True → obrót zgodnie z ruchem wskazówek zegara
                 jeśli False → obrót przeciwnie do ruchu wskazówek zegara
                 
    Wynik:
    - (m_b, b_b) dla prostych niepionowych
    - ("vert", x0) dla prostych pionowych
    """
    x1, y1 = p1
    x2, y2 = p2
    c = math.radians(kat_stopnie)
    
    # przypadek: prosta a pionowa
    # if np.abs(x1 - x2) <= 0.01:# if x1 == x2:
    #     print("pionova |||",end=" ")
    #     # kąt nachylenia prostej a = 90 stopni
    #     alpha = math.pi/2
    #     # obrót w prawo → zmniejszamy kąt
    #     beta = alpha - c if clockwise else alpha + c
    #     # normalizacja kąta do [-pi/2, pi/2] dla tangensa
    #     # jeżeli prosta b pionowa → kat = ±90 stopnFalsei
    #     beta_deg = math.degrees(beta) % 360
    #     if abs(beta_deg - 90) < 0.5:
    #         print("zero |||",end=" ")
    #         beta_deg = 0
    #     return beta_deg
    
    # prosta niepionowa
    m_a = (y2 - y1) / (x2 - x1)
    alpha = math.atan(m_a)
    y_diff = y2 - y1
    x_diff = x2 - x1
    alpha = math.atan2(y_diff, x_diff)
    beta = alpha - c if clockwise else alpha + c
    
    # jeśli nowa prosta pionowa
    beta_deg = math.degrees(beta) % 360
    # if abs(beta_deg - 90 ) < 0.5:
    #     print("zero |||",end=" ")
    #     beta_deg = 0
    return beta_deg
  

if __name__ == "__main__":
    print("--- PRZYKŁAD ---")
    print("Obrót w prawo :", prosta_b_tylko_kat_ox((0,0), (3,1.73), 30, clockwise=True))
    print("Obrót w prawo :", prosta_b_tylko_kat_ox((0,0), (3,1.73*3), 30, clockwise=False))
    print("Obrót w lewo  :", prosta_b_tylko_kat_ox((0,1),(1,0),90,clockwise=True))
    print("Obrót w lewo  :", prosta_b_tylko_kat_ox((0,0), (1,1), 45, clockwise=False))


