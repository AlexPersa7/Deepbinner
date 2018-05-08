"""
Copyright 2018 Ryan Wick (rrwick@gmail.com)
https://github.com/rrwick/Deepbinner/

This file is part of Deepbinner. Deepbinner is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version. Deepbinner is distributed
in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details. You should have received a copy of the GNU General Public License along with Deepbinner.
If not, see <http://www.gnu.org/licenses/>.
"""

import argparse
import io
import pathlib
import unittest
import warnings
import sys
import deepbinner.classify
import deepbinner.load_fast5s


class TestModelLoading(unittest.TestCase):

    def setUp(self):
        model_dir = pathlib.Path(__file__).parent.parent / 'models'
        self.start_model = model_dir / 'EXP-NBD103_read_starts'
        self.end_model = model_dir / 'EXP-NBD103_read_ends'
        self.captured_output = io.StringIO()
        warnings.simplefilter('ignore', DeprecationWarning)
        warnings.simplefilter('ignore', FutureWarning)

    def test_load_2_models(self):
        start_model, start_input_size, end_model, end_input_size, output_size, model_count = \
            deepbinner.classify.load_and_check_models(self.start_model, self.end_model, 6144,
                                                      out_dest=self.captured_output)
        self.assertEqual(start_input_size, 1024)
        self.assertEqual(end_input_size, 1024)
        self.assertEqual(output_size, 13)
        self.assertEqual(model_count, 2)

    def test_load_start_model_only(self):
        start_model, start_input_size, end_model, end_input_size, output_size, model_count = \
            deepbinner.classify.load_and_check_models(self.start_model, None, 6144,
                                                      out_dest=self.captured_output)
        self.assertEqual(start_input_size, 1024)
        self.assertIsNone(end_model)
        self.assertIsNone(end_input_size)
        self.assertEqual(output_size, 13)
        self.assertEqual(model_count, 1)

    def test_load_end_model_only(self):
        start_model, start_input_size, end_model, end_input_size, output_size, model_count = \
            deepbinner.classify.load_and_check_models(None, self.end_model, 6144,
                                                      out_dest=self.captured_output)
        self.assertEqual(end_input_size, 1024)
        self.assertIsNone(start_model)
        self.assertIsNone(start_input_size)
        self.assertEqual(output_size, 13)
        self.assertEqual(model_count, 1)

    def test_bad_scan_size(self):
        with self.assertRaises(SystemExit) as context:
            _, _, _, _, _, _ = \
                deepbinner.classify.load_and_check_models(self.start_model, self.end_model, 6143,
                                                          out_dest=self.captured_output)
        self.assertTrue('--scan_size must be a multiple' in str(context.exception))


class TestFast5Classification(unittest.TestCase):

    def setUp(self):
        self.fast5_dir = pathlib.Path(__file__).parent / 'fast5_files'
        self.single_fast5 = self.fast5_dir / '5210_N125509_20170424_FN2002039725_MN19691_' \
                                             'sequencing_run_klebs_033_75349_ch17_read145_' \
                                             'strand.fast5'
        model_dir = pathlib.Path(__file__).parent.parent / 'models'
        self.start_model = model_dir / 'EXP-NBD103_read_starts'
        self.end_model = model_dir / 'EXP-NBD103_read_ends'

        self.captured_stderr = io.StringIO()
        self.captured_stdout = io.StringIO()
        sys.stderr = self.captured_stderr
        sys.stdout = self.captured_stdout

        warnings.simplefilter('ignore', DeprecationWarning)
        warnings.simplefilter('ignore', FutureWarning)

        parser = argparse.ArgumentParser()
        parser.add_argument('--verbose', default=False)
        parser.add_argument('--batch_size', default=128)
        parser.add_argument('--scan_size', default=6144)
        parser.add_argument('--score_diff', default=0.5)
        parser.add_argument('--require_both', default=False)
        self.args = parser.parse_args([])

    def tearDown(self):
        sys.stderr = sys.__stderr__
        sys.stdout = sys.__stdout__

    def test_start_model_only(self):
        fast5s = deepbinner.load_fast5s.find_all_fast5s(self.fast5_dir, verbose=True)

        start_model, start_input_size, end_model, end_input_size, output_size, model_count = \
            deepbinner.classify.load_and_check_models(self.start_model, None, 6144,
                                                      out_dest=self.captured_stderr)
        classifications, _ = \
            deepbinner.classify.classify_fast5_files(fast5s, start_model, start_input_size,
                                                     end_model, end_input_size, output_size,
                                                     self.args, full_output=False)

        self.assertEqual(classifications['cce0d2da-035e-4e74-9622-4b8884dbe070'], '5')
        self.assertEqual(classifications['4de68977-34ab-4c3e-8adf-abfa45d47690'], '11')
        self.assertEqual(classifications['58fdba7d-9b96-4613-9044-b18d038c0ea4'], 'none')
        self.assertEqual(classifications['baa78ecd-3897-4b96-ad9f-ef3f92f3d2fd'], '7')
        self.assertEqual(classifications['398f4cd6-be09-4de9-8251-efb539fc46aa'], 'none')

    def test_end_model_only(self):
        fast5s = deepbinner.load_fast5s.find_all_fast5s(self.fast5_dir, verbose=True)

        start_model, start_input_size, end_model, end_input_size, output_size, model_count = \
            deepbinner.classify.load_and_check_models(None, self.end_model, 6144,
                                                      out_dest=self.captured_stderr)
        classifications, _ = \
            deepbinner.classify.classify_fast5_files(fast5s, start_model, start_input_size,
                                                     end_model, end_input_size, output_size,
                                                     self.args, full_output=False)

        self.assertEqual(classifications['cce0d2da-035e-4e74-9622-4b8884dbe070'], '5')
        self.assertEqual(classifications['4de68977-34ab-4c3e-8adf-abfa45d47690'], '4')
        self.assertEqual(classifications['58fdba7d-9b96-4613-9044-b18d038c0ea4'], '10')
        self.assertEqual(classifications['baa78ecd-3897-4b96-ad9f-ef3f92f3d2fd'], 'none')
        self.assertEqual(classifications['398f4cd6-be09-4de9-8251-efb539fc46aa'], 'none')

    def test_start_and_end_models(self):
        fast5s = deepbinner.load_fast5s.find_all_fast5s(self.fast5_dir, verbose=True)

        start_model, start_input_size, end_model, end_input_size, output_size, model_count = \
            deepbinner.classify.load_and_check_models(self.start_model, self.end_model, 6144,
                                                      out_dest=self.captured_stderr)
        classifications, _ = \
            deepbinner.classify.classify_fast5_files(fast5s, start_model, start_input_size,
                                                     end_model, end_input_size, output_size,
                                                     self.args, full_output=False)

        self.assertEqual(classifications['cce0d2da-035e-4e74-9622-4b8884dbe070'], '5')
        self.assertEqual(classifications['4de68977-34ab-4c3e-8adf-abfa45d47690'], 'none')
        self.assertEqual(classifications['58fdba7d-9b96-4613-9044-b18d038c0ea4'], '10')
        self.assertEqual(classifications['baa78ecd-3897-4b96-ad9f-ef3f92f3d2fd'], '7')
        self.assertEqual(classifications['398f4cd6-be09-4de9-8251-efb539fc46aa'], 'none')

    def test_start_and_end_models_require_both(self):
        self.args.require_both = True
        fast5s = deepbinner.load_fast5s.find_all_fast5s(self.fast5_dir, verbose=True)

        start_model, start_input_size, end_model, end_input_size, output_size, model_count = \
            deepbinner.classify.load_and_check_models(self.start_model, self.end_model, 6144,
                                                      out_dest=self.captured_stderr)
        classifications, _ = \
            deepbinner.classify.classify_fast5_files(fast5s, start_model, start_input_size,
                                                     end_model, end_input_size, output_size,
                                                     self.args, full_output=False)

        self.assertEqual(classifications['cce0d2da-035e-4e74-9622-4b8884dbe070'], '5')
        self.assertEqual(classifications['4de68977-34ab-4c3e-8adf-abfa45d47690'], 'none')
        self.assertEqual(classifications['58fdba7d-9b96-4613-9044-b18d038c0ea4'], 'none')
        self.assertEqual(classifications['baa78ecd-3897-4b96-ad9f-ef3f92f3d2fd'], 'none')
        self.assertEqual(classifications['398f4cd6-be09-4de9-8251-efb539fc46aa'], 'none')

    def test_regular_output_start_only(self):
        start_model, start_input_size, end_model, end_input_size, output_size, model_count = \
            deepbinner.classify.load_and_check_models(self.start_model, None, 6144,
                                                      out_dest=self.captured_stderr)
        classifications, _ = \
            deepbinner.classify.classify_fast5_files([self.single_fast5], start_model,
                                                     start_input_size, end_model, end_input_size,
                                                     output_size, self.args, full_output=True)

        self.assertEqual(classifications['cce0d2da-035e-4e74-9622-4b8884dbe070'], '5')
        output_lines = self.captured_stdout.getvalue().splitlines()
        self.assertEqual(len(output_lines), 2)
        self.assertEqual(output_lines[0], 'read_ID\tbarcode_call')
        self.assertEqual(output_lines[1], 'cce0d2da-035e-4e74-9622-4b8884dbe070\t5')

    def test_verbose_output_start_only(self):
        self.args.verbose = True

        start_model, start_input_size, end_model, end_input_size, output_size, model_count = \
            deepbinner.classify.load_and_check_models(self.start_model, None, 6144,
                                                      out_dest=self.captured_stderr)
        classifications, _ = \
            deepbinner.classify.classify_fast5_files([self.single_fast5], start_model,
                                                     start_input_size, end_model, end_input_size,
                                                     output_size, self.args, full_output=True)

        self.assertEqual(classifications['cce0d2da-035e-4e74-9622-4b8884dbe070'], '5')
        output_lines = self.captured_stdout.getvalue().splitlines()
        self.assertEqual(len(output_lines), 2)
        self.assertEqual(output_lines[0], 'read_ID\tbarcode_call\t'
                                          'none\t1\t2\t3\t4\t5\t6\t7\t8\t9\t10\t11\t12')
        self.assertEqual(output_lines[1], 'cce0d2da-035e-4e74-9622-4b8884dbe070\t5\t'
                                          '0.00\t0.00\t0.00\t0.00\t0.00\t1.00\t0.00\t'
                                          '0.00\t0.00\t0.00\t0.00\t0.00\t0.00')

    def test_regular_output_end_only(self):
        start_model, start_input_size, end_model, end_input_size, output_size, model_count = \
            deepbinner.classify.load_and_check_models(None, self.end_model, 6144,
                                                      out_dest=self.captured_stderr)
        classifications, _ = \
            deepbinner.classify.classify_fast5_files([self.single_fast5], start_model,
                                                     start_input_size, end_model, end_input_size,
                                                     output_size, self.args, full_output=True)

        self.assertEqual(classifications['cce0d2da-035e-4e74-9622-4b8884dbe070'], '5')
        output_lines = self.captured_stdout.getvalue().splitlines()
        self.assertEqual(len(output_lines), 2)
        self.assertEqual(output_lines[0], 'read_ID\tbarcode_call')
        self.assertEqual(output_lines[1], 'cce0d2da-035e-4e74-9622-4b8884dbe070\t5')

    def test_verbose_output_end_only(self):
        self.args.verbose = True
        start_model, start_input_size, end_model, end_input_size, output_size, model_count = \
            deepbinner.classify.load_and_check_models(None, self.end_model, 6144,
                                                      out_dest=self.captured_stderr)
        classifications, _ = \
            deepbinner.classify.classify_fast5_files([self.single_fast5], start_model,
                                                     start_input_size, end_model, end_input_size,
                                                     output_size, self.args, full_output=True)

        self.assertEqual(classifications['cce0d2da-035e-4e74-9622-4b8884dbe070'], '5')
        output_lines = self.captured_stdout.getvalue().splitlines()
        self.assertEqual(len(output_lines), 2)
        self.assertEqual(output_lines[0], 'read_ID\tbarcode_call\t'
                                          'none\t1\t2\t3\t4\t5\t6\t7\t8\t9\t10\t11\t12')
        self.assertEqual(output_lines[1], 'cce0d2da-035e-4e74-9622-4b8884dbe070\t5\t'
                                          '0.00\t0.00\t0.00\t0.00\t0.00\t1.00\t0.00\t'
                                          '0.00\t0.00\t0.00\t0.00\t0.00\t0.00')

    def test_regular_output_start_and_end(self):
        start_model, start_input_size, end_model, end_input_size, output_size, model_count = \
            deepbinner.classify.load_and_check_models(self.start_model, self.end_model, 6144,
                                                      out_dest=self.captured_stderr)
        classifications, _ = \
            deepbinner.classify.classify_fast5_files([self.single_fast5], start_model,
                                                     start_input_size, end_model, end_input_size,
                                                     output_size, self.args, full_output=True)

        self.assertEqual(classifications['cce0d2da-035e-4e74-9622-4b8884dbe070'], '5')
        output_lines = self.captured_stdout.getvalue().splitlines()
        self.assertEqual(len(output_lines), 2)
        self.assertEqual(output_lines[0], 'read_ID\tbarcode_call')
        self.assertEqual(output_lines[1], 'cce0d2da-035e-4e74-9622-4b8884dbe070\t5')

    def test_verbose_output_start_and_end(self):
        self.args.verbose = True
        start_model, start_input_size, end_model, end_input_size, output_size, model_count = \
            deepbinner.classify.load_and_check_models(self.start_model, self.end_model, 6144,
                                                      out_dest=self.captured_stderr)
        classifications, _ = \
            deepbinner.classify.classify_fast5_files([self.single_fast5], start_model,
                                                     start_input_size, end_model, end_input_size,
                                                     output_size, self.args, full_output=True)

        self.assertEqual(classifications['cce0d2da-035e-4e74-9622-4b8884dbe070'], '5')
        output_lines = self.captured_stdout.getvalue().splitlines()
        self.assertEqual(len(output_lines), 2)
        self.assertEqual(output_lines[0], 'read_ID\tbarcode_call\tstart_none\tstart_1\tstart_2\t'
                                          'start_3\tstart_4\tstart_5\tstart_6\tstart_7\tstart_8\t'
                                          'start_9\tstart_10\tstart_11\tstart_12\t'
                                          'start_barcode_call\tend_none\tend_1\tend_2\tend_3\t'
                                          'end_4\tend_5\tend_6\tend_7\tend_8\tend_9\tend_10\t'
                                          'end_11\tend_12\tend_barcode_call')
        self.assertEqual(output_lines[1], 'cce0d2da-035e-4e74-9622-4b8884dbe070\t5\t0.00\t0.00\t'
                                          '0.00\t0.00\t0.00\t1.00\t0.00\t0.00\t0.00\t0.00\t0.00\t'
                                          '0.00\t0.00\t5\t0.00\t0.00\t0.00\t0.00\t0.00\t1.00\t'
                                          '0.00\t0.00\t0.00\t0.00\t0.00\t0.00\t0.00\t5')
