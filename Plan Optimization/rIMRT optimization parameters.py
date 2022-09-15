# --------------------------------------------------------------------------------------------------------
#                DEFINITION AUTOMATIQUE DES PARAMETRES NECESSAIRES AUX OPTIMISATIONS EN rIMRT
# --------------------------------------------------------------------------------------------------------

# Création 14/04/2021  - C. Milewski

# Ce script a pour but de définir automatiquement les paramètres requis pour la réalisation de plans rIMRT sur RayStation.
# Ces paramètres sont visibiles en cliquant sur l'icône Optimization and Segmentation dans l'onglet Plan Optimization.

from connect import *
import tkinter
import tkinter.ttk as ttk
from tkinter import *
from tkinter.messagebox import *

try:
    plan = get_current("Plan")
    beam_set = get_current("BeamSet")
    exam = get_current('Examination')
except:
    print('there is no plan/Beamset')
    exit()

#assert (beam_set.DeliveryTechnique == 'SMLC', 'Technique of beam set is not SMLC')

def get_entry(master, entry_n_beams):
    """Function aiming to get the number of beams given by user in the pop up master.
    This information is necessary to set the number of segments possible for the plan (5 segments per beam)."""

    def check_and_highlight_n_beams_int(entry_n_beams_value):
        """Function highlighting the entry of number of expected beams for the plan in red when user enter a float
        (int value expected)."""
        is_okay = True
        try:
            entry_n_beams_value = int(entry_n_beams_value)
            entry_n_beams.configure(highlightbackground="grey", highlightcolor="grey")
            assert 0 < entry_n_beams_value
        except (ValueError, AssertionError):
            entry_n_beams.configure(highlightbackground="red", highlightcolor="red")
            is_okay = False
            entry_n_beams_value = None
        return is_okay, entry_n_beams_value

    entry_n_beams_value = entry_n_beams.get()
    global number_of_beams, quit_script
    if entry_n_beams_value is not None:
        is_n_beams_int, entry_n_beams_value = check_and_highlight_n_beams_int(entry_n_beams_value)
        if is_n_beams_int:
            number_of_beams = entry_n_beams_value
        else:
            return
    master.destroy()
    quit_script = False


def checks_quit_script():
    """ Function aiming to close any pop-up when the red-cross is clicked """
    global quit_script
    if quit_script:
        print('Pop-up was quit by red-cross click -> exiting')
        sys.exit()
    quit_script = True



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
    study_shadow_test = exam.GetStoredDicomTagValueForVerification(Group=0x0008, Element=0x0050)
    print(study_shadow_test)
except:
    is_study_shadow = True

# Study instance UID verification
study_instance_uid = exam.GetStoredDicomTagValueForVerification(Group=0x0020, Element=0x000D)['Study Instance UID']
# Gets groups separated by '.'
groups = study_instance_uid.split('.')
# if group starts with 0 and is not '.0.', study instance uid is corrupted
is_study_instance_uid_corrupted = any(group.startswith('0') and group != '0' for group in groups)

# Message to display in pop up
if is_study_shadow and is_study_instance_uid_corrupted:
    message = 'Attention le CT "' + exam.Name + '" est un study shadow ET son study Instance UID du CT est ' \
                                                         'corrompu, contactez le physicien de garde (4905).'
elif is_study_shadow and is_study_instance_uid_corrupted == False:
    message = 'Attention, le CT "' + exam.Name + '" est un study shadow, contacter le physicien de garde (4905)'
elif is_study_shadow == False and is_study_instance_uid_corrupted:
    message = 'Attention le Study Instance UID du CT "' + exam.Name + '" est corrompu, contactez le physicien ' \
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

quit_script = True
number_of_beams = None
# Creates pop up asking number of beams planned
root_pop_up = Tk()
root_pop_up.title("Information nécessaire")
Label(root_pop_up, text='Renseigner le nombre de faisceaux prévus pour le plan:').grid(row=1, column=1, sticky=E)
entry_n_beams = Entry(root_pop_up, width=18, highlightthickness=1, highlightbackground="grey", highlightcolor="grey")
entry_n_beams.grid(row=1, column=2, sticky=W, padx=10)

onclick_continue_function = lambda: get_entry(root_pop_up, entry_n_beams)
Button(root_pop_up, text='Continuer', command=onclick_continue_function).grid(row=11, column=2, sticky=W, pady=4)
root_pop_up.bind('<Return>', lambda event: onclick_continue_function())
root_pop_up.bind('<Escape>', lambda event: sys.exit())
mainloop()
checks_quit_script()

#  Gets beam set number in order to get the plan optimization corresponding to the beam set (not possible to retrieve it
#  by beam set name)
beam_set_name = beam_set.DicomPlanLabel
beam_set_number = 0
while beam_set_name != plan.BeamSets[beam_set_number].DicomPlanLabel:
    beam_set_number += 1
plan_optimization = plan.PlanOptimizations[beam_set_number]

# Sets optimization parameters
assert beam_set.DeliveryTechnique == 'SMLC', 'Technique of beam set is not SMLC'
plan_optimization_parameters = plan_optimization.OptimizationParameters
tss = plan_optimization_parameters.TreatmentSetupSettings[0]
tss.SegmentConversion.MaxNumberOfSegments = number_of_beams * 5
tss.SegmentConversion.MinSegmentArea = 9
tss.SegmentConversion.MinSegmentMUPerFraction = 5
tss.SegmentConversion.MinNumberOfOpenLeafPairs = 5
tss.SegmentConversion.MinLeafEndSeparation = 2


