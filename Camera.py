import cv2
import numpy as np
import glob
import os


class Camera:

    matrix = []
    optimal_matrix = []
    distortion_coeffs = []
    ROI = []

    image_size = (1296, 972)

    chessboard_pattern = (7, 9)
    calibrate_imgs_path = glob.glob("./ccalib-test-images-5/*.jpg")

    perspective_src_points = np.float32([[170, image_size[1]], [1164, image_size[1]],
                                [688, image_size[1] * 0.55], [576, image_size[1] * 0.55]])

    perspective_dst_points = np.float32([[image_size[0] / 4, image_size[1]],
                                [image_size[0] * 3 / 4, image_size[1]],
                                [image_size[0] * 3 / 4, image_size[1] * 0.1],
                                [image_size[0] / 4, image_size[1] * 0.1]])

    perspective_transform_matrix = []
    rev_perspective_transform_matrix = []

    def __init__(self):
        self.calibrate()
        self.perspective_transform_matrix = cv2.getPerspectiveTransform(self.perspective_src_points,
                                                                        self.perspective_dst_points)
        self.rev_perspective_transform_matrix = cv2.getPerspectiveTransform(self.perspective_dst_points,
                                                                            self.perspective_src_points)

    def calibrate(self):
        object_points = []
        image_points = []
        object_point = np.zeros((self.chessboard_pattern[0] * self.chessboard_pattern[1], 3), np.float32)
        object_point[:, :2] = np.mgrid[0:self.chessboard_pattern[0], 0:self.chessboard_pattern[1]].T.reshape(-1, 2)

        for image in self.calibrate_imgs_path:
            calib_img = cv2.imread(image)
            ret, corners = cv2.findChessboardCorners(calib_img, self.chessboard_pattern)
            cv2.drawChessboardCorners(calib_img, self.chessboard_pattern, corners, ret)
            if ret:
                image_points.append(corners)
                object_points.append(object_point)
                print(self.calibrate_imgs_path.index(image), ": ", os.path.basename(image))

        retval, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(object_points, image_points,
                                                                               self.image_size, None, None)

        if retval:
            opt_alpha = 1
            opt_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, dist_coeffs,
                                                                   self.image_size, opt_alpha)
            self.matrix = camera_matrix
            self.optimal_matrix = opt_camera_matrix
            self.ROI = roi
            self.distortion_coeffs = dist_coeffs

            # np.savetxt('cameraMatrix.csv', camera_matrix)
            # np.savetxt('cameraOptMatrix.csv', opt_camera_matrix)
            # np.savetxt('cameraDistCoeffs.csv', dist_coeffs)
            # np.savetxt('cameraCalibROI.csv', roi)

    # def loadCameraProperties(self):
    #     self.matrix = np.genfromtxt('cameraMatrix.csv')
    #     self.optimal_matrix = np.genfromtxt('cameraOptMatrix.csv')
    #     self.distortion_coeffs = np.genfromtxt('cameraDistCoeffs.csv')
    #     self.ROI = np.genfromtxt('cameraCalibROI.csv')

    def undistort(self, img):
        img_undist = cv2.undistort(img, self.matrix, self.distortion_coeffs, None, self.optimal_matrix)
        x, y, w, h = self.ROI
        x, y, w, h = int(x), int(y), int(w), int(h)
        img_undist = img_undist[y:y + h, x:x + w]
        img_undist = cv2.resize(img_undist, self.image_size)
        # cv2.imwrite(self.sourceImg.replace('.png', '_result_cropped_scaled.png'), img_undist)
        return img_undist

    def calculate_perspective_transform_matrix(self):
        self.perspective_transform_matrix = cv2.getPerspectiveTransform(self.perspective_src_points,
                                                                        self.perspective_dst_points)

    def perspective_transform(self, img):

        srcPoints = np.float32([[170, self.image_size[1]], [1164, self.image_size[1]],
                                [688, self.image_size[1] * 0.55], [576, self.image_size[1] * 0.55]])
        # np.array([[self.imageSize[0] / 2 - 470, self.imageSize[1]],
        #              [self.imageSize[0] / 2 + 470, self.imageSize[1]],
        #              [self.imageSize[0] / 2 + 190, self.imageSize[1] / 2],
        #              [self.imageSize[0] / 2 - 190, self.imageSize[1] / 2]], dtype=np.float32)

        dstPoints = np.float32([[self.image_size[0] / 4, self.image_size[1]],
                                [self.image_size[0] * 3 / 4, self.image_size[1]],
                                [self.image_size[0] * 3 / 4, self.image_size[1] * 0.1],
                                [self.image_size[0] / 4, self.image_size[1] * 0.1]])

        # np.array([[self.imageSize[0] / 2 - 440, self.imageSize[1]],
        #          [self.imageSize[0] / 2 + 440, self.imageSize[1]],
        #          [self.imageSize[0] / 2 + 440, self.imageSize[1] / 2],
        #          [self.imageSize[0] / 2 - 440, self.imageSize[1] / 2]], dtype=np.float32)

        img_transformed = cv2.warpPerspective(img, self.perspective_transform_matrix, self.image_size)
        # cv2.imwrite(self.sourceImg.replace('.png', '_result_cs_trans.png'), img_transformed)
        return img_transformed

    def rev_perspective_transform(self, img):
        rev_img_transformed = cv2.warpPerspective(img, self.rev_perspective_transform_matrix, self.image_size)
        return rev_img_transformed

    def laneBinary(self):
        pass


    def colorTransforms(self, img):
        b, g, r = cv2.split(img)
        cv2.imwrite('samples/color_results/bgr/video_snap_1_b.png', b)
        cv2.imwrite('samples/color_results/bgr/video_snap_1_g.png', g)
        cv2.imwrite('samples/color_results/bgr/video_snap_1_r.png', r)
        _, rthresh = cv2.threshold(r, 120, 255, cv2.THRESH_BINARY)
        cv2.imwrite('samples/color_results/bgr/video_snap_1_rthresh.png', rthresh)

        imgHLS = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)
        h, l, s = cv2.split(imgHLS)
        cv2.imwrite('samples/color_results/hls/video_snap_1_h.png', h)
        cv2.imwrite('samples/color_results/hls/video_snap_1_l.png', l)
        cv2.imwrite('samples/color_results/hls/video_snap_1_s.png', s)

        imgHSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(imgHSV)
        cv2.imwrite('samples/color_results/hsv/video_snap_1_h.png', h)
        cv2.imwrite('samples/color_results/hsv/video_snap_1_s.png', s)
        cv2.imwrite('samples/color_results/hsv/video_snap_1_v.png', v)

    def get_image_size(self):
        return self.image_size


