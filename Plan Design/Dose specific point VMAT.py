from connect import *
from math import *
from tkinter import *

# -*- coding: utf-8 -*-

# ---------------------------------------------------------------
#			Dose Specification Point - VMAT
# ----------------------------------------------------------------
#
# Création :
# Date inconnue - M. Edouard
#
# Modication :
# 11/06/2020 - A. Alexis
#			  *Correction lorsque plusieurs beam sets existants.
#			  *Ne générait le DSP que du 1er beam set.
# 30/07/2020 - A. Alexis - V2.0 - RS9B
#			  *Refonte du code qui était basé sur le beam_set.Number unique au moment de la création du beam set
#			   pour atteindre les distributions de dose, ce qui pouvait amener à des erreurs de création de BDSP dans
#			   les mauvais beam set.
# 12/04/2021 - M. Candice - V3.0 RS9B
#              *Modification du code de manière à ce que le dose specification point soit sur le pixel de contour (de la
#              ROI créée à partir de l'isodose 100%) le plus proche possible de l'isocentre.
#              Ceci est utile pour que  le point envoyé sur RadCalc (double calcul nécessaire pour technique rIMRT) ait
#              plus de chance de se trouver à un endroit où le calcul sera valide.
#
# ----------------------------------------------------------------

try:
    patient = get_current('Patient')
    case = get_current('Case')
    plan = get_current('Plan')
    examination = get_current('Examination')
except:
    print('there is no plan/Beamset')
    exit()

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


patient.Save()
# Nombre de beam sets existants dans le plan
number_of_beamset = plan.BeamSets.Count
# Nombre de distributions de dose existantes (= nombre de beam sets ici)
number_of_dose_ref = plan.TreatmentCourse.TotalDose.WeightedDoseReferences.Count

# Création des BDSP pour chaque Beam Set
for i in range(number_of_beamset):
    beam_set = plan.BeamSets[i]
    beam_set.SetCurrent()
    # Nom du beam set
    beam_set_name = plan.BeamSets[i].DicomPlanLabel
    # Dose prescrite pour ce beam set
    Dose_prescrite = beam_set.Prescription.PrimaryPrescriptionDoseReference.DoseValue

    for k in range(number_of_dose_ref):
        if beam_set_name == plan.TreatmentCourse.TotalDose.WeightedDoseReferences[k].DoseDistribution.ForBeamSet.DicomPlanLabel:
            # Nombre de fractions à délivrer pour le beam seat
            weight = plan.TreatmentCourse.TotalDose.WeightedDoseReferences[k].Weight
            # Distribution de dose associé au beam set (matrice de dose)
            plan_dose = plan.TreatmentCourse.TotalDose.WeightedDoseReferences[k].DoseDistribution
            break

    # Création de la ROI basée sur l'isodose de prescription
    threshold_level = Dose_prescrite / weight
    roi_name = 'Control1_' + str(Dose_prescrite)
    roi = case.PatientModel.CreateRoi(Name=roi_name, Color='Blue', Type='Control')
    roi.CreateRoiGeometryFromDose(DoseDistribution=plan_dose, ThresholdLevel=threshold_level)

    # Coordonnées de l'isocentre
    position_isocenter = plan.BeamSets[beam_set_name].Beams[0].Isocenter.Position
    x_isocenter = position_isocenter.x  # droite gauche
    y_isocenter = position_isocenter.y  # antérieur postérieur
    z_isocenter = position_isocenter.z  # tête pied
    # Matrice  3D contenant les coordonnées des pixels de contours de la ROI créée à partir de l'isodose de presc
    isodose_contours = case.PatientModel.StructureSets[examination.Name].RoiGeometries[roi_name].PrimaryShape.Contours

    # Recherche du/des contour(s) de de la coupe la plus proche de l'isocentre en T/P dans cette matrice 3D
    # Il peut y avoir plusieurs contours sur une même coupe
    min_dist_to_isocenter_slice = None
    for slice in range(len(isodose_contours)):
        dist_to_isocenter_slice = abs(isodose_contours[slice][0].z - z_isocenter)
        if min_dist_to_isocenter_slice is None or dist_to_isocenter_slice < min_dist_to_isocenter_slice:
            min_dist_to_isocenter_slice = dist_to_isocenter_slice
            isocenter_slices = [slice]
        elif dist_to_isocenter_slice == min_dist_to_isocenter_slice:
            isocenter_slices.append(slice)

    min_dist_to_isocenter = None
    coord_dose_spec_point_x, coord_dose_spec_point_y = None, None
    # On parcourt tous les contours de la ROI présent sur la coupe la plus proche de l'iso
    for slice in isocenter_slices:
        current_isodose_contour = isodose_contours[slice]
        # On parcout tous les pixels de chacun de ses contours et on cherche le plus proche de l'iso en x y
        for pixel in range(len(current_isodose_contour)):
            current_isodose_pixel = current_isodose_contour[pixel]
            dist_to_isocenter = sqrt((x_isocenter - current_isodose_pixel.x) ** 2 +
                           (y_isocenter - current_isodose_pixel.y) ** 2)
            if min_dist_to_isocenter is None or dist_to_isocenter < min_dist_to_isocenter:
                min_dist_to_isocenter = dist_to_isocenter
                coord_dose_spec_point_x = current_isodose_pixel.x
                coord_dose_spec_point_y = current_isodose_pixel.y

    # Création du BDSP
    Nom = beam_set.Prescription.PrimaryPrescriptionDoseReference.OnStructure.Name
    Name_DSP = 'Point_' + Nom + '_BDSP'
    beam_set.CreateDoseSpecificationPoint(Name=Name_DSP,
                                          Coordinates={'x': coord_dose_spec_point_x,
                                                       'y': coord_dose_spec_point_y,
                                                       'z': current_isodose_contour[0].z},
                                          VisualizationDiameter=1)

    # _Sélection du BDSP nouvellement crée dans l'onglet BDSP dans PLan Design
    for beam in beam_set.Beams:
        beam_set.Beams[beam.Name].SetDoseSpecificationPoint(Name=Name_DSP)
    case.PatientModel.RegionsOfInterest[roi_name].DeleteRoi()
    patient.Save()