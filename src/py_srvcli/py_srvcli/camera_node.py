"""Lekki węzeł ROS 2 pobierający obraz z RTSP/USB i publikujący w ROS 2."""

import cv2
from cv_bridge import CvBridge, CvBridgeError
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image

USB_SOURCE = 'usb'
RTSP_SOURCE = 'rtsp'

class CameraNode(Node):
    """Węzeł publikujący obraz z kamery jako sensor_msgs/Image."""

    def __init__(self) -> None:
        super().__init__('camera_publisher')
        
        # Parametry
        self.declare_parameter('source', RTSP_SOURCE)
        self.declare_parameter('usb_index', 0)
        self.declare_parameter('rtsp_url', '')
        self.declare_parameter('camera_frame', 'camera_optical_frame')

        source = str(self.get_parameter('source').value).lower()
        if source not in (USB_SOURCE, RTSP_SOURCE):
            raise ValueError("source musi być 'usb' lub 'rtsp'")
        if source == RTSP_SOURCE and not self.get_parameter('rtsp_url').value:
            raise ValueError('rtsp_url jest wymagane dla source = rtsp')

        self._source = source
        self._bridge = CvBridge()
        
        # Publikator obrazu do sieci ROS 2
        self._image_publisher = self.create_publisher(
            Image,
            '~/image_raw',
            10
        )

        # Inicjalizacja kamery
        self._capture = self._open_capture()
        
        # ========================================================
        # ZMIANA 1: BARDZO SZYBKI ZEGAR (0.02s -> 50Hz) 
        # Zmusza OpenCV do błyskawicznego opróżniania bufora RTSP
        # ========================================================
        self._timer = self.create_timer(0.02, self._read_camera)
        
        # ========================================================
        # ZMIANA 2: LICZNIK KLATEK
        # Pozwoli nam ignorować większość klatek i nie obciążać sieci
        # ========================================================
        self._frame_counter = 0 
        # Ustal co którą klatkę chcesz publikować. 
        # Jeśli kamera ma 25 FPS, a podasz 3, uzyskasz stabilne ~8 FPS w ROS.
        self._publish_every_n_frames = 3 
        
        width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self._capture.get(cv2.CAP_PROP_FPS)
        
        self.get_logger().info(
            f'Rozpoczęto nadawanie: {self._source}, rozdzielczość: {width}x{height}, FPS: {fps}'
        )

    def _open_capture(self) -> cv2.VideoCapture:
        if self._source == USB_SOURCE:
            index = int(self.get_parameter('usb_index').value)
            capture = cv2.VideoCapture(index, cv2.CAP_V4L2)
            description = f'Kamera USB (indeks {index})'
        else:
            url = str(self.get_parameter('rtsp_url').value)
            capture = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            if not capture.isOpened():
                capture.release()
                capture = cv2.VideoCapture(url) # Fallback bez wymuszania FFMPEG
            description = 'Strumień RTSP'

        if not capture.isOpened():
            capture.release()
            raise RuntimeError(f'Nie można otworzyć: {description}')
        return capture

    def _read_camera(self) -> None:
        if self._capture is None:
            return
            
        # 1. Błyskawiczny odczyt, który utrzymuje strumień RTSP przy życiu
        success, frame = self._capture.read()
        
        if not success:
            self.get_logger().warning(
                'Nie można odczytać klatki z kamery!',
                throttle_duration_sec=5.0,
            )
            return

        # ========================================================
        # ZMIANA 3: SYSTEM PUBLIKOWANIA (FRAME SKIP)
        # ========================================================
        self._frame_counter += 1
        
        # Publikujemy tylko co N-tą klatkę
        if self._frame_counter >= self._publish_every_n_frames:
            self._publish_frame(frame)
            self._frame_counter = 0 # Zerujemy licznik na nowo

    def _publish_frame(self, frame) -> None:
        try:
            # Konwersja OpenCV (BGR) -> ROS 2 Image (bgr8)
            ros_image_msg = self._bridge.cv2_to_imgmsg(frame, encoding="bgr8")
            
            # Wypełnienie nagłówka
            ros_image_msg.header.stamp = self.get_clock().now().to_msg()
            ros_image_msg.header.frame_id = str(self.get_parameter('camera_frame').value)
            
            # Wysłanie w świat
            self._image_publisher.publish(ros_image_msg)
            
        except CvBridgeError as error:
            self.get_logger().error(f'Błąd konwersji obrazu dla ROS: {error}')

    def destroy_node(self) -> None:
        """Zwolnienie zasobów wideo przed wyłączeniem."""
        if self._capture is not None:
            self._capture.release()
        super().destroy_node()


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node: CameraNode | None = None
    try:
        node = CameraNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()