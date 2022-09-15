from connect import *
import math
import sys
import subprocess
import tkinter.messagebox
from tkinter import *

#################################################
#
# Script pour la dosi in vivo
#
# 1/ Création des points selon la nomenclature : DIV + Nom du faisceau + Description (colonnes NAME et DESCRIPTION dans Raystation)
# ex: DIV 10TGI pour NAME = 10 et DESCRIPTION = TGI
# 2/ Placement des points div manuellement
# On relance le script : Vérification que les points de div existent
# 3/ Calcul du champ carré équivalent (pas de changement par rapport à l'ancien script)
# 4/ Mesure de la dose aux points DIV et affichage de la dose et du champ carré équivalent : Name + Description : ex 10TGI
# 5/ Cerise sur le gâteau, le résultats est déjà copié dans le presse-papier de Windows, il ne reste plus qu'à le coller dans Mosaiq.
#
# Version 1.0 : Création du script
# Version 1.1 : Correction d'un bug dans la numératotation des beams
# Version 1.2 : Ajustement du script afin qu'il fonctionne pour les plans en rIMRT par CM.
# Version 1.2.1 : On enlève l'argument volume de la fonction CreatePOI() car il n'existe plus dans la version 10B.
##################################################

Patient = get_current("Patient")
machine_db = get_current("MachineDB")
beam_set = get_current("BeamSet")
ui = get_current('ui')
case = get_current('Case')
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


phrase = ""

flag = True
poi_list = [poi.Name for poi in case.PatientModel.PointsOfInterest]

for beam in beam_set.Beams:
    poi_name = f"DIV {str(beam.Name).strip()}{str(beam.Description).strip()}"

    if poi_name not in poi_list:
        flag = False

if flag == False:
    div_phrase = ""
    for beam in beam_set.Beams:
        poi_name = f"DIV {str(beam.Name).strip()}{str(beam.Description).strip()}"
        div_phrase += poi_name + ", "
        if poi_name not in [str(poi.Name) for poi in case.PatientModel.PointsOfInterest]:
            case.PatientModel.CreatePoi(Examination=examination, Point=beam.Isocenter.Position, Name=poi_name,
                                        Color="Yellow", VisualizationDiameter=1, Type="Undefined")
            case.PatientModel.ToggleExcludeFromExport(ExcludeFromExport=True, RegionOfInterests=[],
                                                      PointsOfInterests=[poi_name])
    Patient.Save()
    tkinter.messagebox.showinfo("Information", "Placer les points de DIV : " + div_phrase[:-2])
    sys.exit()


# les doses par beam sont une liste et non un dictionnaire. Il sont indexés dans l'ordre de création des beams et non dans l'ordre des beams
# on crée un dictionnaire pour faire correspondre le nom du beam à son index de dose
dict_beam_name_i = {(str(b.ForBeam.Name) + str(b.ForBeam.Description)): i for i, b in
                    enumerate(beam_set.FractionDose.ForBeamSet.FractionDose.BeamDoses)}
# print(dict_beam_name_i)

for beam in beam_set.Beams:
    poi_name = f"DIV {str(beam.Name).strip()}{str(beam.Description).strip()}"
    machine = machine_db.GetTreatmentMachine(machineName=beam.MachineReference.MachineName, lockMode=None)
    mlc_physics = machine.Physics.MlcPhysics
    n_leaf_pairs = mlc_physics.UpperLayer.NumOfLeafPairs
    # print("----------------")

    phrase += "----------------" + "\n"

    equivalent_square = 0
    for segment_index, segment in enumerate(beam.Segments):

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

        # print("dictionnaire : ",beam.Name+beam.Description)
        # print("dict : ",dict_beam_name_i[beam.Name+beam.Description])
        frame_OR = beam_set.FractionDose.BeamDoses[
            dict_beam_name_i[beam.Name + beam.Description]].InDoseGrid.FrameOfReference;
        point_coord = case.PatientModel.StructureSets[examination.Name].PoiGeometries[poi_name].Point;
        dose_at_point = beam_set.FractionDose.BeamDoses[
            dict_beam_name_i[beam.Name + beam.Description]].InterpolateDoseInPoint(Point=point_coord,
                                                                                   PointFrameOfReference=frame_OR);
        dose = round(dose_at_point / 100, 3)
        # Ajout CM version 1.2 : le carré équivalent correspond à la moyenne pondérée par le nombre d'UMs du carré
        # équivalent de chaque segment :
        equivalent_square += round(4 * exposed_area / exposed_circumference * segment.RelativeWeight, 2)

    phrase += f"Dose au point DIV {beam.Name}{beam.Description} : {dose} Gy" + "\n"
    phrase += f"equivalent square: {equivalent_square} cm" + "\n"

print(phrase)
subprocess.Popen(['clip'], stdin=subprocess.PIPE).communicate(phrase.encode())
