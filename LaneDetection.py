import cv2
import numpy as np
import glob
import os

from Camera import Camera


class LaneDetection:


    thresh_gray = []
    thresh_rgb_r = []
    thresh_hls_l = []
    thresh_lab_l = []


    thresh_gray_vals = [g for g in range(105, 170, 5)]
    thresh_rgb_r_vals = [r for r in range(105, 170, 5)]
    thresh_hls_l_vals = [l for l in range(105, 170, 5)]
    thresh_lab_l_vals = [l for l in range(105, 155, 2)]

    # real lane dimensions
    lane_width_real = 3.75

    # max_m_offset_abs = 0.39

    min_m_offset_warn = 0.2

    min_m_offset_alert = 0.4

    max_m_offset_error = 2.

    tail_frame_correct_max = 7

    def __init__(self):
        self.load_color_thresholds()
        self.camera = Camera()

        self.x_m_per_px = self.lane_width_real\
                          / (self.camera.perspective_dst_points[1][0] - self.camera.perspective_dst_points[0][0])

        self.tail_frame_correct = 0

        self.prev_left_fit_x = [0]
        self.prev_right_fit_x = [0]
        self.prev_fit_y = [0]
        self.prev_offset = 0.

    def process(self, image):
        alert = False

        # undistorted_image = self.camera.undistort(image)
        # gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        transformed_image = self.camera.perspective_transform(image)
        binary_image = self.get_lane_binary_image(transformed_image, image)
        ret, left_fit_x, right_fit_x, fit_y, offset = self.find_lanes_rect(binary_image)

        if ret:
            marked_lane_image = self.mark_lane(image, left_fit_x, right_fit_x, fit_y)
            offset = self.get_offset(left_fit_x, right_fit_x, self.camera.get_image_size()[0] / 2)

            if offset > 0:
                direction = "L"
            elif offset == 0:
                direction = "S"
            else:
                direction = "R"
            # direction = "L " if offset > 0 else "R "

            offset = abs(offset)

            marked_lane_image = self.mark_offset(marked_lane_image, offset, direction)



            if offset < self.min_m_offset_warn:
                priority = 0
            elif offset < self.min_m_offset_alert:
                priority = 1
            else:
                priority = 2
                alert = True
        else:
            direction = "S"
            marked_lane_image = self.mark_offset(image, " - ", direction)
            priority = 0
            offset = 0

        # marked_lane_image = self.camera.mark_roi(undistorted_image)
        return marked_lane_image, alert, direction, offset, priority

    def find_lanes_rect(self, img_bin):
        image_size = self.camera.get_image_size()
        histogram = np.sum(img_bin[np.int(image_size[1] / 2):, :], axis=0)
        # out_img = np.dstack((img_bin, img_bin, img_bin)) * 255
        mid_x = np.int(image_size[0] / 2)

        # average starting base for left and right line
        left_x_base = np.int(np.argmax(histogram[:mid_x]))
        right_x_base = np.int(np.argmax(histogram[mid_x:]) + mid_x)

        margin = 50
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

        left_fit_coeffs = np.array([0, 0, 0])
        right_fit_coeffs = np.array([0, 0, 0])

        # Fit a second order polynomial to each
        if left_x.size == 0 or left_y.size == 0 or right_x.size == 0 or right_y.size == 0:
            ret = False

        else:
            left_fit_coeffs = np.polyfit(left_y, left_x, 2)
            right_fit_coeffs = np.polyfit(right_y, right_x, 2)
            ret = True

            # if right_fit_coeffs[2] - left_fit_coeffs[2] < 0.9 * (self.camera.perspective_dst_points[1][0] - self.camera.perspective_dst_points[0][0]):
            #     ret = False

        # print(left_fit_coeffs, right_fit_coeffs)

        # Generate x and y values for plotting
        if ret:
            fit_y = np.linspace(0, image_size[0] - 1, image_size[0])
            left_fit_x = left_fit_coeffs[0] * fit_y ** 2 + left_fit_coeffs[1] * fit_y + left_fit_coeffs[2]
            right_fit_x = right_fit_coeffs[0] * fit_y ** 2 + right_fit_coeffs[1] * fit_y + right_fit_coeffs[2]

            base_width = right_fit_x[-1] - left_fit_x[-1]
            nominal_width = self.camera.perspective_dst_points[1][0] - self.camera.perspective_dst_points[0][0]

            nominal_area = nominal_width * self.camera.get_image_size()[1]

            # filter outputs
            if base_width < 0.7 * nominal_width or base_width > 1.5 * nominal_width:
                # print("Base err: {}".format(base_width))
                self.tail_frame_correct += 1
                ret = False
            elif self.curves_inter_area(left_fit_x, right_fit_x) > 1.5 * nominal_area or\
                self.curves_inter_area(left_fit_x, right_fit_x) < 0.75 * nominal_area:
                self.tail_frame_correct += 1
                ret = False
                # print("Area err: {}".format(self.curves_inter_area(left_fit_x, right_fit_x)))
            # elif self.curves_difference(left_fit_x, right_fit_x) > 2500:
            #     # print("Diff err: {}".format(self.curves_difference(left_fit_x, right_fit_x)))
            #     self.tail_frame_correct += 1
            #     ret = False

            offset = self.get_offset(left_fit_x, right_fit_x, self.camera.get_image_size()[0] / 2)

            if offset > self.max_m_offset_error:
                self.tail_frame_correct += 1
                ret = False

            if ret:
                self.prev_left_fit_x = left_fit_x
                self.prev_right_fit_x = right_fit_x
                self.prev_fit_y = fit_y
                self.prev_offset = offset
                self.tail_frame_correct = 0

            elif self.tail_frame_correct < self.tail_frame_correct_max:
                left_fit_x = self.prev_left_fit_x
                right_fit_x = self.prev_right_fit_x
                fit_y = self.prev_fit_y
                offset = self.prev_offset
                ret = True

        else:
            if self.tail_frame_correct < self.tail_frame_correct_max:
                left_fit_x = self.prev_left_fit_x
                right_fit_x = self.prev_right_fit_x
                fit_y = self.prev_fit_y
                offset = self.prev_offset
                ret = True
            else:
                fit_y = None
                left_fit_x = None
                right_fit_x = None
                offset = 0.


        return ret, left_fit_x, right_fit_x, fit_y, offset

    def get_lane_binary_image(self, trans_image, image):
        img_gray = self.threshold_gray(trans_image)
        # img_rgb_r = self.threshold_rgb_r(trans_image)
        img_hls_l = self.threshold_hls_l(trans_image)
        # img_lab_l = self.threshold_lab_l(trans_image)
        img_canny = self.camera.perspective_transform(self.canny_edge_detect(image))
        img_binary = self.combine_binary([img_gray, img_hls_l, img_canny])
        # img_binary = cv2.GaussianBlur(img_combined, (5, 5), 0)
        img_binary.dtype = 'uint8'
        return img_binary

    def threshold_gray(self, img):
        img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        _, img_thresh = cv2.threshold(img_gray, self.thresh_gray[0], self.thresh_gray[1], cv2.THRESH_BINARY)
        return img_thresh

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

    def canny_edge_detect(self, gray_img):
        gray_img.dtype = 'uint8'
        img_blur = cv2.GaussianBlur(gray_img, (3, 3), 0)
        img_gray = cv2.cvtColor(img_blur, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(img_blur, 60, 150, (3, 3))
        return edges

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

    def mark_offset(self, img, offset, direction):
        out_img = img.copy()
        font = cv2.FONT_HERSHEY_SIMPLEX
        out_text = str(offset) + "m"
        if direction == "L":
            out_text = "<<< " + out_text
        elif direction == "R":
            out_text = out_text + " >>>"
        cv2.putText(out_img, out_text, (250, 100), font, 1, (255, 0, 0), 2)
        return out_img

    def get_color_thresholds_to_str(self):
        thresholds = str(self.thresh_rgb_r[0]) + " " + str(self.thresh_hls_l[0]) + " " + str(self.thresh_lab_l[0])
        return thresholds

    def set_color_thresholds_from_str(self, thresh):
        self.thresh_rgb_r[0] = int(thresh[0])
        self.thresh_hls_l[0] = int(thresh[1])
        self.thresh_lab_l[0] = int(thresh[2])

    def get_color_thresholds_to_seeknum(self):
        return self.thresh_gray_vals.index(self.thresh_gray[0])

    def set_color_thresholds_from_seeknum(self, seeknum):
        self.thresh_gray[0] = self.thresh_gray_vals[seeknum]
        # self.thresh_rgb_r[0] = self.thresh_rgb_r_vals[seeknum]
        self.thresh_hls_l[0] = self.thresh_hls_l_vals[seeknum]
        # self.thresh_lab_l[0] = self.thresh_lab_l_vals[seeknum]

    def save_color_thresholds(self):
        thresh = np.int32([self.thresh_gray, self.thresh_hls_l])
        np.savetxt('colorThresholds.csv', thresh)

    def load_color_thresholds(self):
        thresh = np.genfromtxt('colorThresholds.csv', dtype='int32')
        self.thresh_gray = list(thresh[0])
        self.thresh_hls_l = list(thresh[1])
        # self.thresh_lab_l = list(thresh[2])

    def curves_difference(self, left_fit, right_fit):
        sum = 0
        base_width = right_fit[-1] - left_fit[-1]
        for i in range(len(left_fit)):
            sum += (right_fit[i] - base_width - left_fit[i])**2
        return sum**0.5

    def curves_inter_area(self, left_fit, right_fit):
        area = 0
        for i in range(len(left_fit)):
            area += (right_fit[i] - left_fit[i])
        return area

    def get_offset(self, left_fit, right_fit, midpoint):
        offset = round(((left_fit[-1] + right_fit[-1]) / 2 - midpoint) * self.x_m_per_px, 2)
        return offset
