"""Layered Human (AnatomyExplorer) hepatobiliary centrelines and radii, ported as plain Python literals.

Source : https://github.com/ethanprince4/AnatomyExplorer
File   : app/micro/hepatobiliary.py
Commit : d5f522fa51d6919b6a3fe28a9e075b531320a92a
SHA-256 of that file: f0dabd45df71e0a7f1809d3dfcdfc2ea42695683b0cf8eec36a7d5fe94788aab

The values below were copied UNCHANGED from the module-level constant assignments of that file
(and from the literal radii/branch arguments of build_gallbladder, build_ducts and build_vessels),
read with Python's `ast` module (literal_eval-style; the names CONFLUENCE, TRIFURC and AMPULLA were
resolved to their literal values). The source module was never imported or executed.

Frame of these values (as in the source): x = the patient's left, y = superior, z = anterior; origin in
the midline at the level of L1; 1 unit = 10 cm; NORMAL situs (the gallbladder lies at x < 0).
They are NOT mirrored here. build_anatomy_1654623.py mirrors them once (x -> -x) for situs inversus,
scales them to metres and translates them into the case frame; the transform is recorded in
content/assets/cases/cmcr-1654623/anatomy.json ("portedCentrelineTransform").

Licence of the source (it covers the procedural builders in app/micro, see its LICENSE "Scope"):

    MIT License

    Copyright (c) 2026 Ethan Prince

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""

SOURCE_URL = "https://github.com/ethanprince4/AnatomyExplorer"
SOURCE_FILE = "app/micro/hepatobiliary.py"
SOURCE_COMMIT = "d5f522fa51d6919b6a3fe28a9e075b531320a92a"
SOURCE_SHA256 = "f0dabd45df71e0a7f1809d3dfcdfc2ea42695683b0cf8eec36a7d5fe94788aab"
COPYRIGHT = "Copyright (c) 2026 Ethan Prince"
LICENSE = "MIT"
UNIT_METRES = 0.1          # 1 source unit = 10 cm
AXES = "x = patient left, y = superior, z = anterior; origin midline at L1; normal situs"

# ---------------------------------------------------------------- gallbladder (source lines 479-482, 579-584, 742-765)
# centreline, fundus -> neck, and its radii
GB_CTRL = [(-0.465, -0.1, 0.66), (-0.44, -0.07, 0.55), (-0.4, -0.03, 0.43), (-0.355, 0.015, 0.32), (-0.315, 0.045, 0.24), (-0.29, 0.075, 0.17), (-0.278, 0.075, 0.125)]
GB_R = [0.125, 0.125, 0.115, 0.095, 0.075, 0.052, 0.03]
# Hartmann's pouch ellipsoid in _gb_shapes (extra = 0.0)
HARTMANN_CENTRE = (-0.3, 0.02, 0.2)
HARTMANN_RADII = (0.065, 0.06, 0.075)
# build_gallbladder: parts by fraction t of arc length along GB_CTRL (fundus end t=0, neck end t=1)
GB_PART_SPLIT = [('gb_fundus', -1.0, 0.2), ('gb_body', 0.2, 0.66), ('gb_neck', 0.66, 2.0)]

# ---------------------------------------------------------------- biliary tree (source lines 484-492)
RHD_CTRL = [(-0.34, 0.25, 0.1), (-0.26, 0.22, 0.1), (-0.17, 0.2, 0.1)]
LHD_CTRL = [(0.04, 0.22, 0.14), (-0.05, 0.21, 0.12), (-0.17, 0.2, 0.1)]
CHD_CTRL = [(-0.17, 0.2, 0.1), (-0.185, 0.11, 0.1), (-0.2, 0.03, 0.09), (-0.211, -0.035, 0.082)]
CYSTIC_CTRL = [(-0.278, 0.075, 0.13), (-0.285, 0.03, 0.118), (-0.272, -0.02, 0.104), (-0.245, -0.045, 0.09), (-0.215, -0.04, 0.083)]
AMPULLA = (-0.443, -0.505, -0.1)
CBD_CTRL = [(-0.211, -0.035, 0.082), (-0.218, -0.1, 0.065), (-0.23, -0.17, 0.035), (-0.255, -0.26, -0.03), (-0.31, -0.37, -0.09), (-0.37, -0.45, -0.117), (-0.415, -0.49, -0.114), (-0.443, -0.505, -0.1)]      # last point = AMPULLA

# ---------------------------------------------------------------- portal venous system (source lines 501-505)
CONFLUENCE = (-0.01, -0.27, 0.115)
PV_CTRL = [(-0.01, -0.27, 0.115), (-0.06, -0.12, 0.05), (-0.11, 0.03, 0.005), (-0.14, 0.14, 0.0), (-0.15, 0.19, 0.01)]
RPV_CTRL = [(-0.15, 0.19, 0.01), (-0.26, 0.2, 0.0), (-0.38, 0.23, 0.0)]
LPV_CTRL = [(-0.15, 0.19, 0.01), (-0.06, 0.2, 0.03), (0.03, 0.2, 0.07), (0.055, 0.2, 0.18), (0.055, 0.19, 0.3)]

# ---------------------------------------------------------------- arteries (source lines 511-521)
COELIAC_O = (0.08, 0.02, -0.28)
TRIFURC = (0.08, 0.03, -0.1)
CHA_CTRL = [(0.08, 0.03, -0.1), (-0.01, 0.0, -0.03), (-0.08, -0.03, 0.02), (-0.12, -0.05, 0.05)]
PHA_CTRL = [(-0.12, -0.05, 0.05), (-0.122, 0.04, 0.06), (-0.112, 0.13, 0.062), (-0.1, 0.18, 0.064)]
RHA_CTRL = [(-0.1, 0.18, 0.064), (-0.16, 0.195, 0.05), (-0.24, 0.205, 0.045), (-0.33, 0.22, 0.05)]
LHA_CTRL = [(-0.1, 0.18, 0.064), (-0.03, 0.2, 0.08), (0.04, 0.215, 0.1), (0.1, 0.26, 0.14)]
CYSTIC_A_CTRL = [(-0.24, 0.205, 0.045), (-0.275, 0.18, 0.09), (-0.3, 0.13, 0.15), (-0.335, 0.1, 0.23), (-0.37, 0.08, 0.34)]
GDA_CTRL = [(-0.12, -0.05, 0.05), (-0.125, -0.14, 0.09), (-0.13, -0.25, 0.155), (-0.14, -0.38, 0.215), (-0.17, -0.47, 0.235)]
# second cystic-artery branch, a literal in build_vessels (source line 1001), starts on CYSTIC_A_CTRL[2]
CYSTIC_A_BRANCH_CTRL = [(-0.3, 0.13, 0.15), (-0.26, 0.08, 0.22), (-0.3, 0.04, 0.33)]
# terminal continuation of the gastroduodenal artery, a literal in build_vessels (source line 1004),
# starts on GDA_CTRL[-2]
GDA_BRANCH_CTRL = [(-0.14, -0.38, 0.215), (-0.05, -0.49, 0.3), (0.08, -0.48, 0.38)]

# ---------------------------------------------------------------- tube radii (source units), with the source line
# A list is a radius profile interpolated linearly along the normalised arc length (taper() in app/micro/organic.py).
RADII = {
    'RHD_CTRL': [0.02, 0.021],                   # build_ducts, line 771
    'LHD_CTRL': [0.019, 0.021],                  # build_ducts, line 775
    'CHD_CTRL': [0.026, 0.026, 0.027],           # build_ducts, line 779
    'CYSTIC_CTRL': [0.024, 0.018, 0.018, 0.019], # build_gallbladder, line 762
    'CBD_CTRL': [0.03, 0.031, 0.03, 0.028, 0.022, 0.016], # build_ducts, line 781
    'PV_CTRL': [0.066, 0.064, 0.062, 0.062],     # build_vessels, line 968
    'RPV_CTRL': [0.05, 0.047, 0.045],            # build_vessels, line 969
    'LPV_CTRL': [0.04, 0.038, 0.038, 0.036, 0.034], # build_vessels, line 971
    'CHA_CTRL': [0.025, 0.024, 0.023],           # build_vessels, line 988
    'PHA_CTRL': [0.02, 0.019, 0.018],            # build_vessels, line 990
    'RHA_CTRL': [0.015, 0.014, 0.013],           # build_vessels, line 992
    'LHA_CTRL': [0.013, 0.012, 0.011],           # build_vessels, line 996
    'CYSTIC_A_CTRL': [0.009, 0.008, 0.007, 0.005], # build_vessels, line 1000
    'CYSTIC_A_BRANCH_CTRL': [0.006, 0.004, 0.003], # build_vessels, line 1001
    'GDA_CTRL': [0.016, 0.015, 0.014, 0.012],    # build_vessels, line 1003
    'GDA_BRANCH_CTRL': [0.011, 0.01, 0.009],     # build_vessels, line 1004
}

