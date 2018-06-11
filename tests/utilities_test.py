##
# \file utilities_test.py
#  \brief  Class containing unit tests for utility functions
#
#  \author Michael Ebner (michael.ebner.14@ucl.ac.uk)
#  \date April 2018

import os
import numpy as np
import SimpleITK as sitk
import unittest

import pysitk.simple_itk_helper as sitkh

import simplereg.utilities as utils
from simplereg.definitions import DIR_TMP, DIR_DATA, DIR_TEST


class UtilitiesTest(unittest.TestCase):

    def setUp(self):
        self.precision = 7

    def test_convert_regaladin_to_sitk_transform(self):
        for dim in [2, 3]:
            path_to_regaladin_transform = os.path.join(
                DIR_TEST, "%dD_regaladin_Target_Source.txt" % dim)
            path_to_sitk_reference_transform = os.path.join(
                DIR_TEST, "%dD_sitk_Target_Source.txt" % dim)

            matrix_regaladin = np.loadtxt(path_to_regaladin_transform)
            transform_sitk = utils.convert_regaladin_to_sitk_transform(
                matrix_regaladin)
            transform_reference_sitk = sitk.AffineTransform(
                sitk.ReadTransform(path_to_sitk_reference_transform))

            nda = np.array(transform_sitk.GetParameters())
            nda_reference = transform_reference_sitk.GetParameters()

            self.assertAlmostEqual(
                np.sum(np.abs(nda - nda_reference)), 0,
                places=self.precision)

    def test_convert_sitk_to_regaladin_transform(self):
        for dim in [2, 3]:
            path_to_sitk_transform = os.path.join(
                DIR_TEST, "%dD_sitk_Target_Source.txt" % dim)
            path_to_reference_transform = os.path.join(
                DIR_TEST, "%dD_regaladin_Target_Source.txt" % dim)

            transform_sitk = sitk.AffineTransform(sitk.ReadTransform(
                path_to_sitk_transform))

            nda_reference = np.loadtxt(path_to_reference_transform)
            nda = utils.convert_sitk_to_regaladin_transform(transform_sitk)

            self.assertAlmostEqual(
                np.sum(np.abs(nda - nda_reference)), 0,
                places=self.precision)

    def test_convert_sitk_to_flirt_transform(self):
        for dim in [3]:
            path_to_sitk_transform = os.path.join(
                DIR_TEST, "%dD_sitk_Target_Source.txt" % dim)
            path_to_fixed = os.path.join(
                DIR_DATA, "%dD_Brain_Target.nii.gz" % dim)
            path_to_moving = os.path.join(
                DIR_DATA, "%dD_Brain_Source.nii.gz" % dim)
            path_to_res = os.path.join(
                DIR_TMP, "%dD_sitk2flirt_target_Source.txt" % dim)
            path_to_reference_transform = os.path.join(
                DIR_TEST, "%dD_flirt_Target_Source.txt" % dim)

            utils.convert_sitk_to_flirt_transform(
                path_to_sitk_transform, path_to_fixed, path_to_moving, path_to_res)
            nda = np.loadtxt(path_to_res)

            nda_reference = np.loadtxt(
                path_to_reference_transform)

            self.assertAlmostEqual(
                np.sum(np.abs(nda - nda_reference)), 0,
                places=self.precision)

    def test_convert_flirt_to_sitk_transform(self):
        for dim in [3]:
            path_to_flirt_transform = os.path.join(
                DIR_TEST, "%dD_flirt_Target_Source.txt" % dim)
            path_to_fixed = os.path.join(
                DIR_DATA, "%dD_Brain_Target.nii.gz" % dim)
            path_to_moving = os.path.join(
                DIR_DATA, "%dD_Brain_Source.nii.gz" % dim)
            path_to_res = os.path.join(
                DIR_TMP, "%dD_flirt2sitk_target_Source_.txt" % dim)
            path_to_reference_transform = os.path.join(
                DIR_TEST, "%dD_sitk_Target_Source.txt" % dim)

            utils.convert_flirt_to_sitk_transform(
                path_to_flirt_transform, path_to_fixed, path_to_moving, path_to_res)
            transform_sitk = sitkh.read_transform_sitk(path_to_res)

            transform_ref_sitk = sitkh.read_transform_sitk(
                path_to_reference_transform)

            nda_reference = np.array(transform_ref_sitk.GetParameters())
            nda = np.array(transform_sitk.GetParameters())

            # Conversion to FLIRT only provides 4 decimal places
            self.assertAlmostEqual(
                np.sum(np.abs(nda - nda_reference)), 0,
                places=2)

    def test_get_resampling_space_properties(self):
        for dim in [2, 3]:
            path_to_image = os.path.join(
                DIR_DATA, "%dD_Brain_Target.nii.gz" % dim)

            image_sitk = sitk.ReadImage(path_to_image)

            # image size is (181, 217). Division by 2 problematic otherwise
            if dim == 2:
                image_sitk = image_sitk[0:180, 0:200]

            spacing_in = np.array(image_sitk.GetSpacing())
            size_in = np.array(image_sitk.GetSize()).astype("int")
            origin = np.array(image_sitk.GetOrigin())
            direction = image_sitk.GetDirection()

            factor_spacing = 13.
            factor_add_to_grid = -3.5

            spacing = factor_spacing * spacing_in
            add_to_grid = factor_add_to_grid * spacing
            size = np.round(size_in / factor_spacing + 2 * factor_add_to_grid)

            size_out, origin_out, spacing_out, direction_out = \
                utils.get_space_resampling_properties(
                    image_sitk, spacing, add_to_grid)

            if dim == 3:
                a_x = image_sitk.TransformIndexToPhysicalPoint(
                    (1, 0, 0)) - origin
                a_y = image_sitk.TransformIndexToPhysicalPoint(
                    (0, 1, 0)) - origin
                a_z = image_sitk.TransformIndexToPhysicalPoint(
                    (0, 0, 1)) - origin
                e_x = a_x / np.linalg.norm(a_x)
                e_y = a_y / np.linalg.norm(a_y)
                e_z = a_z / np.linalg.norm(a_z)
                offset = (e_x + e_y + e_z) * add_to_grid
                origin -= offset
            else:
                a_x = image_sitk.TransformIndexToPhysicalPoint((1, 0)) - origin
                a_y = image_sitk.TransformIndexToPhysicalPoint((0, 1)) - origin
                e_x = a_x / np.linalg.norm(a_x)
                e_y = a_y / np.linalg.norm(a_y)
                offset = (e_x + e_y) * add_to_grid
                origin -= offset

            self.assertEqual(np.sum(np.abs(spacing_out - spacing)), 0)
            self.assertEqual(np.sum(np.abs(size_out - size)), 0)
            self.assertEqual(np.sum(np.abs(direction_out - direction)), 0)
            self.assertEqual(np.sum(np.abs(origin_out - origin)), 0)

            # check whether extension/cropping does not change 'pixel position'
            resampled_image_sitk = sitk.Resample(
                image_sitk,
                size_out,
                getattr(sitk, "Euler%dDTransform" % dim)(),
                sitk.sitkNearestNeighbor,
                origin_out,
                spacing_out,
                direction_out,
                0,
                image_sitk.GetPixelIDValue()
            )
            image_sitk = sitk.Resample(
                image_sitk,
                resampled_image_sitk,
                getattr(sitk, "Euler%dDTransform" % dim)(),
                sitk.sitkNearestNeighbor,
            )
            nda_diff = sitk.GetArrayFromImage(
                image_sitk - resampled_image_sitk)
            self.assertEqual(np.sum(np.abs(nda_diff)), 0)
