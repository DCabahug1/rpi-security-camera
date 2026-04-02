import cv2

cap = cv2.VideoCapture(0)

cv2.namedWindow("Webcam", cv2.WINDOW_FULLSCREEN)
cv2.setWindowProperty("Webcam", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

cv2.namedWindow("Webcam_Gray", cv2.WINDOW_FULLSCREEN)
cv2.setWindowProperty("Webcam_Gray", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

while True:
  ret, frame = cap.read()

  if not ret:
    print("Unable to read frame")
    break

  cv2.rectangle(frame, (20,20), (80,80), (255,0,0), 2)

  gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

  cv2.imshow("Webcam", frame)
  cv2.imshow('Webcam_Gray', gray_frame)

  key = cv2.waitKey(1) & 0xFF

  if key == ord('q'):
    break
  elif key == ord('s'):
    cv2.imwrite('color_snapshot.jpg', frame)
  elif key == ord('g'):
    cv2.imwrite('gray_snapshot.jpg', gray_frame)

cap.release()
cv2.destroyAllWindows()
