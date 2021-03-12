# -*- coding: utf-8 -*-
import cv2
# import dlib
import numpy
from numpy import ndarray
from pathlib import Path
from typing import Optional, List

from ..utils import read_landmarks, read_frames
from ..utils import LOG


class TemplateFrameSeq:
    template_root = Path(__file__).parent.joinpath('../assets/template').resolve()
    ALIGN_POINTS = [0, 1]
    COLOUR_CORRECT_BLUR_FRAC = 1

    # Points from the second image to overlay on the first. The convex hull of each
    # element will be overlaid.

    def __init__(self, template_name, fixed_landmarks: Optional[List] = None):
        template_dir = self.template_root / template_name
        frames = read_frames(template_dir)
        if fixed_landmarks is None:
            landmarks = read_landmarks(template_dir)
        else:
            landmarks = numpy.array([fixed_landmarks for i in range(len(frames))])
            if landmarks.shape != (len(frames), 2, 2):
                raise ValueError(
                    'the fixed_landmarks {} is supposed to be transformed to ndarray with shape (length of frames, 2, 2)'.format(
                        fixed_landmarks))
        self.frames_landmarks = list(zip(frames, landmarks))

    def __len__(self):
        return len(self.frames_landmarks)

    def __getitem__(self, idx):
        current_frame = len(self.frames_landmarks)
        integer = idx // current_frame
        remainder = idx % current_frame
        if integer % 2 == 0:
            index = remainder
        else:
            index = - remainder - 1
        return self.frames_landmarks[index]


    def synthesize(self, viseme_frame_landmark, template_frame_landmark):

        im1, landmarks1 = template_frame_landmark
        im1 = im1.astype(numpy.uint8)
        if viseme_frame_landmark is None:
            return im1.astype(numpy.uint8)
        im2, landmarks2 = viseme_frame_landmark
        im2 = im2.astype(numpy.uint8)
        # print(' points to be registered: ', landmarks1[self.ALIGN_POINTS])

        M = self.transformation_from_points(landmarks1[self.ALIGN_POINTS],
                                            landmarks2[self.ALIGN_POINTS])
        # print(M)
        mask = self.get_face_mask(im2)
        warped_mask = self.warp_im(mask, M, im1.shape)
        # combined_mask = numpy.max([self.get_face_mask(im1, landmarks1), warped_mask],
        #                           axis=0)
        combined_mask = warped_mask
        warped_im2 = self.warp_im(im2, M, im1.shape)
        final_mask = self.get_face_mask(warped_im2).astype(numpy.float32)
        # final_mask = final_mask.transpose((2, 0, 1))[0]

        # return warped_im2
        self.correct_colours(im1, warped_im2, landmarks1)
        warped_corrected_im2 = warped_im2
        # output_im = im1 * (1.0 - combined_mask) + warped_corrected_im2 * combined_mask
        output_im = im1 * (1.0 - final_mask) + warped_corrected_im2 * final_mask

        return output_im.astype(numpy.uint8)

    def transformation_from_points(self, points1, points2):
        """
        Return an affine transformation [s * R | T] such that:
            sum ||s*R*p1,i + T - p2,i||^2
        is minimized.
        """
        # Solve the procrustes problem by subtracting centroids, scaling by the
        # standard deviation, and then using the SVD to calculate the rotation. See
        # the following for more details:
        #   https://en.wikipedia.org/wiki/Orthogonal_Procrustes_problem
        """
        Return an affine transformation [s * R | T] such that:
            sum ||s*R*p1,i + T - p2,i||^2
        is minimized.
        """
        # Solve the procrustes problem by subtracting centroids, scaling by the
        # standard deviation, and then using the SVD to calculate the rotation. See
        # the following for more details:
        #   https://en.wikipedia.org/wiki/Orthogonal_Procrustes_problem

        points1 = points1.astype(numpy.float64)
        points1 = numpy.matrix(points1)
        # points1 = numpy.vstack([points1, points1, points1])

        # print('shape of points', points1)
        points2 = points2.astype(numpy.float64)
        points2 = numpy.matrix(points2)

        # points2 = numpy.vstack([points2, points2, points2])


        # print('shape of points', points2)
        c1 = numpy.mean(points1, axis=0)
        c2 = numpy.mean(points2, axis=0)
        points1 -= c1
        points2 -= c2

        s1 = numpy.std(points1)
        s2 = numpy.std(points2)
        points1 /= s1
        points2 /= s2

        U, S, Vt = numpy.linalg.svd(points1.T * points2)

        # The R we seek is in fact the transpose of the one given by U * Vt. This
        # is because the above formulation assumes the matrix goes on the right
        # (with row vectors) where as our solution requires the matrix to be on the
        # left (with column vectors).
        R = (U * Vt).T
        # print('shape before stacks: ', (s2 / s1) * R)
        # print('shape before stacks: ', (s2 / s1) * R * c1.T)
        M = numpy.vstack([numpy.hstack(((s2 / s1) * R,
                                           c2.T - (s2 / s1) * R * c1.T)),
                             numpy.matrix([0., 0., 1.])])
        return M


    def get_face_mask(self, im):
        im = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
        idtype= im.dtype

        im = numpy.where(im == 0, 0, 1)


        mask = numpy.array([im, im, im]).transpose((1, 2, 0)).astype(idtype)

        # im = (cv2.GaussianBlur(im, (self.FEATHER_AMOUNT, self.FEATHER_AMOUNT), 0) > 0) * 1.0
        # im = cv2.GaussianBlur(im, (self.FEATHER_AMOUNT, self.FEATHER_AMOUNT), 0)

        return mask



    def warp_im(self, im, M, dshape):
        output_im = numpy.zeros(dshape, dtype=im.dtype)
        cv2.warpAffine(im,
                       M[:2],
                       (dshape[1], dshape[0]),
                       dst=output_im,
                       borderMode=cv2.BORDER_TRANSPARENT,
                       flags=cv2.WARP_INVERSE_MAP)
        return output_im

    def correct_colours(self, im1, im2, landmarks1):
        im1 = im1.copy()
        im2 = im2.copy()
        blur_amount = self.COLOUR_CORRECT_BLUR_FRAC * 1
        blur_amount = int(blur_amount)
        if blur_amount % 2 == 0:
            blur_amount += 1
        im1_blur = cv2.GaussianBlur(im1, (blur_amount, blur_amount), 0)
        im1_blur = cv2.GaussianBlur(im1_blur, (blur_amount, blur_amount), 0)
        im2_blur = cv2.GaussianBlur(im2, (blur_amount, blur_amount), 0)

        # Avoid divide-by-zero errors.
        im2_blur += (128 * (im2_blur <= 1.0)).astype(im2_blur.dtype)

        return (im2.astype(numpy.float64) * im1_blur.astype(numpy.float64) /
                im2_blur.astype(numpy.float64))

    def synthesize_seq(self, viseme_frame_seq):

        def generator_():
            for idx in range(len(viseme_frame_seq)):
                # print('idx', idx)
                # if idx == 24:
                #     print('right here')
                viseme_frame_landmark = viseme_frame_seq[idx]
                template_frame_landmark = self[idx]
                img = self.synthesize(viseme_frame_landmark, template_frame_landmark)
                yield img
        return generator_()
