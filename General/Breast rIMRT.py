# Script recorded 14 Nov 2020, 18:39:22

#   RayStation version: 9.2.0.483
#   Selected patient: ...

from connect import *

import tkinter.ttk as ttk
from tkinter import *
from tkinter.messagebox import *
import re
import datetime

import statetree

# statetree.RunStateTree(True)
# statetree.RunMachineStateTree(None,True)
# statetree.RunPatientDBStateTree(True)
# statetree.RunMachineDBStateTree(True)
# statetree.RunClinicDBStateTree(True)
# statetree.RunUiStateTree(True)

case = get_current("Case")
patient = get_current("Patient")
machine_db = get_current("MachineDB")
patient_db = get_current("PatientDB")

# Dictionary matching possible doses for this technique with associated template of clinical goals (editable):
dose_fractions_value_template_matching = {(28.5, 5): 'Sein/Paroi Mamy Flash 28,5Gy/5fr',
                                          (50.0, 25): 'Sein/Paroi seul 50Gy +/- Boost 66Gy 3D',
                                          (40.05, 15): 'Sein/Paroi seul 40,05Gy +/- Boost 56,05Gy seq',
                                          (26.0, 5): 'Sein/Paroi 26Gy +/- Boost 13,35Gy FAST-Forward'}


def create_ring(patient, case, examination, ptv_name, roi_geometries):
    """ Creates a ring around the PTV derived from 2 intermediary rings. If the ring and intermediary already exist :
    update them, otherwise : create them."""

    def does_roi_exist(roi_name, roi_geometries_names):
        """ Returns whether roi exists. """
        return roi_name in roi_geometries_names

    roi_geometries_names = [roi.OfRoi.Name for roi in roi_geometries]

    # Intermediary ring 1
    name_inter_ring_1 = 'inter_ring_1_' + ptv_name
    if does_roi_exist(name_inter_ring_1, roi_geometries_names):
        case.PatientModel.UpdateDerivedGeometries(RoiNames=[name_inter_ring_1], Examination=examination,
                                                  Algorithm="Auto", AreEmptyDependenciesAllowed=False)
        patient.SetRoiVisibility(RoiName=name_inter_ring_1, IsVisible=False)
    else:
        case.PatientModel.CreateRoi(Name=name_inter_ring_1, Color="Black", Type="Undefined", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        case.PatientModel.RegionsOfInterest[name_inter_ring_1].SetAlgebraExpression(
            ExpressionA={'Operation': "Union", 'SourceRoiNames': [ptv_name],
                         'MarginSettings': {'Type': "Expand", 'Superior': 4.3, 'Inferior': 4.3, 'Anterior': 4.3,
                                            'Posterior': 4.3, 'Right': 4.3, 'Left': 4.3}},
            ExpressionB={'Operation': "Union", 'SourceRoiNames': [ptv_name],
                         'MarginSettings': {'Type': "Expand", 'Superior': 0.3, 'Inferior': 0.3, 'Anterior': 0.3,
                                            'Posterior': 0.3, 'Right': 0.3, 'Left': 0.3}},
            ResultOperation="Subtraction",
            ResultMarginSettings={'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                  'Right': 0, 'Left': 0})
        case.PatientModel.RegionsOfInterest[name_inter_ring_1].UpdateDerivedGeometry(Examination=examination,
                                                                                     Algorithm="Auto")
        patient.SetRoiVisibility(RoiName=name_inter_ring_1, IsVisible=False)

    # Intermediary ring 2
    name_inter_ring_2 = 'inter_ring_2_' + ptv_name
    if does_roi_exist(name_inter_ring_2, roi_geometries_names):
        case.PatientModel.UpdateDerivedGeometries(RoiNames=[name_inter_ring_2], Examination=examination,
                                                  Algorithm="Auto", AreEmptyDependenciesAllowed=False)
        patient.SetRoiVisibility(RoiName=name_inter_ring_2, IsVisible=False)
    else:
        case.PatientModel.CreateRoi(Name=name_inter_ring_2, Color="Black", Type="Undefined", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        case.PatientModel.RegionsOfInterest[name_inter_ring_2].SetAlgebraExpression(
            ExpressionA={'Operation': "Union", 'SourceRoiNames': [name_inter_ring_1],
                         'MarginSettings': {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0,
                                            'Posterior': 0, 'Right': 0, 'Left': 0}},
            ExpressionB={'Operation': "Union", 'SourceRoiNames': [r"External"],
                         'MarginSettings': {'Type': "Contract", 'Superior': 0.5, 'Inferior': 0.5, 'Anterior': 0.5,
                                            'Posterior': 0.5, 'Right': 0.5, 'Left': 0.5}},
            ResultOperation="Intersection",
            ResultMarginSettings={'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                  'Right': 0, 'Left': 0})
        case.PatientModel.RegionsOfInterest[name_inter_ring_2].UpdateDerivedGeometry(Examination=examination,
                                                                                     Algorithm="Auto")
        patient.SetRoiVisibility(RoiName=name_inter_ring_2, IsVisible=False)

    # Final ring
    ring_name = 'RING_' + ptv_name + '_0_3_cm_4_3_cm'
    if does_roi_exist(ring_name, roi_geometries_names):
        case.PatientModel.UpdateDerivedGeometries(RoiNames=[ring_name], Examination=examination,
                                                  Algorithm="Auto", AreEmptyDependenciesAllowed=False)
        patient.SetRoiVisibility(RoiName=ring_name, IsVisible=True)
    else:
        case.PatientModel.CreateRoi(Name=ring_name, Color="Red", Type="Undefined", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        case.PatientModel.RegionsOfInterest[ring_name].SetAlgebraExpression(
            ExpressionA={'Operation': "Union", 'SourceRoiNames': [name_inter_ring_2],
                         'MarginSettings': {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0,
                                            'Posterior': 0, 'Right': 0, 'Left': 0}},
            ExpressionB={'Operation': "Union", 'SourceRoiNames': [r"Heart", r"Lungs"],
                         'MarginSettings': {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0,
                                            'Posterior': 0, 'Right': 0, 'Left': 0}}, ResultOperation="Subtraction",
            ResultMarginSettings={'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                  'Right': 0, 'Left': 0})
        case.PatientModel.RegionsOfInterest[ring_name].UpdateDerivedGeometry(Examination=examination, Algorithm="Auto")
        patient.SetRoiVisibility(RoiName=ring_name, IsVisible=True)
    return ring_name


def checks_quit_script():
    """ Function aiming to close any pop-up when the red-cross is clicked """
    global quit_script
    if quit_script:
        print('Pop-up was quit by red-cross click -> exiting')
        sys.exit()
    quit_script = True


def ask_for_ct_curve(parent_master):
    """ Function only called if a CT curve was already set previously to this script and is different to the one
    chosen by the user (in the first pop up asking for all information). A pop up warning the user about possible dose
    clearance appears and user can choose whether to continue with the same curve or change."""

    def modify_ct_curve():
        global continue_with_ct_curve
        continue_with_ct_curve = False
        top_master.destroy()

    def continue_script():
        global continue_with_ct_curve
        continue_with_ct_curve = True
        top_master.destroy()

    top_master = Toplevel(parent_master)
    top_master.title("Attention")
    Label(top_master,
          text="En choisissant cette courbe CT toutes les doses calculées avec la courbe " + selected_examination
          .EquipmentInfo.ImagingSystemReference.ImagingSystemName + " seront effacées.").grid(
        row=1, column=1, sticky=E)
    Button(top_master, text='Choisir une autre courbe CT', command=modify_ct_curve).grid(row=11, column=1, sticky=W,
                                                                                         pady=4)
    Button(top_master, text='Continuer le script', command=continue_script).grid(row=11, column=18, sticky=W, pady=4)
    top_master.wait_window()


def get_entry(master, scrolling_menu_examinations, scrolling_menu_ct_curves, scrolling_menu_ct_curves_values,
              scrolling_menu_machines, entry_fractions, entry_dose, scrolling_menu_breast, scrolling_menu_ptv):
    """ Function aiming to retrieve the information the user provided for the plan creation
        :param master: tkinter window object
        :param scrolling_menu_examinations: list of available CT
        :param scrolling_menu_ct_curves: list of available CT curves
        :param scrolling_menu_machines: list of available machines
        :param entry_fractions: number of fractions entered by user
        :param entry_dose: dose entered by user
        :param scrolling_menu_breast: list of breast sides
        :param multiple_cts: True if the case has multiple CTs, otherwise False
        :param scrolling_menu_ptv: a scrolling menu if there are multiple ptv for the selected CT or None
    """

    def check_and_hightlight_dose_fraction_values(entry_fractions_value, entry_dose_value):
        are_appropriate = True
        try:
            entry_fractions_value = int(entry_fractions_value)
            entry_fractions.configure(highlightbackground="grey", highlightcolor="grey")
        except ValueError:
            entry_fractions.configure(highlightbackground="red", highlightcolor="red")
            are_appropriate = False
            entry_fractions_value = None
        try:
            entry_dose_value = float(entry_dose_value)
            entry_dose.configure(highlightbackground="grey", highlightcolor="grey")
        except ValueError:
            entry_dose.configure(highlightbackground="red", highlightcolor="red")
            are_appropriate = False
            entry_dose_value = None
        return are_appropriate, entry_fractions_value, entry_dose_value

    entry_ct = scrolling_menu_examinations.get() if scrolling_menu_examinations is not None else None
    entry_ct_curves_value = scrolling_menu_ct_curves.get()
    entry_machine_value = scrolling_menu_machines.get()
    entry_fractions_value = entry_fractions.get()
    entry_dose_value = entry_dose.get()
    entry_breast = scrolling_menu_breast.get()
    entry_ptv = scrolling_menu_ptv.get() if scrolling_menu_ptv is not None else None
    if (entry_ct is not None and entry_ct == '') or entry_ct_curves_value == '' or entry_machine_value == '' or \
            entry_fractions_value == '' or entry_dose_value == '' or \
            (scrolling_menu_ptv is not None and entry_ptv == '') or entry_breast == '':
        check_and_hightlight_dose_fraction_values(entry_fractions_value, entry_dose_value)
        return

    # Checks dose and fraction input values are appropriate
    are_dose_fraction_okay, entry_fractions_value, entry_dose_value = check_and_hightlight_dose_fraction_values(
        entry_fractions_value, entry_dose_value)
    if not are_dose_fraction_okay:
        return

    # Determines name of CT curve input (which contains name + date + time of possible CT curves)
    index_of_selected_ct_curve = [i for i, ct_curve_name_time in enumerate(scrolling_menu_ct_curves_values)
                                  if entry_ct_curves_value == ct_curve_name_time]
    assert len(index_of_selected_ct_curve) != 0, 'Found no associated ct_curve with selected name: should not happen'
    assert len(index_of_selected_ct_curve) < 2, 'Found multiple ct_curve with selected name: should not happen'
    index_of_selected_ct_curve = index_of_selected_ct_curve[0]
    entry_ct_curve_name = ct_curves_names[index_of_selected_ct_curve]
    global continue_with_ct_curve
    # Warns user another CT curve has been set previously to this script (which could clear doses of potential other plans)
    if selected_examination.EquipmentInfo.ImagingSystemReference is not None and \
            selected_examination.EquipmentInfo.ImagingSystemReference.ImagingSystemName != entry_ct_curve_name:
        ask_for_ct_curve(master)
    else:
        continue_with_ct_curve = True

    if not continue_with_ct_curve:
        return

    # Assign selected values to variables
    global selected_ct_value, selected_ct_curve, selected_machine, n_fractions, dose_value, selected_breast_side, \
        selected_ptv_name, quit_script
    if scrolling_menu_examinations is not None:
        selected_ct_value = entry_ct
    selected_ct_curve = entry_ct_curve_name
    selected_machine = entry_machine_value
    n_fractions = entry_fractions_value
    dose_value = entry_dose_value
    selected_breast_side = entry_breast
    if scrolling_menu_ptv is not None:
        selected_ptv_name = entry_ptv
    quit_script = False
    master.destroy()


def process_selected_ct(scrolling_menu_examinations, all_examinations, case, row_item_combobox_ptv):
    """Function aiming to check if several PTVs are associated with the selected CT.
    If there are, creates a menu with the possible PTVs in the first window asking for plan information."""
    global scrolling_menu_ptv, optional_ptv_label, selected_ptv_name, selected_examination
    if scrolling_menu_examinations is not None:
        entry_value = scrolling_menu_examinations.get()
        selected_ptv_name = None
        if entry_value == '':
            if scrolling_menu_ptv is not None:
                scrolling_menu_ptv.destroy()
                scrolling_menu_ptv = None
                optional_ptv_label.grid_forget()
            return
        # Find CT name based on selected value
        entry_value = re.search(r'\d+\) (.*?) réalisé le (.*)', entry_value)
        selected_ct_name = entry_value.group(1)
        selected_ct_date_time = entry_value.group(2)
        selected_examination = [examination for examination in all_examinations if examination.Name == selected_ct_name
                                and str(examination.GetExaminationDateTime()) == selected_ct_date_time]
        assert len(selected_examination) != 0, 'Found no associated examination with selected name: should not happen'
        assert len(selected_examination) < 2, 'Found multiple examinations with selected name: should not happen'
        selected_examination = selected_examination[0]
    else:
        assert selected_examination is not None

    # Seek number of PTVs in selected CT
    roi_geometries = case.PatientModel.StructureSets[selected_examination.Name].RoiGeometries
    ptv_names = [roi.OfRoi.Name for roi in roi_geometries if roi.OfRoi.Type.lower() == 'ptv' and roi.HasContours()]
    if len(ptv_names) == 1:
        if scrolling_menu_ptv is not None:
            scrolling_menu_ptv.destroy()
            scrolling_menu_ptv = None
            optional_ptv_label.grid_forget()
        selected_ptv_name = ptv_names[0]
        return

    # Create a menu with possible ptv names
    optional_ptv_label.grid(row=row_item_combobox_ptv, column=1, sticky=E)
    scrolling_menu_ptv = ttk.Combobox(root_pop_up, values=sorted(ptv_names), width=17, state='readonly')
    scrolling_menu_ptv.grid(row=row_item_combobox_ptv, column=2, sticky=W, padx=10)


def print_associated_clinical_goals_template(clinical_goals_template):
    """Function printing the clinical goal template corresponding to the dose chosen by user under the dose entry
    in pop up."""
    global associated_template_label
    entered_dose = entry_dose.get()
    entered_fraction = entry_fractions.get()
    entered_dose = float(entered_dose)
    entered_fraction = int(entered_fraction)
    if entered_dose == '':
        optional_associated_template_label.grid_forget()
        if associated_template_label is not None:
            associated_template_label.destroy()
            associated_template_label = None
    else:
        optional_associated_template_label.grid(row=row_item + 4, column=1, sticky=E)
        if (entered_dose, entered_fraction) not in dose_fractions_value_template_matching.keys():
            label_to_print = 'Pas de template clinical goals associé'
        else:
            label_to_print = clinical_goals_template[(entered_dose, entered_fraction)]
        # tkinter draw labels on top of each other if not destroy, so destroy previous one
        if associated_template_label is not None:
            associated_template_label.destroy()
            associated_template_label = None
        associated_template_label = Label(root_pop_up, text=label_to_print)
        associated_template_label.grid(row=row_item + 4, column=2, sticky=W, padx=10)


quit_script = True

# Variables to be assigned by the user
selected_ct_value = None
selected_ct_curve = None
selected_machine = None
n_fractions = None
dose_value = None
selected_ptv_name = None
selected_breast_side = None
continue_with_ct_curve = False

# Checks number of CTs, if only 1 => selects it, if more than 1 => gets ct names in scrolling_menu_examinations_values
selected_examination = None
scrolling_menu_examinations_values = None
multiple_cts = False
all_examinations = case.Examinations
if len(all_examinations) == 0:
    print('Found 0 CT. Exiting...')
    exit()
elif len(all_examinations) == 1:
    selected_examination = case.Examinations[0]
else:
    multiple_cts = True
    scrolling_menu_examinations_values = [
        f'{i + 1}) {examination.Name} réalisé le {examination.GetExaminationDateTime()}'
        for i, examination in enumerate(all_examinations)]

# Lists CT curves names
ct_systems_dict = machine_db.GetCtImagingSystemsNameAndCommissionTime()
ct_curves_names = sorted(list(ct_systems_dict.keys()))
ct_curves_names_times = [ct_curve + ' ' + str(ct_systems_dict[ct_curve]) for ct_curve in ct_curves_names]

# Lists machine names
available_machines = machine_db.QueryCommissionedMachineInfo(Filter={'IsLinac': True})
available_machines_names = [machine["Name"] for machine in available_machines]

# Lists breast side
possible_breast_sides = ['Sein droit', 'Sein gauche']

# Pop up asking all the information needed to create the plan
root_pop_up = Tk()
root_pop_up.title("Paramètres du plan")
row_item = 1

scrolling_menu_examinations = None
# If selected CT has multiple PTVs, creates a menu with possible PTVs names
optional_ptv_label = Label(root_pop_up, text='PTV :')
scrolling_menu_ptv = None
if multiple_cts:
    Label(root_pop_up, text="CT :").grid(row=row_item, column=1, sticky=E)
    scrolling_menu_examinations = ttk.Combobox(root_pop_up, values=scrolling_menu_examinations_values, width=50,
                                               state='readonly')
    scrolling_menu_examinations.grid(row=row_item, column=2, sticky=W, padx=10)
    scrolling_menu_examinations.bind("<<ComboboxSelected>>", lambda event: process_selected_ct(
        scrolling_menu_examinations, all_examinations, case, row_item_combobox_ptv=2))
else:
    process_selected_ct(None, all_examinations, case, row_item_combobox_ptv=2)
row_item += 2
# CT curve
Label(root_pop_up, text="Courbe CT :").grid(row=row_item, column=1, sticky=E)
scrolling_menu_ct_curves = ttk.Combobox(root_pop_up, values=ct_curves_names_times, width=50, state='readonly')
scrolling_menu_ct_curves.grid(row=row_item, column=2, sticky=W, padx=10)
# Machine
Label(root_pop_up, text="Machine de traitement :").grid(row=row_item + 1, column=1, sticky=E)
scrolling_menu_machines = ttk.Combobox(root_pop_up, values=sorted(available_machines_names), width=17, state='readonly')
scrolling_menu_machines.grid(row=row_item + 1, column=2, sticky=W, padx=10)
# Fraction number
Label(root_pop_up, text='Nombre de fractions :').grid(row=row_item + 2, column=1, sticky=E)
entry_fractions = Entry(root_pop_up, width=18, highlightthickness=1, highlightbackground="grey", highlightcolor="grey")
entry_fractions.grid(row=row_item + 2, column=2, sticky=W, padx=10)
# Dose
Label(root_pop_up, text='Dose totale (Gy) :').grid(row=row_item + 3, column=1, sticky=E)
entry_dose = Entry(root_pop_up, width=18, highlightthickness=1, highlightbackground="grey", highlightcolor="grey")
entry_dose.bind('<FocusOut>',
                lambda event: print_associated_clinical_goals_template(dose_fractions_value_template_matching))
entry_dose.grid(row=row_item + 3, column=2, sticky=W, padx=10)
# Template associated to the entered dose value
optional_associated_template_label = Label(root_pop_up, text='Clinical goals associés :')
# optional_associated_template_label.grid_forget()
associated_template_label = None

# Breast side
Label(root_pop_up, text='Latéralité :').grid(row=row_item + 5, column=1, sticky=E)
scrolling_menu_breast = ttk.Combobox(root_pop_up, values=possible_breast_sides, width=17, state='readonly')
scrolling_menu_breast.grid(row=row_item + 5, column=2, sticky=W, padx=10)

onclick_continue_function = lambda: get_entry(root_pop_up, scrolling_menu_examinations, scrolling_menu_ct_curves,
                                              ct_curves_names_times,
                                              scrolling_menu_machines, entry_fractions, entry_dose,
                                              scrolling_menu_breast, scrolling_menu_ptv)
Button(root_pop_up, text='Continuer', command=onclick_continue_function).grid(row=11, column=2, sticky=W, pady=4)
root_pop_up.bind('<Return>', lambda event: onclick_continue_function())
root_pop_up.bind('<Escape>', lambda event: sys.exit())
mainloop()
checks_quit_script()

# Sets CT curve
if selected_examination.EquipmentInfo.ImagingSystemReference is None:
    selected_examination.EquipmentInfo.SetImagingSystemReference(ImagingSystemName=selected_ct_curve)
elif selected_examination.EquipmentInfo.ImagingSystemReference.ImagingSystemName != selected_ct_curve:
    selected_examination.EquipmentInfo.SetImagingSystemReference(ImagingSystemName=selected_ct_curve)

# Creates plan

# Gets plan name (= CT selected date); anonymized patients have no date-time
date_time = selected_examination.GetExaminationDateTime()
plan_name = "Pas de date CT" if not date_time else str(date_time).split(' ')[0]

# If a plan already exists with the expected name, prompts the user to create a plan with a new name
# Otherwise creates plan
existing_plans = case.TreatmentPlans
existing_plans_names = [plan.Name for plan in existing_plans]
if plan_name in existing_plans_names:
    create_new_plan = False
    quit_script = True


    def toggle_create_new_plan(root):
        global create_new_plan, quit_script
        create_new_plan = True
        quit_script = False
        root.destroy()


    root_pop_up = Tk()
    root_pop_up.title("Avertissement")
    Label(root_pop_up, text=f'Le plan intitulé {plan_name} existe déjà.').grid(row=1, column=1, sticky=E)
    onclick_continue_function = lambda: toggle_create_new_plan(root_pop_up)
    Button(root_pop_up, text='Créer un nouveau plan', command=onclick_continue_function).grid(
        row=11, column=4, sticky=W, pady=4)
    Button(root_pop_up, text='Arrêter le script', command=sys.exit).grid(row=11, column=1, sticky=W, pady=4)
    root_pop_up.bind('<Return>', lambda event: onclick_continue_function())
    root_pop_up.bind('<Escape>', lambda event: sys.exit())
    mainloop()
    checks_quit_script()

    if create_new_plan:
        def get_entry(master, entry, existing_plans_names, label_object):
            entry_value = entry.get()
            if entry_value != '':
                if entry_value in existing_plans_names:
                    label_object['text'] = f'Le nom {entry_value} existe déjà.\n' + label_object['text']
                    return
                global plan_name, quit_script
                plan_name = entry_value
                quit_script = False
                master.destroy()


        root_pop_up = Tk()
        root_pop_up.title('')
        label = Label(root_pop_up, text='Précisez le nom du nouveau plan :')
        label.grid(row=1, column=1)
        entry = Entry(root_pop_up)
        entry.grid(row=2, column=1)
        onclick_continue_function = lambda: get_entry(root_pop_up, entry, existing_plans_names, label)
        Button(root_pop_up, text='Arrêter le script', command=sys.exit).grid(row=11, column=1, sticky=W, pady=4)
        Button(root_pop_up, text='Valider', command=onclick_continue_function).grid(row=11, column=15, sticky=W, pady=4)
        root_pop_up.bind('<Return>', lambda event: onclick_continue_function())
        root_pop_up.bind('<Escape>', lambda event: sys.exit())
        mainloop()
        checks_quit_script()

# Creates plan
assert plan_name not in existing_plans_names, 'Plan name already exists, should not happen'
plan = case.AddNewPlan(PlanName=plan_name, PlannedBy=r"", Comment=r"", ExaminationName=selected_examination.Name,
                       IsMedicalOncologyPlan=False, AllowDuplicateNames=False)

# Creates beam set with parameters chosen by user
if selected_breast_side == 'Sein droit':
    beam_set_name = r"Sein D"
else:
    beam_set_name = r"Sein G"

if selected_examination.PatientPosition == "HFS":
    patient_position = "HeadFirstSupine"
else:
    patient_position = "FeetFirstSupine"
beam_set = plan.AddNewBeamSet(Name=beam_set_name, ExaminationName=selected_examination.Name,
                              MachineName=selected_machine, Modality="Photons", TreatmentTechnique="SMLC",
                              PatientPosition=patient_position, NumberOfFractions=n_fractions,
                              CreateSetupBeams=True, UseLocalizationPointAsSetupIsocenter=False,
                              Comment=r"", EnableDynamicTrackingForVero=False, NewDoseSpecificationPointNames=[],
                              NewDoseSpecificationPoints=[])

beam_set.AddRoiPrescriptionDoseReference(RoiName=selected_ptv_name, PrescriptionType='MedianDose',
                                         DoseValue=dose_value * 100.,  # DoseValue is in cGy, put back to Gy
                                         RelativePrescriptionLevel=1.0)

# Loads plan created
patient.Save()
plan.SetCurrent()

# Adjustment of dose grid so that potential skin PTV is still contained in it => addition of 2 cm on right/left depending
# on breast side and 4 cm in anterior (+10 voxels in left-right direction and +20 voxels in anterior)
beam_set.SetDefaultDoseGrid(VoxelSize={'x': 0.2, 'y': 0.2, 'z': 0.2})
beam_set.FractionDose.UpdateDoseGridStructures()
dose_grid = plan.GetTotalDoseGrid()
assert selected_breast_side in possible_breast_sides
dose_grid_corner_x = dose_grid.Corner.x
if selected_breast_side == 'Sein droit':
    dose_grid_corner_x = dose_grid.Corner.x - 2
dose_grid_nr_voxels_x = dose_grid.NrVoxels.x + 10
dose_grid_corner_y = dose_grid.Corner.y - 4
dose_grid_nr_voxels_y = dose_grid.NrVoxels.y + 20
beam_set.UpdateDoseGrid(Corner={'x': dose_grid_corner_x, 'y': dose_grid_corner_y, 'z': dose_grid.Corner.z},
                        VoxelSize={'x': 0.2, 'y': 0.2, 'z': 0.2},
                        NumberOfVoxels={'x': dose_grid_nr_voxels_x, 'y': dose_grid_nr_voxels_y,
                                        'z': dose_grid.NrVoxels.z})

# Loads examination chosen - test to resolve RS issue with loading CT images
# plan_infos = case.QueryPlanInfo(Filter={'Name': plan.Name})
# patient_infos = patient_db.QueryPatientInfo(Filter={'PatientID': patient.PatientID})
# examination_infos = patient_db.QueryExaminationInfo(PatientInfo=patient_infos[0],
#                                                    Filter={'Name': selected_examination.Name})
# case.LoadExamination(ExaminationInfo=examination_infos[0])

# Creates localization point
structure_set = case.PatientModel.StructureSets[selected_examination.Name]
roi_geometries = structure_set.RoiGeometries
poi_geometries = structure_set.PoiGeometries
localization_point = [localization_point for localization_point in poi_geometries
                      if localization_point.OfPoi.Type == "LocalizationPoint"]
assert len([external_roi for external_roi in roi_geometries if external_roi.OfRoi.Name == 'External']) == 1, \
    "No external contour found or more than one external contour found, should not happen."
external_roi_center = structure_set.RoiGeometries['External'].GetCenterOfRoi()
if len(localization_point) == 0:
    case.PatientModel.CreatePoi(Examination=selected_examination,
                                Point={'x': external_roi_center.x, 'y': external_roi_center.y,
                                       'z': external_roi_center.z}, Name=r"Point_billes",
                                Color="Yellow", VisualizationDiameter=1, Type="LocalizationPoint")

else:
    assert len(localization_point) == 1, "More than one localization points found with the name point_billes, " \
                                         "possible confusion on which to select."
    external_roi_bounding_box = structure_set.RoiGeometries['External'].GetBoundingBox()
    external_roi_extreme_x_1 = external_roi_bounding_box[0].x
    external_roi_extreme_x_2 = external_roi_bounding_box[1].x
    actual_localization_point_coordinates = localization_point[0].Point
    # If localization point coordinates incoherent (e.g. outside of the external ROI + margin 1000cm) => sets new ones
    # Happens if localization point is not defined on CT but exists anyway
    if not external_roi_extreme_x_1 - 1000 <= actual_localization_point_coordinates.x <= external_roi_extreme_x_2 + 1000:
        localization_point[0].Point = {'x': external_roi_center.x,
                                       'y': external_roi_center.y,
                                       'z': external_roi_center.z}

# Creates couch
assert selected_machine is not None
if selected_machine.lower() == "novalis":
    couch_name_1 = 'CouchSurface'
    couch_name_2 = 'CouchInterior'
    template_name = 'COUCH Brainlab extra'
    source_examination_name = 'CT 1'
else:
    couch_name_1 = 'Couch_VERSA_650_Interior'
    couch_name_2 = 'Couch_VERSA_650_Surface'
    template_name = 'COUCH_650_VERSA'
    source_examination_name = 'CT'
couch_1 = [roi for roi in roi_geometries if roi.OfRoi.Name == couch_name_1]
couch_2 = [roi for roi in roi_geometries if roi.OfRoi.Name == couch_name_2]
assert (len(couch_1) == 0 or len(
    couch_1) == 1), 'More than one ROI with the name ' + couch_name_1 + ', should not happen.'
assert (len(couch_2) == 0 or len(
    couch_2) == 1), 'More than one ROI with the name ' + couch_name_2 + ', should not happen.'

if len(couch_1) == 0 and len(couch_2) == 0:
    template = patient_db.LoadTemplatePatientModel(templateName=template_name)
    case.PatientModel.CreateStructuresFromTemplate(SourceTemplate=template,
                                                   SourceExaminationName=source_examination_name,
                                                   SourceRoiNames=[couch_name_1, couch_name_2],
                                                   SourcePoiNames=[], AssociateStructuresByName=False,
                                                   TargetExamination=selected_examination,
                                                   InitializationOption="AlignImageCenters")
elif not (couch_1[0].HasContours() and couch_2[0].HasContours()):
    template = patient_db.LoadTemplatePatientModel(templateName=template_name)
    case.PatientModel.CreateStructuresFromTemplate(SourceTemplate=template,
                                                   SourceExaminationName=source_examination_name,
                                                   SourceRoiNames=[couch_name_1, couch_name_2],
                                                   SourcePoiNames=[], AssociateStructuresByName=True,
                                                   TargetExamination=selected_examination,
                                                   InitializationOption="AlignImageCenters")

await_user_input('Placez le point bille et ajustez la table.')

# Creates ring
ring_name = create_ring(patient, case, selected_examination, selected_ptv_name, roi_geometries)

# Creates beams
# Get isocenter coordinates
ptv_center = structure_set.RoiGeometries[selected_ptv_name].GetCenterOfRoi()
iso_position = {'x': ptv_center.x, 'y': ptv_center.y, 'z': ptv_center.z}
iso_data = beam_set.CreateDefaultIsocenterData(Position=iso_position)
assert selected_breast_side == 'Sein droit' or selected_breast_side == 'Sein gauche', "No selected breast side."
if selected_breast_side == 'Sein droit':
    gantry_angle_1 = 60
    gantry_angle_2 = 234
else:
    gantry_angle_1 = 308
    gantry_angle_2 = 133
beam_1 = beam_set.CreatePhotonBeam(BeamQualityId=r"6", IsocenterData=iso_data, Name=r"10",
                                   Description=r"TGI", GantryAngle=gantry_angle_1, CouchRotationAngle=0,
                                   CouchPitchAngle=0, CouchRollAngle=0, CollimatorAngle=0)
beam_1.SetBolus(BolusName=r"")
beam_set.Beams['10'].BeamMU = 0

beam_2 = beam_set.CreatePhotonBeam(BeamQualityId=r"6", IsocenterData=iso_data, Name=r"11",
                                   Description=r"TGE", GantryAngle=gantry_angle_2, CouchRotationAngle=0,
                                   CouchPitchAngle=0, CouchRollAngle=0, CollimatorAngle=0)
beam_2.SetBolus(BolusName=r"")
beam_set.Beams['11'].BeamMU = 0
beam_set.Beams['10'].Isocenter.EditIsocenter(Name="Isocentre " + beam_set_name)
# Prompts user to adjust beams angle
await_user_input('Placez l\'isocentre et ajustez les angles des faisceaux tangentiels.')

# Adjusts modulation parameters (specific to rIMRT)
plan_optimization = plan.PlanOptimizations[0]
plan_optimization_parameters = plan_optimization.OptimizationParameters
plan_optimization_parameters.DoseCalculation.IterationsInPreparationsPhase = 5
algorithm_parameters = plan_optimization_parameters.Algorithm
algorithm_parameters.MaxNumberOfIterations = 5  # first optimization done with only 5 iterations (used for beam positioning)
tss = plan_optimization_parameters.TreatmentSetupSettings[0]
tss.SegmentConversion.MaxNumberOfSegments = 10
tss.SegmentConversion.MinSegmentArea = 9
tss.SegmentConversion.MinSegmentMUPerFraction = 5
tss.SegmentConversion.MinNumberOfOpenLeafPairs = 5
tss.SegmentConversion.MinLeafEndSeparation = 2

# Creates optimisation functions
min_dose_function = plan_optimization.AddOptimizationFunction(
    FunctionType="MinDose", RoiName=selected_ptv_name, IsConstraint=False, RestrictAllBeamsIndividually=False,
    RestrictToBeam=None, IsRobust=False, RestrictToBeamSet=None, UseRbeDose=False)
plan_optimization.Objective.ConstituentFunctions[0].DoseFunctionParameters.DoseLevel = round((dose_value - 0.1),
                                                                                             1) * 100
plan_optimization.Objective.ConstituentFunctions[0].DoseFunctionParameters.Weight = 100


max_dose_function = plan_optimization.AddOptimizationFunction(
    FunctionType="MaxDose", RoiName=selected_ptv_name, IsConstraint=False, RestrictAllBeamsIndividually=False,
    RestrictToBeam=None, IsRobust=False, RestrictToBeamSet=None, UseRbeDose=False)
plan_optimization.Objective.ConstituentFunctions[1].DoseFunctionParameters.DoseLevel = round((dose_value + 0.1),
                                                                                             1) * 100
plan_optimization.Objective.ConstituentFunctions[1].DoseFunctionParameters.Weight = 100

uniform_dose_function = plan_optimization.AddOptimizationFunction(
    FunctionType="UniformDose", RoiName=selected_ptv_name, IsConstraint=False, RestrictAllBeamsIndividually=False,
    RestrictToBeam=None, IsRobust=False, RestrictToBeamSet=None, UseRbeDose=False)
plan_optimization.Objective.ConstituentFunctions[2].DoseFunctionParameters.DoseLevel = dose_value * 100
plan_optimization.Objective.ConstituentFunctions[2].DoseFunctionParameters.Weight = 100

uniform_dose_function_robust = plan_optimization.AddOptimizationFunction(
    FunctionType="UniformDose", RoiName=selected_ptv_name, IsConstraint=False, RestrictAllBeamsIndividually=False,
    RestrictToBeam=None, IsRobust=True, RestrictToBeamSet=None, UseRbeDose=False)
plan_optimization.Objective.ConstituentFunctions[3].DoseFunctionParameters.DoseLevel = dose_value * 100
plan_optimization.Objective.ConstituentFunctions[3].DoseFunctionParameters.Weight = 100

maxDVH_ring_function = plan_optimization.AddOptimizationFunction(
    FunctionType="MaxDvh", RoiName=ring_name, IsConstraint=False, RestrictAllBeamsIndividually=False,
    RestrictToBeam=None, IsRobust=False, RestrictToBeamSet=None, UseRbeDose=False)
plan_optimization.Objective.ConstituentFunctions[4].DoseFunctionParameters.DoseLevel = round(dose_value * 0.95) * 100
plan_optimization.Objective.ConstituentFunctions[4].DoseFunctionParameters.Weight = 10

maxDVH_lung_ispit_function = plan_optimization.AddOptimizationFunction(
    FunctionType="MaxDvh", RoiName=r"Lung_ipsilat", IsConstraint=False, RestrictAllBeamsIndividually=False,
    RestrictToBeam=None, IsRobust=False, RestrictToBeamSet=None, UseRbeDose=False)
plan_optimization.Objective.ConstituentFunctions[5].DoseFunctionParameters.DoseLevel = round(dose_value * 0.125) * 100
plan_optimization.Objective.ConstituentFunctions[5].DoseFunctionParameters.PercentVolume = 25
plan_optimization.Objective.ConstituentFunctions[5].DoseFunctionParameters.Weight = 10

maxEUD_heart_function = plan_optimization.AddOptimizationFunction(
    FunctionType="MaxEud", RoiName=r"Heart", IsConstraint=False, RestrictAllBeamsIndividually=False,
    RestrictToBeam=None, IsRobust=False, RestrictToBeamSet=None, UseRbeDose=False)
plan_optimization.Objective.ConstituentFunctions[6].DoseFunctionParameters.DoseLevel = round(dose_value * 0.05) * 100

# Adjusts Robust parameters
if selected_breast_side == 'Sein droit':
    plan_optimization_parameters.SaveRobustnessParameters(PositionUncertaintyAnterior=1,
                                                          PositionUncertaintyPosterior=0,
                                                          PositionUncertaintySuperior=0,
                                                          PositionUncertaintyInferior=0,
                                                          PositionUncertaintyLeft=0,
                                                          PositionUncertaintyRight=1,
                                                          DensityUncertainty=0,
                                                          PositionUncertaintySetting="Universal",
                                                          IndependentLeftRight=True,
                                                          IndependentAnteriorPosterior=True,
                                                          IndependentSuperiorInferior=True,
                                                          ComputeExactScenarioDoses=False,
                                                          NamesOfNonPlanningExaminations=[])
else:
    plan_optimization_parameters.SaveRobustnessParameters(PositionUncertaintyAnterior=1,
                                                          PositionUncertaintyPosterior=0,
                                                          PositionUncertaintySuperior=0,
                                                          PositionUncertaintyInferior=0,
                                                          PositionUncertaintyLeft=1,
                                                          PositionUncertaintyRight=0,
                                                          DensityUncertainty=0,
                                                          PositionUncertaintySetting="Universal",
                                                          IndependentLeftRight=True,
                                                          IndependentAnteriorPosterior=True,
                                                          IndependentSuperiorInferior=True,
                                                          ComputeExactScenarioDoses=False,
                                                          NamesOfNonPlanningExaminations=[])

plan_optimization.RunOptimization()

await_user_input('Ré-ajustez l\'isocentre et les faisceaux.')
plan_optimization_parameters.DoseCalculation.IterationsInPreparationsPhase = 10
algorithm_parameters.MaxNumberOfIterations = 40
plan.PlanOptimizations[0].ResetOptimization()
#  Run 2 optimisations
print("Running optimisation...")
plan_optimization.RunOptimization()
plan_optimization.RunOptimization()
beam_set.SetAutoScaleToPrimaryPrescription(AutoScale=True)
# Load clinical goals template associated to input dose
dose_value = float(dose_value)
if (dose_value, n_fractions) in dose_fractions_value_template_matching:
    clinical_goals_template = patient_db.LoadTemplateClinicalGoals(
        templateName=dose_fractions_value_template_matching[(dose_value, n_fractions)])
    plan.TreatmentCourse.EvaluationSetup.ApplyClinicalGoalTemplate(Template=clinical_goals_template)
patient.Save()
