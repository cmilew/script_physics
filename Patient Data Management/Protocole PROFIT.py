from connect import *
import tkinter.ttk as ttk
from tkinter import *

case = get_current('Case')
patient_model = case.PatientModel
patient = get_current("Patient")
machine_db = get_current("MachineDB")
patient_db = get_current("PatientDB")

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
          .EquipmentInfo.ImagingSystemReference.ImagingSystemName + " seront effacées.").grid(row=1, column=1,
                                                                                              sticky=E, padx=10, pady=5)
    Button(top_master, text='Choisir une autre courbe CT', command=modify_ct_curve).grid(row=11, column=1, sticky=W,
                                                                                         pady=4, padx=10)
    Button(top_master, text='Continuer le script', command=continue_script).grid(row=11, column=18, sticky=W, pady=4,
                                                                                 padx=10)
    top_master.wait_window()


def get_entry(master, scrolling_menu_examinations, scrolling_menu_ct_curves, scrolling_menu_ct_curves_values,
              scrolling_menu_machines, scrolling_menu_ctv, scrolling_menu_ptv):
    """ Function aiming to retrieve the information the user provided for the plan creation
        :param master: tkinter window object
        :param scrolling_menu_examinations: list of available CT
        :param scrolling_menu_ct_curves: list of available CT curves
        :param scrolling_menu_machines: list of available machines
        :param scrolling_menu_ctv: a scrolling menu if there are multiple ctv for the selected CT or None
        :param scrolling_menu_ptv: a scrolling menu if there are multiple ptv for the selected CT or None
    """
    entry_ct = scrolling_menu_examinations.get() if scrolling_menu_examinations is not None else None
    entry_ct_curves_value = scrolling_menu_ct_curves.get()
    entry_machine_value = scrolling_menu_machines.get()
    entry_ctv = scrolling_menu_ctv.get() if scrolling_menu_ctv is not None else None
    entry_ptv = scrolling_menu_ptv.get() if scrolling_menu_ptv is not None else None
    if (entry_ct is not None and entry_ct == '') or entry_ct_curves_value == '' or entry_machine_value == '' or \
            (scrolling_menu_ctv is not None and entry_ctv == '') or (scrolling_menu_ptv is not None and
                                                                     entry_ptv == ''):
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
    global selected_ct_value, selected_ct_curve, selected_machine, selected_ctv_name, selected_ptv_name, quit_script
    if scrolling_menu_examinations is not None:
        selected_ct_value = entry_ct
    selected_ct_curve = entry_ct_curve_name
    selected_machine = entry_machine_value
    if scrolling_menu_ctv is not None:
        selected_ctv_name = entry_ctv
    if scrolling_menu_ptv is not None:
        selected_ptv_name = entry_ptv
    quit_script = False
    master.destroy()


def process_selected_ct(scrolling_menu_examinations, all_examinations, case, row_item_combobox_ctv,
                        row_item_combobox_ptv):
    """Function aiming to check if several CTVs and PTVs are associated with the selected CT.
    If there are, creates a menu with the possible CTVs and PTVs asking for plan information."""
    global scrolling_menu_ctv, scrolling_menu_ptv, optional_ctv_label, optional_ptv_label, selected_ctv_name, \
        selected_ptv_name, selected_examination
    if scrolling_menu_examinations is not None:
        entry_value = scrolling_menu_examinations.get()
        selected_ctv_name = None
        selected_ptv_name = None
        if entry_value == '':
            if scrolling_menu_ctv is not None and scrolling_menu_ptv is not None:
                scrolling_menu_ctv.destroy()
                scrolling_menu_ctv = None
                optional_ctv_label.grid_forget()
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

    # Seek number of CTVs and PTVs in selected CT
    roi_geometries = case.PatientModel.StructureSets[selected_examination.Name].RoiGeometries
    ctv_names = [roi.OfRoi.Name for roi in roi_geometries if roi.OfRoi.Type.lower() == 'ctv' and roi.HasContours()]
    ptv_names = [roi.OfRoi.Name for roi in roi_geometries if roi.OfRoi.Type.lower() == 'ptv' and roi.HasContours()]
    if len(ptv_names) == 1:
        if scrolling_menu_ptv is not None:
            scrolling_menu_ptv.destroy()
            scrolling_menu_ptv = None
            optional_ptv_label.grid_forget()
        selected_ptv_name = ptv_names[0]
    else:
        optional_ptv_label.grid(row=row_item_combobox_ptv, column=1, sticky=E)
        scrolling_menu_ptv = ttk.Combobox(root_pop_up, values=sorted(ptv_names), width=17, state='readonly')
        scrolling_menu_ptv.grid(row=row_item_combobox_ptv, column=2, sticky=W, padx=10)

    if len(ctv_names) == 1:
        if scrolling_menu_ctv is not None:
            scrolling_menu_ctv.destroy()
            scrolling_menu_ctv = None
            optional_ctv_label.grid_forget()
        selected_ctv_name = ctv_names[0]
    else:
        # Create a menu with possible CTVs and PTVs names
        optional_ctv_label.grid(row=row_item_combobox_ctv, column=1, sticky=E)
        scrolling_menu_ctv = ttk.Combobox(root_pop_up, values=sorted(ctv_names), width=17, state='readonly')
        scrolling_menu_ctv.grid(row=row_item_combobox_ctv, column=2, sticky=W, padx=10)


def creates_optimization_function(plan_optimization, roi_name, type, dose_level, percent_volume, weight,
                                  roi_list_names):
    """Function aiming to create an optimization function for a designated ROI with provided parameters.
    If the ROI does not exist/has no contour or multiple version of this ROI exists, the function is not created."""
    roi_name_rs = [roi for roi in roi_list_names if roi.lower() == roi_name.lower()]
    if len(roi_name_rs) == 1:
        print_label = 'Creating optimization function for ROI ' + roi_name_rs[0]
        print(print_label)
        function = plan_optimization.AddOptimizationFunction(FunctionType=type, RoiName=roi_name_rs[0],
                                                             IsConstraint=False, RestrictAllBeamsIndividually=False,
                                                             RestrictToBeam=None, IsRobust=False,RestrictToBeamSet=None,
                                                             UseRbeDose=False)
        dose_function_parameters = function.DoseFunctionParameters
        if roi_name.lower() != 'external':
            dose_function_parameters.DoseLevel = dose_level
            dose_function_parameters.PercentVolume = percent_volume
        else:
            dose_function_parameters.HighDoseLevel = dose_level
            dose_function_parameters.LowDoseLevel = 2000
            dose_function_parameters.LowDoseDistance = 4
        dose_function_parameters.Weight = weight

quit_script = True

# Variables to be assigned by the user
selected_ct_value = None
selected_ct_curve = None
selected_machine = None
selected_ctv_name = None
selected_ptv_name = None
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

# Pop up asking all the information needed to create the plan
root_pop_up = Tk()
root_pop_up.title("Paramètres du plan")
row_item = 1

scrolling_menu_examinations = None
# If selected CT has multiple CTVs and PTVs, creates a menu with possible CTVs and PTVs names
optional_ctv_label = Label(root_pop_up, text='CTV :')
scrolling_menu_ctv = None
optional_ptv_label = Label(root_pop_up, text='PTV :')
scrolling_menu_ptv = None
if multiple_cts:
    Label(root_pop_up, text="CT :").grid(row=row_item, column=1, sticky=E)
    scrolling_menu_examinations = ttk.Combobox(root_pop_up, values=scrolling_menu_examinations_values, width=50,
                                               state='readonly')
    scrolling_menu_examinations.grid(row=row_item, column=2, sticky=W, padx=10)
    scrolling_menu_examinations.bind("<<ComboboxSelected>>", lambda event: process_selected_ct(
        scrolling_menu_examinations, all_examinations, case, row_item_combobox_ctv=2, row_item_combobox_ptv=3))
else:
    process_selected_ct(None, all_examinations, case, row_item_combobox_ctv=2, row_item_combobox_ptv=3)

row_item += 3
# CT curve
Label(root_pop_up, text="Courbe CT :").grid(row=row_item, column=1, sticky=E, pady=5)
scrolling_menu_ct_curves = ttk.Combobox(root_pop_up, values=ct_curves_names_times, width=50, state='readonly')
scrolling_menu_ct_curves.grid(row=row_item, column=2, sticky=W, padx=10, pady=5)
# Machine
Label(root_pop_up, text="Machine de traitement :").grid(row=row_item + 1, column=1, sticky=E, pady=5)
scrolling_menu_machines = ttk.Combobox(root_pop_up, values=sorted(available_machines_names), width=17, state='readonly')
scrolling_menu_machines.grid(row=row_item + 1, column=2, sticky=W, padx=10, pady=5)


onclick_continue_function = lambda: get_entry(root_pop_up, scrolling_menu_examinations, scrolling_menu_ct_curves,
                                              ct_curves_names_times, scrolling_menu_machines, scrolling_menu_ctv,
                                              scrolling_menu_ptv)
Button(root_pop_up, text='Continuer', command=onclick_continue_function).grid(row=11, column=2, sticky=W, pady=5)
root_pop_up.bind('<Return>', lambda event: onclick_continue_function())
root_pop_up.bind('<Escape>', lambda event: sys.exit())
mainloop()
checks_quit_script()

# Tests if selected CT is a study shadow or if its study instance UID is corrupted
is_study_shadow = False
is_study_instance_uid_corrupted = False

# Study shadow test
try:
    study_shadow_test = selected_examination.GetStoredDicomTagValueForVerification(Group=0x0008, Element=0x0050)
    print(study_shadow_test)
except:
    is_study_shadow = True

# Study instance UID verification
study_instance_uid = str(selected_examination.GetStoredDicomTagValueForVerification(Group=0x0020, Element=0x000D))
print("Study instance UID :", study_instance_uid)
# Gets groups separated by '.'
groups = study_instance_uid.split('.')
# if group starts with 0 and is not '.0.', study instance uid is corrupted
is_study_instance_uid_corrupted = any(group.startswith('0') and group != '0' for group in groups)

# Message to display in pop up
if is_study_shadow and is_study_instance_uid_corrupted:
    message = 'Attention le CT "' + selected_examination.Name + '" est un study shadow ET son study Instance UID du CT est ' \
                                                'corrompu, contactez le physicien de garde (4905).'
elif is_study_shadow and is_study_instance_uid_corrupted == False:
    message = 'Attention, le CT "' + selected_examination.Name + '" est un study shadow, contacter le physicien de garde (4905)'
elif is_study_shadow == False and is_study_instance_uid_corrupted:
    message = 'Attention le Study Instance UID du CT "' + selected_examination.Name + '" est corrompu, contactez le physicien ' \
                                                                      'de garde (4905).'
else:
    message = 'Le CT n\'est pas corrompu, vous pouvez contourer/faire la dosimétrie dessus.'

print(message)


# Sets CT curve
print('Setting CT curve...')
if selected_examination.EquipmentInfo.ImagingSystemReference is None:
    selected_examination.EquipmentInfo.SetImagingSystemReference(ImagingSystemName=selected_ct_curve)
elif selected_examination.EquipmentInfo.ImagingSystemReference.ImagingSystemName != selected_ct_curve:
    selected_examination.EquipmentInfo.SetImagingSystemReference(ImagingSystemName=selected_ct_curve)

# Plan name checks

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
print('Creating plan...')
assert plan_name not in existing_plans_names, 'Plan name already exists, should not happen'
plan = case.AddNewPlan(PlanName=plan_name, PlannedBy=r"", Comment=r"", ExaminationName=selected_examination.Name,
                       IsMedicalOncologyPlan=False, AllowDuplicateNames=False)

# Creates beam set with parameters chosen by user
print('Creating beamset...')
if selected_examination.PatientPosition == "HFS":
    patient_position = "HeadFirstSupine"
else:
    patient_position = "FeetFirstSupine"
beam_set = plan.AddNewBeamSet(Name='PROFIT', ExaminationName=selected_examination.Name,
                              MachineName=selected_machine, Modality="Photons", TreatmentTechnique="VMAT",
                              PatientPosition=patient_position, NumberOfFractions=20,
                              CreateSetupBeams=True, UseLocalizationPointAsSetupIsocenter=False,
                              Comment=r"", EnableDynamicTrackingForVero=False, NewDoseSpecificationPointNames=[],
                              NewDoseSpecificationPoints=[])

beam_set.AddRoiPrescriptionDoseReference(RoiName=selected_ctv_name, PrescriptionType='DoseAtVolume',
                                         DoseValue=6000., DoseVolume=99, RelativePrescriptionLevel=1)

# Loads plan created
patient.Save()
plan.SetCurrent()

# Creates localization point
print('Creating localization point...')
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
print('Creating couch...')
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

# Creates beams
print('Creating beams...')
# Gets isocenter coordinates
ctv_center = structure_set.RoiGeometries[selected_ctv_name].GetCenterOfRoi()
iso_position = {'x': ctv_center.x, 'y': ctv_center.y, 'z': ctv_center.z}
iso_data = beam_set.CreateDefaultIsocenterData(Position=iso_position)
beam_1 = beam_set.CreateArcBeam(ArcStopGantryAngle=181, ArcRotationDirection='CounterClockwise', BeamQualityId=r"6",
                                IsocenterData=iso_data, Name=r"10", Description=r"ARC1", GantryAngle=179,
                                CouchRotationAngle=0, CouchPitchAngle=0, CouchRollAngle=0, CollimatorAngle=15)
beam_2 = beam_set.CreateArcBeam(ArcStopGantryAngle=179, ArcRotationDirection='Clockwise', BeamQualityId=r"6",
                                IsocenterData=iso_data, Name=r"11", Description=r"ARC2", GantryAngle=181,
                                CouchRotationAngle=0, CouchPitchAngle=0, CouchRollAngle=0, CollimatorAngle=345)
beam_3 = beam_set.CreateArcBeam(ArcStopGantryAngle=181, ArcRotationDirection='CounterClockwise', BeamQualityId=r"6",
                                IsocenterData=iso_data, Name=r"12", Description=r"ARC3", GantryAngle=179,
                                CouchRotationAngle=0, CouchPitchAngle=0, CouchRollAngle=0, CollimatorAngle=90)

# Creates ring around PTV if does not already exists and set its algebra expression
print('Creating/updating ring...')
ring_name = 'RING_PTV_1.5cm_0.2cm'
roi_geom_names = [roi.Name for roi in patient_model.RegionsOfInterest]
if ring_name not in roi_geom_names:
    roi_ring = patient_model.CreateRoi(Name=ring_name, Color="Green", Type="Undefined", TissueName=None,
                                       RbeCellTypeName=None, RoiMaterial=None)
roi_ring = patient_model.RegionsOfInterest[ring_name].SetAlgebraExpression(
    ExpressionA={'Operation': "Union", 'SourceRoiNames': [selected_ptv_name],
                 'MarginSettings': {'Type': "Expand", 'Superior': 1.5, 'Inferior': 1.5, 'Anterior': 1.5,
                                    'Posterior': 1.5, 'Right': 1.5, 'Left': 1.5}},
    ExpressionB={'Operation': "Union", 'SourceRoiNames': [selected_ptv_name],
                 'MarginSettings': {'Type': "Expand", 'Superior': 0.2, 'Inferior': 0.2, 'Anterior': 0.2,
                                    'Posterior': 0.2, 'Right': 0.2, 'Left': 0.2}},
    ResultOperation="Subtraction",
    ResultMarginSettings={'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                          'Right': 0, 'Left': 0})

roi_ring.UpdateDerivedGeometry(Examination=selected_examination, Algorithm="Auto")


roi_list = patient_model.StructureSets[selected_examination.Name].RoiGeometries
roi_list_names = [roi.OfRoi.Name for roi in roi_list if roi.HasContours()]

# Creates optimisation functions
plan_optimization = plan.PlanOptimizations[0]
creates_optimization_function(plan_optimization, selected_ctv_name, 'MinDvh', 6000, 99, 100, roi_list_names)
creates_optimization_function(plan_optimization, selected_ptv_name, 'MinDvh', 5700, 99, 100, roi_list_names)
creates_optimization_function(plan_optimization, selected_ptv_name, 'MaxDose', 6300, 0, 100, roi_list_names)
creates_optimization_function(plan_optimization, ring_name, 'MaxDose', 5820, 0, 10, roi_list_names)
creates_optimization_function(plan_optimization, 'external', 'DoseFallOff', 6000, 0, 20, roi_list_names)
creates_optimization_function(plan_optimization, 'rectum', 'MaxDose', 6000, 0, 10, roi_list_names)
creates_optimization_function(plan_optimization, 'vessie', 'MaxDose', 6000, 0, 10, roi_list_names)
creates_optimization_function(plan_optimization, 'tf d', 'MaxDvh', 3000, 2, 10, roi_list_names)
creates_optimization_function(plan_optimization, 'tf g', 'MaxDvh', 3000, 2, 10, roi_list_names)

# Load clinical goals template
print('Loading template...')
profit_template = patient_db.LoadTemplateClinicalGoals(templateName='Prostate - PROFIT', lockMode='Read')
plan.TreatmentCourse.EvaluationSetup.ApplyClinicalGoalTemplate(Template=profit_template)