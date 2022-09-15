from connect import *
import math
from tkinter import *

# Script works in RS5 and RS6

machine_db = get_current("MachineDB")
beam_set = get_current("BeamSet")
ui = get_current('ui')
examination = get_current('Examination')


# STUDY SHADOW & STUDY INSTANCE UID TEST ########################################

def checks_quit_script():
    """ Function aiming to close any pop-up when the red-cross is clicked """
    global quit_script
    if quit_script:
        print('Pop-up was quit by red-cross click -> exiting')
        sys.exit()
    quit_script = True


is_study_shadow = False
is_study_instance_uid_corrupted = False

# Study shadow test
try:
    study_shadow_test = examination.GetStoredDicomTagValueForVerification(Group=0x0008, Element=0x0050)
    print(study_shadow_test)
except:
    is_study_shadow = True

# Study instance UID verification
study_instance_uid = str(examination.GetStoredDicomTagValueForVerification(Group=0x0020, Element=0x000D))
# Gets groups separated by '.'
groups = study_instance_uid.split('.')
# if group starts with 0 and is not '.0.', study instance uid is corrupted
is_study_instance_uid_corrupted = any(group.startswith('0') and group != '0' for group in groups)

# Message to display in pop up
if is_study_shadow and is_study_instance_uid_corrupted:
    message = 'Attention le CT "' + examination.Name + '" est un study shadow ET son study Instance UID du CT est ' \
                                                         'corrompu, contactez le physicien de garde (4905).'
elif is_study_shadow and is_study_instance_uid_corrupted == False:
    message = 'Attention, le CT "' + examination.Name + '" est un study shadow, contacter le physicien de garde (4905)'
elif is_study_shadow == False and is_study_instance_uid_corrupted:
    message = 'Attention le Study Instance UID du CT "' + examination.Name + '" est corrompu, contactez le physicien ' \
                                                                               'de garde (4905).'
quit_script = True
if is_study_shadow or is_study_instance_uid_corrupted:
    print(message)
    root_pop_up = Tk()
    root_pop_up.title("")
    Label(root_pop_up, text=message, foreground='red', font='Calibri 12 bold').grid(row=1, column=1, padx=5, pady=5)
    Button(root_pop_up, text='OK', command=sys.exit, width=10).grid(row=2, column=1, padx=5, pady=5)
    root_pop_up.bind('<Return>', lambda event: sys.exit())
    root_pop_up.bind('<Escape>', lambda event: sys.exit())
    mainloop()
    checks_quit_script()

################################################################################################################



# Application version check
a = [int(b) for b in ui.GetApplicationVersion().split('.')]
MainVersion = a[0]
SubVersion = a[1]
if SubVersion == 99:
    MainVersion += 1
# print "Application main version number = " + str(MainVersion)

for beam in beam_set.Beams:

    # find the machine, syntax depends on version
    if MainVersion > 5:
        machine = machine_db.GetTreatmentMachine(machineName=beam.MachineReference.MachineName, lockMode=None)
    else:  # old syntax
        machine = machine_db.GetLatestTreatmentMachineByName(machineName=beam.MachineReference.MachineName,
                                                             lockMode=None)

    mlc_physics = machine.Physics.MlcPhysics
    n_leaf_pairs = mlc_physics.UpperLayer.NumOfLeafPairs

    print("----------------")

    equivalent_square = 0

    for [segment_index, segment] in enumerate(beam.Segments):

        exposed_area = 0.0
        exposed_circumference = 0.0

        previous_exposed_side = 0.0
        previous_exposed_opening = 0.0
        previous_exposed_left_edge = 0.0
        previous_exposed_right_edge = 0.0

        jaw_positions = segment.JawPositions

        left_jaw = jaw_positions[0]
        right_jaw = jaw_positions[1]
        lower_jaw = jaw_positions[2]
        upper_jaw = jaw_positions[3]

        leaf_positions = segment.LeafPositions

        for i in range(n_leaf_pairs):

            leaf_lower_edge = mlc_physics.UpperLayer.LeafCenterPositions[i] - mlc_physics.UpperLayer.LeafWidths[i] * 0.5
            leaf_upper_edge = mlc_physics.UpperLayer.LeafCenterPositions[i] + mlc_physics.UpperLayer.LeafWidths[i] * 0.5

            exposed_lower_edge = max(leaf_lower_edge, lower_jaw)
            exposed_upper_edge = min(leaf_upper_edge, upper_jaw)

            exposed_side = max(0.0, exposed_upper_edge - exposed_lower_edge)

            left_leaf = leaf_positions[0][i]
            right_leaf = leaf_positions[1][i]

            exposed_left_edge = max(left_leaf, left_jaw)
            exposed_right_edge = min(right_leaf, right_jaw)

            exposed_opening = max(0.0, exposed_right_edge - exposed_left_edge)

            # area

            exposed_area += exposed_side * exposed_opening

            # circumference

            exposed_circumference += exposed_side * 2

            if exposed_side > 0.0:
                if previous_exposed_side == 0.0:
                    # first exposed side
                    exposed_circumference += exposed_opening
                else:
                    if i > 0:
                        # check difference vs previous leaf pair
                        left_diff = abs(exposed_left_edge - previous_exposed_left_edge)
                        right_diff = abs(exposed_right_edge - previous_exposed_right_edge)

                        # circumference cannot be more than sum of openings (interdigitation)
                        exposed_circumference += min(left_diff + right_diff, exposed_opening + previous_exposed_opening)

            if exposed_side == 0.0 and previous_exposed_side > 0.0:
                # previous was last exposed side
                exposed_circumference += previous_exposed_opening

            # done, record current state as previous
            previous_exposed_opening = exposed_opening
            previous_exposed_side = exposed_side
            previous_exposed_left_edge = exposed_left_edge
            previous_exposed_right_edge = exposed_right_edge

            # end of leaf loop

        # possibly, the last leaf was still exposed
        if previous_exposed_side > 0.0:
            exposed_circumference += previous_exposed_opening


        equivalent_square = equivalent_square + (4 * exposed_area / exposed_circumference) * segment.RelativeWeight
    print("Beam : [" + beam.Name + "]")
    print("Equivalent square : " + str(round(equivalent_square, 1))+" cm")


