import cv2
import numpy as np
import glob
import os

from Camera import Camera


class LaneKeepAssistSystem:

    thresh_rgb_r = (145, 255)
    thresh_hls_l = (145, 255)
    thresh_lab_l = (154, 255)

    def __init__(self):
        self.camera = Camera()

    def process(self, image):
        undistorted_image = self.camera.undistort(image)
        transformed_image = self.camera.perspective_transform(undistorted_image)
        binary_image = self.get_lane_binary_image(transformed_image)
        left_fit_x, right_fit_x, fit_y = self.find_lanes_rect(binary_image)
        marked_lane_image = self.mark_lane(undistorted_image, left_fit_x, right_fit_x, fit_y)
        return marked_lane_image

    def find_lanes_rect(self, img_bin):
        image_size = self.camera.get_image_size()
        histogram = np.sum(img_bin[np.int(image_size[1] / 2):, :], axis=0)
        out_img = np.dstack((img_bin, img_bin, img_bin)) * 255
        mid_x = np.int(image_size[0] / 2)

        # average starting base for left and right line
        left_x_base = np.int(np.argmax(histogram[:mid_x]))
        right_x_base = np.int(np.argmax(histogram[mid_x:]) + mid_x)

        margin = 80
        windows_num = 8

        window_height = np.int(image_size[1] / windows_num)

        nonzero = img_bin.nonzero()
        nonzero_y = np.array(nonzero[0])
        nonzero_x = np.array(nonzero[1])

        left_x_current, right_x_current = left_x_base, right_x_base

        # least pixels amount for rect to be change next position
        pixels_thresh = 10

        left_lane_pix = []
        right_lane_pix = []

        for window in range(windows_num):
            # Identify window boundaries in x and y (and right and left)
            win_y_low = img_bin.shape[0] - (window + 1) * window_height
            win_y_high = img_bin.shape[0] - window * window_height
            win_x_left_low = left_x_current - margin
            win_x_left_high = left_x_current + margin
            win_x_right_low = right_x_current - margin
            win_x_right_high = right_x_current + margin
            # print(win_y_low, win_y_high, win_x_left_low, win_x_left_high, win_x_right_low, win_x_right_high)
            # Draw the windows on the visualization image
            # cv2.rectangle(out_img, (win_x_left_low, win_y_low), (win_x_left_high, win_y_high), (0, 255, 0), 2)
            # cv2.rectangle(out_img, (win_x_right_low, win_y_low), (win_x_right_high, win_y_high), (0, 255, 0), 2)

            # Identify the nonzero pixels in x and y within the window
            good_left_ids = ((nonzero_y >= win_y_low) & (nonzero_y < win_y_high) & (nonzero_x >= win_x_left_low) & (
                        nonzero_x < win_x_left_high)).nonzero()[0]
            good_right_ids = ((nonzero_y >= win_y_low) & (nonzero_y < win_y_high) & (nonzero_x >= win_x_right_low) & (
                        nonzero_x < win_x_right_high)).nonzero()[0]

            # Append these indices to the lists
            left_lane_pix.append(good_left_ids)
            right_lane_pix.append(good_right_ids)

            # If you found pixels > pixels_thresh, recenter next window on their mean position
            if len(good_left_ids) > pixels_thresh:
                left_x_current = np.int(np.mean(nonzero_x[good_left_ids]))
            if len(good_right_ids) > pixels_thresh:
                right_x_current = np.int(np.mean(nonzero_x[good_right_ids]))

        left_lane_pix = np.concatenate(left_lane_pix)
        right_lane_pix = np.concatenate(right_lane_pix)

        # Extract left and right line pixel positions
        left_x = nonzero_x[left_lane_pix]
        left_y = nonzero_y[left_lane_pix]
        right_x = nonzero_x[right_lane_pix]
        right_y = nonzero_y[right_lane_pix]

        # Fit a second order polynomial to each
        if left_x.size == 0 or left_y.size == 0 or right_x.size == 0 or right_y.size == 0:
            left_fit_coeffs = np.array([0, 0, 0])
            right_fit_coeffs = np.array([0, 0, 0])

        else:
            left_fit_coeffs = np.polyfit(left_y, left_x, 2)
            right_fit_coeffs = np.polyfit(right_y, right_x, 2)

        # Generate x and y values for plotting
        fit_y = np.linspace(0, image_size[0] - 1, image_size[0])
        left_fit_x = left_fit_coeffs[0] * fit_y ** 2 + left_fit_coeffs[1] * fit_y + left_fit_coeffs[2]
        right_fit_x = right_fit_coeffs[0] * fit_y ** 2 + right_fit_coeffs[1] * fit_y + right_fit_coeffs[2]

        return left_fit_x, right_fit_x, fit_y

    def get_lane_binary_image(self, trans_image):
        img_rgb_r = self.threshold_rgb_r(trans_image)
        img_hls_l = self.threshold_hls_l(trans_image)
        img_lab_l = self.threshold_lab_l(trans_image)
        img_combined = self.combine_binary([img_rgb_r, img_hls_l, img_lab_l])
        img_binary = cv2.GaussianBlur(img_combined, (5, 5), 0)
        img_binary.dtype = 'uint8'
        return img_binary

    def threshold_rgb_r(self, img):
        r, _, _ = cv2.split(img)
        _, img_thresh = cv2.threshold(r, self.thresh_rgb_r[0], self.thresh_rgb_r[1], cv2.THRESH_BINARY)
        return img_thresh

    def threshold_hls_l(self, img):
        _, l, _ = cv2.split(img)
        _, img_thresh = cv2.threshold(l, self.thresh_hls_l[0], self.thresh_hls_l[1], cv2.THRESH_BINARY)
        return img_thresh

    def threshold_lab_l(self, img):
        l, _, _ = cv2.split(img)
        _, img_thresh = cv2.threshold(l, self.thresh_lab_l[0], self.thresh_lab_l[1], cv2.THRESH_BINARY)
        return img_thresh

    def combine_binary(self, imgs):
        if len(imgs) > 1:
            img_combined = imgs[0]
            for img in imgs[1:]:
                img_combined = cv2.bitwise_or(img_combined, img)
            return img_combined
        else:
            return None

    def mark_lane(self, undistorted_image, left_fix_x, right_fix_x, fit_y):
        warp_zero = np.zeros_like(undistorted_image[:, :, 0]).astype(np.uint8)
        color_mark_trans = np.dstack((warp_zero, warp_zero, warp_zero))

        # recast x and y for fillPoly
        pts_left = np.array([np.transpose(np.vstack([left_fix_x, fit_y]))])
        pts_right = np.array([np.flipud(np.transpose(np.vstack([right_fix_x, fit_y])))])
        pts = np.hstack((pts_left, pts_right))

        cv2.fillPoly(color_mark_trans, np.int_([pts]), (0, 255, 0))

        color_mark = self.camera.rev_perspective_transform(color_mark_trans)

        marked_lane_image = cv2.addWeighted(undistorted_image, 1, color_mark, 0.3, 0)
        return marked_lane_image
