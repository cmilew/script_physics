from connect import *
import sys

#############################################
##### SCRIPT SENO - ETAPE 2 : PHYSICIEN #####
#############################################

################################################################
# Version 1 : Création
# Version 1.1 : Si la structure existe déjà, on supprime la géométrie plutôt que la ROI. Ceci permet de prendre en compte les reprises de traitement.
# Version 1.2 : Correction du bug et gestion des structures * RING OUT si jamais elles existent
# Version 1.3 : Modification de certaines couleurs de ROI et passage en booleen
# Version 1.4 : Correction d'un bug : le script plantait depuis le passage en booleen si on voulait l'executer alors que les structure existaient déjà. Ceci est désormais corrigé car on ne recrée plus les booleens, on les relance seulement.
# Version 1.5 : Création du volume RING PTV TOT - PTVp_tumourbed_TOT à la place des 2 volumes RING PTV TOT - PTVp_tumourbed_R et RING PTV TOT - PTVp_tumourbed_L
# Version 1.6 : Modification du type de HumHead_PRV en enlevant "Undefined" et en mettant "Organ"
# Version 1.7 : Ajout de la vérification si la ROI External - PTV TOT a une expression avant de faire l'update de la géométrie (sinon bug)
################################################################


VersionScript = "1.5"


def test_intersec(case, examination, roi1, roi2):
    newroi = case.PatientModel.CreateRoi(Name="temp_roi", Color="White", Type="Undefined", TissueName=None,
                                         RbeCellTypeName=None, RoiMaterial=None)
    ExpressionA = {'Operation': "Union", 'SourceRoiNames': [roi1.OfRoi.Name],
                   'MarginSettings': {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                      'Right': 0, 'Left': 0}}
    ExpressionB = {'Operation': "Union", 'SourceRoiNames': [roi2.OfRoi.Name],
                   'MarginSettings': {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                      'Right': 0, 'Left': 0}}
    ResultOperation = "Intersection"
    ResultMarginSettings = {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0,
                            'Left': 0}

    newroi.CreateAlgebraGeometry(Examination=examination, Algorithm="Auto", ExpressionA=ExpressionA,
                                 ExpressionB=ExpressionB, ResultOperation=ResultOperation,
                                 ResultMarginSettings=ResultMarginSettings)
    if case.PatientModel.StructureSets[examination.Name].RoiGeometries["temp_roi"].HasContours():
        abs_vol = case.PatientModel.StructureSets[examination.Name].RoiGeometries["temp_roi"].GetRoiVolume()
        rel_vol = abs_vol / min(
            case.PatientModel.StructureSets[examination.Name].RoiGeometries[roi1.OfRoi.Name].GetRoiVolume(),
            case.PatientModel.StructureSets[examination.Name].RoiGeometries[roi2.OfRoi.Name].GetRoiVolume()) * 100
        newroi.DeleteRoi()
        return (round(abs_vol, 2), round(rel_vol, 1))
    else:
        newroi.DeleteRoi()
        return (0, 0)


def get_roi_list_name(roi_list):
    roi_name_list = []
    for roi in roi_list:
        roi_name_list.append(roi.Name)
    return roi_name_list


def create_z_ROI(Case, exam, roi, color, marge=""):
    roi_list = get_roi_list_name(Case.PatientModel.RegionsOfInterest)
    if marge == "":
        marge = 0.2
        marge_txt = ""
    else:
        marge = float(marge)
        marge_txt = "-" + str(marge) + "cm"
    if "z_" + roi + marge_txt not in roi_list:
        Case.PatientModel.CreateRoi(Name="z_" + roi + marge_txt, Color=color, Type="Undefined", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': [roi],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["PTV TOT"],
                       'MarginSettings': {'Type': "Expand", 'Superior': marge, 'Inferior': marge, 'Anterior': marge,
                                          'Posterior': marge, 'Right': marge, 'Left': marge}}
        ResultOperation = "Subtraction"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["z_" + roi + marge_txt].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                         ExpressionB=ExpressionB,
                                                                                         ResultOperation=ResultOperation,
                                                                                         ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["z_" + roi + marge_txt].UpdateDerivedGeometry(
        Examination=Case.Examinations[exam], Algorithm="Auto")

    return True


Patient = get_current("Patient")
Case = get_current("Case")
exam = get_current("Examination").Name

"""
if not Case.PatientModel.StructureSets[exam].RoiGeometries["PTV TOT"].HasContours():
    Case.PatientModel.RegionsOfInterest["PTV TOT"].UpdateDerivedGeometry(Examination=Case.Examinations[exam], Algorithm="Auto")
"""
# On éxécute le booléen du PTV TOT pour forcer la mise à jour en cas de mapping de déformation
Case.PatientModel.RegionsOfInterest["PTV TOT"].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                     Algorithm="Auto")

roi_list = get_roi_list_name(Case.PatientModel.RegionsOfInterest)

structures_a_creer = ["RING PTVp_tumourbed out_L", "RING PTVp_tumourbed out_R", "RING PTVp_tumourbed out",
                      "RING PTV TOT out", "Cylindre_L=26cmR=25cm", "HorsFOV (EVIT)", "ChambreChimio",
                      "ChambreChimio+3mm (EVIT)", "RING PTV TOT out", "RING PTV TOT", "zc out", "zc",
                      "External - PTV TOT", "RING PTVp_tumourbed", "RING PTVp_tumourbed out",
                      "RING PTVp_tumourbed out_L", "RING PTVp_tumourbed out_R", "RING PTV TOT - PTVp_tumourbed",
                      "RING PTV TOT - PTVp_tumourbed_TOT", "RING PTVp_tumourbed_R", "RING PTV TOT - PTVp_tumourbed_R",
                      "RING PTVp_tumourbed_L", "RING PTV TOT - PTVp_tumourbed_L", "Spinal_cord+1cm", "HumHead_PRV",
                      "HumHead_L_PRV", "HumHead_R_PRV", "z_Heart", "z_Heart-1.5cm", "z_Thyroid", "z_Lung_ipsilat",
                      "z_Lung_ipsilat-1.5cm", "z_Lungs", "z_Lung_R", "z_Lung_R-1.5cm", "z_Lung_L", "z_Lung_L-1.5cm",
                      "breast-tbed", "PTVp_breast-(tbed+4mm)", "PTVp_tumourbed+2mm", "PTVp_breast-tbed",
                      "breast-tbed_L", "PTVp_breast-(tbed+4mm)_L", "PTVp_tumourbed+2mm_L", "PTVp_breast-tbed_L",
                      "breast-tbed_R", "PTVp_breast-(tbed+4mm)_R", "PTVp_tumourbed+2mm_R", "PTVp_breast-tbed_R"]

for roi in structures_a_creer:
    if roi in roi_list:
        Case.PatientModel.StructureSets[exam].RoiGeometries[roi].DeleteGeometry()
        # Case.PatientModel.RegionsOfInterest[roi].DeleteRoi()

if "HorsFOV (EVIT)" not in roi_list:
    Case.PatientModel.CreateRoi(Name="HorsFOV (EVIT)", Color="255,255,0", Type="Undefined", TissueName=None,
                                RbeCellTypeName=None, RoiMaterial=None)

if "ChambreChimio" not in roi_list:
    Case.PatientModel.CreateRoi(Name="ChambreChimio", Color="255,165,0", Type="Undefined", TissueName=None,
                                RbeCellTypeName=None, RoiMaterial=None)

if "ChambreChimio+3mm (EVIT)" not in roi_list:
    Case.PatientModel.CreateRoi(Name="ChambreChimio+3mm (EVIT)", Color="0,0,255", Type="Undefined", TissueName=None,
                                RbeCellTypeName=None, RoiMaterial=None)
    ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["ChambreChimio"],
                   'MarginSettings': {'Type': "Expand", 'Superior': 0.3, 'Inferior': 0.3, 'Anterior': 0.3,
                                      'Posterior': 0.3, 'Right': 0.3, 'Left': 0.3}}
    ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["External"],
                   'MarginSettings': {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                      'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
    ResultOperation = "Intersection"
    ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                            'Right': 0.0, 'Left': 0.0}
    Case.PatientModel.RegionsOfInterest["ChambreChimio+3mm (EVIT)"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                         ExpressionB=ExpressionB,
                                                                                         ResultOperation=ResultOperation,
                                                                                         ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["ChambreChimio+3mm (EVIT)"].UpdateDerivedGeometry(
        Examination=Case.Examinations[exam], Algorithm="Auto")

if "CTVp_tumourbed" or "GTVp_tumour" or "CTVp_tumour" in roi_list:
    if not Case.PatientModel.StructureSets[exam].RoiGeometries["CTVp_tumourbed"].HasContours():
        Case.PatientModel.RegionsOfInterest["CTVp_tumourbed"].DeleteRoi()
        Case.PatientModel.RegionsOfInterest["PTVp_tumourbed"].DeleteRoi()
        del roi_list[roi_list.index('CTVp_tumourbed')]
        del roi_list[roi_list.index('PTVp_tumourbed')]
    else:

        if not Case.PatientModel.StructureSets[exam].RoiGeometries["PTVp_tumourbed"].HasContours():
            Case.PatientModel.RegionsOfInterest["PTVp_tumourbed"].UpdateDerivedGeometry(
                Examination=Case.Examinations[exam], Algorithm="Auto")

        # union du CTV sein et du CTV boost si il existe
        if \
                test_intersec(Case, Case.Examinations[exam],
                              Case.PatientModel.StructureSets[exam].RoiGeometries['CTVp_breast'],
                              Case.PatientModel.StructureSets[exam].RoiGeometries["CTVp_tumourbed"])[1] != 100:
            ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["CTVp_tumourbed"],
                           'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                              'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
            ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["CTVp_breast"],
                           'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                              'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
            ResultOperation = "Union"
            ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                    'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}
            Case.PatientModel.RegionsOfInterest["CTVp_breast"].CreateAlgebraGeometry(
                Examination=Case.Examinations[exam], Algorithm="Auto", ExpressionA=ExpressionA, ExpressionB=ExpressionB,
                ResultOperation=ResultOperation, ResultMarginSettings=ResultMarginSettings)

            Case.PatientModel.RegionsOfInterest['PTV TOT'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                                 Algorithm="Auto")

if "CTVp_tumourbed_R" in roi_list:
    if not Case.PatientModel.StructureSets[exam].RoiGeometries["CTVp_tumourbed_R"].HasContours():
        Case.PatientModel.RegionsOfInterest["CTVp_tumourbed_R"].DeleteRoi()
        Case.PatientModel.RegionsOfInterest["PTVp_tumourbed_R"].DeleteRoi()
        del roi_list[roi_list.index('CTVp_tumourbed_R')]
        del roi_list[roi_list.index('PTVp_tumourbed_R')]
    else:

        if not Case.PatientModel.StructureSets[exam].RoiGeometries["PTVp_tumourbed_R"].HasContours():
            Case.PatientModel.RegionsOfInterest["PTVp_tumourbed_R"].UpdateDerivedGeometry(
                Examination=Case.Examinations[exam], Algorithm="Auto")

        # union du CTV sein et du CTV boost si il existe
        if test_intersec(Case, Case.Examinations[exam],
                         Case.PatientModel.StructureSets[exam].RoiGeometries['CTVp_breast_R'],
                         Case.PatientModel.StructureSets[exam].RoiGeometries["CTVp_tumourbed_R"])[1] != 100:
            ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["CTVp_tumourbed_R"],
                           'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                              'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
            ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["CTVp_breast_R"],
                           'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                              'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
            ResultOperation = "Union"
            ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                    'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}
            Case.PatientModel.RegionsOfInterest["CTVp_breast_R"].CreateAlgebraGeometry(
                Examination=Case.Examinations[exam], Algorithm="Auto", ExpressionA=ExpressionA, ExpressionB=ExpressionB,
                ResultOperation=ResultOperation, ResultMarginSettings=ResultMarginSettings)

            Case.PatientModel.RegionsOfInterest['PTV TOT'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                                 Algorithm="Auto")

if "CTVp_tumourbed_L" in roi_list:
    if not Case.PatientModel.StructureSets[exam].RoiGeometries["CTVp_tumourbed_L"].HasContours():
        Case.PatientModel.RegionsOfInterest["CTVp_tumourbed_L"].DeleteRoi()
        Case.PatientModel.RegionsOfInterest["PTVp_tumourbed_L"].DeleteRoi()
        del roi_list[roi_list.index('CTVp_tumourbed_L')]
        del roi_list[roi_list.index('PTVp_tumourbed_L')]
    else:

        if not Case.PatientModel.StructureSets[exam].RoiGeometries["PTVp_tumourbed_L"].HasContours():
            Case.PatientModel.RegionsOfInterest["PTVp_tumourbed_L"].UpdateDerivedGeometry(
                Examination=Case.Examinations[exam], Algorithm="Auto")

        # union du CTV sein et du CTV boost si il existe
        if test_intersec(Case, Case.Examinations[exam],
                         Case.PatientModel.StructureSets[exam].RoiGeometries['CTVp_breast_L'],
                         Case.PatientModel.StructureSets[exam].RoiGeometries["CTVp_tumourbed_L"])[1] != 100:
            ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["CTVp_tumourbed_L"],
                           'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                              'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
            ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["CTVp_breast_L"],
                           'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                              'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
            ResultOperation = "Union"
            ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                    'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}
            Case.PatientModel.RegionsOfInterest["CTVp_breast_L"].CreateAlgebraGeometry(
                Examination=Case.Examinations[exam], Algorithm="Auto", ExpressionA=ExpressionA, ExpressionB=ExpressionB,
                ResultOperation=ResultOperation, ResultMarginSettings=ResultMarginSettings)

            Case.PatientModel.RegionsOfInterest['PTV TOT'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                                 Algorithm="Auto")

if "RING PTV TOT out" not in roi_list:
    Case.PatientModel.CreateRoi(Name="RING PTV TOT out", Color="0,0,0", Type="Undefined", TissueName=None,
                                RbeCellTypeName=None, RoiMaterial=None)
    ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["PTV TOT"],
                   'MarginSettings': {'Type': "Expand", 'Superior': 1.5, 'Inferior': 1.5, 'Anterior': 1.5,
                                      'Posterior': 1.5, 'Right': 1.5, 'Left': 1.5}}
    ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["PTV TOT"],
                   'MarginSettings': {'Type': "Expand", 'Superior': 0.2, 'Inferior': 0.2, 'Anterior': 0.2,
                                      'Posterior': 0.2, 'Right': 0.2, 'Left': 0.2}}
    ResultOperation = "Subtraction"
    ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                            'Right': 0.0, 'Left': 0.0}
    Case.PatientModel.RegionsOfInterest["RING PTV TOT out"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                 ExpressionB=ExpressionB,
                                                                                 ResultOperation=ResultOperation,
                                                                                 ResultMarginSettings=ResultMarginSettings)
Case.PatientModel.RegionsOfInterest["RING PTV TOT out"].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                              Algorithm="Auto")

if "RING PTV TOT" not in roi_list:
    Case.PatientModel.CreateRoi(Name="RING PTV TOT", Color="255,192,203", Type="Undefined", TissueName=None,
                                RbeCellTypeName=None, RoiMaterial=None)
    ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["RING PTV TOT out"],
                   'MarginSettings': {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                      'Right': 0, 'Left': 0}}
    ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["External"],
                   'MarginSettings': {'Type': "Contract", 'Superior': 0.2, 'Inferior': 0.2, 'Anterior': 0.2,
                                      'Posterior': 0.2, 'Right': 0.2, 'Left': 0.2}}
    ResultOperation = "Intersection"
    ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                            'Right': 0.0, 'Left': 0.0}
    Case.PatientModel.RegionsOfInterest["RING PTV TOT"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                             ExpressionB=ExpressionB,
                                                                             ResultOperation=ResultOperation,
                                                                             ResultMarginSettings=ResultMarginSettings)
Case.PatientModel.RegionsOfInterest["RING PTV TOT"].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                          Algorithm="Auto")

if "zc out" not in roi_list:
    Case.PatientModel.CreateRoi(Name="zc out", Color="0,0,0", Type="Undefined", TissueName=None, RbeCellTypeName=None,
                                RoiMaterial=None)
    ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["PTV TOT"],
                   'MarginSettings': {'Type': "Expand", 'Superior': 6.0, 'Inferior': 6.0, 'Anterior': 6.0,
                                      'Posterior': 6.0, 'Right': 6.0, 'Left': 6.0}}
    ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["PTV TOT"],
                   'MarginSettings': {'Type': "Expand", 'Superior': 1.5, 'Inferior': 1.5, 'Anterior': 1.5,
                                      'Posterior': 1.5, 'Right': 1.5, 'Left': 1.5}}
    ResultOperation = "Subtraction"
    ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                            'Right': 0.0, 'Left': 0.0}
    Case.PatientModel.RegionsOfInterest["zc out"].SetAlgebraExpression(ExpressionA=ExpressionA, ExpressionB=ExpressionB,
                                                                       ResultOperation=ResultOperation,
                                                                       ResultMarginSettings=ResultMarginSettings)
Case.PatientModel.RegionsOfInterest["zc out"].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                    Algorithm="Auto")

if "zc" not in roi_list:
    Case.PatientModel.CreateRoi(Name="zc", Color="255,192,203", Type="Undefined", TissueName=None, RbeCellTypeName=None,
                                RoiMaterial=None)
    ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["zc out"],
                   'MarginSettings': {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                      'Right': 0, 'Left': 0}}
    ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["External"],
                   'MarginSettings': {'Type': "Contract", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                      'Right': 0, 'Left': 0}}
    ResultOperation = "Intersection"
    ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                            'Right': 0.0, 'Left': 0.0}
    Case.PatientModel.RegionsOfInterest["zc"].SetAlgebraExpression(ExpressionA=ExpressionA, ExpressionB=ExpressionB,
                                                                   ResultOperation=ResultOperation,
                                                                   ResultMarginSettings=ResultMarginSettings)
Case.PatientModel.RegionsOfInterest["zc"].UpdateDerivedGeometry(Examination=Case.Examinations[exam], Algorithm="Auto")

if "External - PTV TOT" not in roi_list:
    Case.PatientModel.CreateRoi(Name="External - PTV TOT", Color="255,255,128", Type="Undefined", TissueName=None,
                                RbeCellTypeName=None, RoiMaterial=None)
    ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["External"],
                   'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                      'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
    ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["PTV TOT"],
                   'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                      'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
    ResultOperation = "Subtraction"
    ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                            'Right': 0.0, 'Left': 0.0}
    Case.PatientModel.RegionsOfInterest["External - PTV TOT"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                   ExpressionB=ExpressionB,
                                                                                   ResultOperation=ResultOperation,
                                                                                   ResultMarginSettings=ResultMarginSettings)

# if ROI "External - PTV TOT" exists but don't have expression
elif not Case.PatientModel.RegionsOfInterest["External - PTV TOT"].DerivedRoiExpression:
    Case.PatientModel.RegionsOfInterest['External - PTV TOT'].SetAlgebraExpression(
        ExpressionA={'Operation': "Union", 'SourceRoiNames': ["External"],
                     'MarginSettings': {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                        'Right': 0, 'Left': 0}},
        ExpressionB={'Operation': "Union", 'SourceRoiNames': ["PTV TOT"],
                     'MarginSettings': {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                        'Right': 0, 'Left': 0}}, ResultOperation="Subtraction",
        ResultMarginSettings={'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0,
                              'Left': 0})
Case.PatientModel.RegionsOfInterest["External - PTV TOT"].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                                Algorithm="Auto")

if "CTVp_tumourbed" or "GTVp_tumour" or "CTVp_tumour" in roi_list:
    if "PTVp_tumourbed" in roi_list:
        boost_name = "PTVp_tumourbed"
        boost_abbrev_name = "tbed"
    else:
        boost_name = "PTVp_tumour"
        boost_abbrev_name = "tumour"

    boost_ring_out_name = "RING " + boost_name + " out"
    if boost_ring_out_name not in roi_list:
        Case.PatientModel.CreateRoi(Name=boost_ring_out_name, Color="0,0,0", Type="Undefined", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': [boost_name],
                       'MarginSettings': {'Type': "Expand", 'Superior': 1.5, 'Inferior': 1.5, 'Anterior': 1.5,
                                          'Posterior': 1.5, 'Right': 1.5, 'Left': 1.5}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': [boost_name],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.2, 'Inferior': 0.2, 'Anterior': 0.2,
                                          'Posterior': 0.2, 'Right': 0.2, 'Left': 0.2}}
        ResultOperation = "Subtraction"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest[boost_ring_out_name].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                            ExpressionB=ExpressionB,
                                                                                            ResultOperation=ResultOperation,
                                                                                            ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest[boost_ring_out_name].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                                   Algorithm="Auto")

    boost_ring_name = "RING " + boost_name
    if boost_ring_name not in roi_list:
        Case.PatientModel.CreateRoi(Name=boost_ring_name, Color="255,255,0", Type="Undefined", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': [boost_ring_out_name],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                          'Right': 0, 'Left': 0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["External"],
                       'MarginSettings': {'Type': "Contract", 'Superior': 0.2, 'Inferior': 0.2, 'Anterior': 0.2,
                                          'Posterior': 0.2, 'Right': 0.2, 'Left': 0.2}}
        ResultOperation = "Intersection"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest[boost_ring_name].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                        ExpressionB=ExpressionB,
                                                                                        ResultOperation=ResultOperation,
                                                                                        ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest[boost_ring_name].UpdateDerivedGeometry(
        Examination=Case.Examinations[exam], Algorithm="Auto")

    ring_minus_boost_name = "RING PTV TOT - " + boost_name
    if ring_minus_boost_name not in roi_list:
        Case.PatientModel.CreateRoi(Name=ring_minus_boost_name, Color="255,128,0", Type="Undefined",
                                    TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["RING PTV TOT"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': [boost_ring_name],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ResultOperation = "Subtraction"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest[ring_minus_boost_name].SetAlgebraExpression(
            ExpressionA=ExpressionA, ExpressionB=ExpressionB, ResultOperation=ResultOperation,
            ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest[ring_minus_boost_name].UpdateDerivedGeometry(
        Examination=Case.Examinations[exam], Algorithm="Auto")

    name_ptv_minus_boost_4mm = "PTVp_breast-(" + boost_abbrev_name + "+4mm)"
    if name_ptv_minus_boost_4mm not in roi_list:
        Case.PatientModel.CreateRoi(Name=name_ptv_minus_boost_4mm, Color="0,255,255", Type="PTV", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["PTVp_breast"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': [boost_name],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.4, 'Inferior': 0.4, 'Anterior': 0.4,
                                          'Posterior': 0.4, 'Right': 0.4, 'Left': 0.4}}
        ResultOperation = "Subtraction"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest[name_ptv_minus_boost_4mm].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                           ExpressionB=ExpressionB,
                                                                                           ResultOperation=ResultOperation,
                                                                                           ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest[name_ptv_minus_boost_4mm].UpdateDerivedGeometry(
        Examination=Case.Examinations[exam], Algorithm="Auto")

    name_boost_2mm = boost_name + "+2mm"
    if name_boost_2mm not in roi_list:
        Case.PatientModel.CreateRoi(Name=name_boost_2mm, Color="0,128,64", Type="PTV", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': [boost_name],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.2, 'Inferior': 0.2, 'Anterior': 0.2,
                                          'Posterior': 0.2, 'Right': 0.2, 'Left': 0.2}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': [],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ResultOperation = "None"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest[name_boost_2mm].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                       ExpressionB=ExpressionB,
                                                                                       ResultOperation=ResultOperation,
                                                                                       ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest[name_boost_2mm].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                                    Algorithm="Auto")

    ptv_minus_boost_name = "PTVp_breast-" + boost_abbrev_name
    if ptv_minus_boost_name not in roi_list:
        Case.PatientModel.CreateRoi(Name=ptv_minus_boost_name, Color="255,165,0", Type="PTV", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["PTVp_breast"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': [boost_name],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ResultOperation = "Subtraction"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest[ptv_minus_boost_name].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                     ExpressionB=ExpressionB,
                                                                                     ResultOperation=ResultOperation,
                                                                                     ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest[ptv_minus_boost_name].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                                  Algorithm="Auto")

if "CTVp_tumourbed_L" in roi_list:
    if "RING PTVp_tumourbed out_L" not in roi_list:
        Case.PatientModel.CreateRoi(Name="RING PTVp_tumourbed out_L", Color="0,0,0", Type="Undefined", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["PTVp_tumourbed_L"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 1.5, 'Inferior': 1.5, 'Anterior': 1.5,
                                          'Posterior': 1.5, 'Right': 1.5, 'Left': 1.5}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["PTVp_tumourbed_L"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.2, 'Inferior': 0.2, 'Anterior': 0.2,
                                          'Posterior': 0.2, 'Right': 0.2, 'Left': 0.2}}
        ResultOperation = "Subtraction"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["RING PTVp_tumourbed out_L"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                              ExpressionB=ExpressionB,
                                                                                              ResultOperation=ResultOperation,
                                                                                              ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["RING PTVp_tumourbed out_L"].UpdateDerivedGeometry(
        Examination=Case.Examinations[exam], Algorithm="Auto")

    if "RING PTVp_tumourbed_L" not in roi_list:
        Case.PatientModel.CreateRoi(Name="RING PTVp_tumourbed_L", Color="0,128,0", Type="Undefined", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["RING PTVp_tumourbed out_L"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                          'Right': 0, 'Left': 0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["External"],
                       'MarginSettings': {'Type': "Contract", 'Superior': 0.2, 'Inferior': 0.2, 'Anterior': 0.2,
                                          'Posterior': 0.2, 'Right': 0.2, 'Left': 0.2}}
        ResultOperation = "Intersection"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["RING PTVp_tumourbed_L"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                          ExpressionB=ExpressionB,
                                                                                          ResultOperation=ResultOperation,
                                                                                          ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["RING PTVp_tumourbed_L"].UpdateDerivedGeometry(
        Examination=Case.Examinations[exam], Algorithm="Auto")

    # Case.PatientModel.RegionsOfInterest["RING PTVp_tumourbed out_L"].DeleteRoi()

    if "PTVp_breast-(tbed+4mm)_L" not in roi_list:
        Case.PatientModel.CreateRoi(Name="PTVp_breast-(tbed+4mm)_L", Color="0,255,255", Type="PTV", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["PTVp_breast_L"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["PTVp_tumourbed_L"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.4, 'Inferior': 0.4, 'Anterior': 0.4,
                                          'Posterior': 0.4, 'Right': 0.4, 'Left': 0.4}}
        ResultOperation = "Subtraction"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["PTVp_breast-(tbed+4mm)_L"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                             ExpressionB=ExpressionB,
                                                                                             ResultOperation=ResultOperation,
                                                                                             ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["PTVp_breast-(tbed+4mm)_L"].UpdateDerivedGeometry(
        Examination=Case.Examinations[exam], Algorithm="Auto")

    if "PTVp_tumourbed+2mm_L" not in roi_list:
        Case.PatientModel.CreateRoi(Name="PTVp_tumourbed+2mm_L", Color="0,128,64", Type="PTV", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["PTVp_tumourbed_L"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.2, 'Inferior': 0.2, 'Anterior': 0.2,
                                          'Posterior': 0.2, 'Right': 0.2, 'Left': 0.2}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': [],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ResultOperation = "None"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["PTVp_tumourbed+2mm_L"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                         ExpressionB=ExpressionB,
                                                                                         ResultOperation=ResultOperation,
                                                                                         ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["PTVp_tumourbed+2mm_L"].UpdateDerivedGeometry(
        Examination=Case.Examinations[exam], Algorithm="Auto")

    if "PTVp_breast-tbed_L" not in roi_list:
        Case.PatientModel.CreateRoi(Name="PTVp_breast-tbed_L", Color="128,64,0", Type="PTV", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["PTVp_breast_L"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["PTVp_tumourbed_L"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ResultOperation = "Subtraction"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["PTVp_breast-tbed_L"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                       ExpressionB=ExpressionB,
                                                                                       ResultOperation=ResultOperation,
                                                                                       ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["PTVp_breast-tbed_L"].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                                    Algorithm="Auto")

if "CTVp_tumourbed_R" in roi_list:
    if "RING PTVp_tumourbed out_R" not in roi_list:
        Case.PatientModel.CreateRoi(Name="RING PTVp_tumourbed out_R", Color="0,0,0", Type="Undefined", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["PTVp_tumourbed_R"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 1.5, 'Inferior': 1.5, 'Anterior': 1.5,
                                          'Posterior': 1.5, 'Right': 1.5, 'Left': 1.5}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["PTVp_tumourbed_R"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.2, 'Inferior': 0.2, 'Anterior': 0.2,
                                          'Posterior': 0.2, 'Right': 0.2, 'Left': 0.2}}
        ResultOperation = "Subtraction"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["RING PTVp_tumourbed out_R"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                              ExpressionB=ExpressionB,
                                                                                              ResultOperation=ResultOperation,
                                                                                              ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["RING PTVp_tumourbed out_R"].UpdateDerivedGeometry(
        Examination=Case.Examinations[exam], Algorithm="Auto")

    if "RING PTVp_tumourbed_R" not in roi_list:
        Case.PatientModel.CreateRoi(Name="RING PTVp_tumourbed_R", Color="0,128,0", Type="Undefined", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["RING PTVp_tumourbed out_R"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                          'Right': 0, 'Left': 0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["External"],
                       'MarginSettings': {'Type': "Contract", 'Superior': 0.2, 'Inferior': 0.2, 'Anterior': 0.2,
                                          'Posterior': 0.2, 'Right': 0.2, 'Left': 0.2}}
        ResultOperation = "Intersection"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["RING PTVp_tumourbed_R"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                          ExpressionB=ExpressionB,
                                                                                          ResultOperation=ResultOperation,
                                                                                          ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["RING PTVp_tumourbed_R"].UpdateDerivedGeometry(
        Examination=Case.Examinations[exam], Algorithm="Auto")

    # Case.PatientModel.RegionsOfInterest["RING PTVp_tumourbed out_R"].DeleteRoi()

    if "PTVp_breast-(tbed+4mm)_R" not in roi_list:
        Case.PatientModel.CreateRoi(Name="PTVp_breast-(tbed+4mm)_R", Color="0,255,255", Type="PTV", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["PTVp_breast_R"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["PTVp_tumourbed_R"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.4, 'Inferior': 0.4, 'Anterior': 0.4,
                                          'Posterior': 0.4, 'Right': 0.4, 'Left': 0.4}}
        ResultOperation = "Subtraction"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["PTVp_breast-(tbed+4mm)_R"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                             ExpressionB=ExpressionB,
                                                                                             ResultOperation=ResultOperation,
                                                                                             ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["PTVp_breast-(tbed+4mm)_R"].UpdateDerivedGeometry(
        Examination=Case.Examinations[exam], Algorithm="Auto")

    if "PTVp_tumourbed+2mm_R" not in roi_list:
        Case.PatientModel.CreateRoi(Name="PTVp_tumourbed+2mm_R", Color="0,128,64", Type="PTV", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["PTVp_tumourbed_R"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.2, 'Inferior': 0.2, 'Anterior': 0.2,
                                          'Posterior': 0.2, 'Right': 0.2, 'Left': 0.2}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': [],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ResultOperation = "None"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["PTVp_tumourbed+2mm_R"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                         ExpressionB=ExpressionB,
                                                                                         ResultOperation=ResultOperation,
                                                                                         ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["PTVp_tumourbed+2mm_R"].UpdateDerivedGeometry(
        Examination=Case.Examinations[exam], Algorithm="Auto")

    if "PTVp_breast-tbed_R" not in roi_list:
        Case.PatientModel.CreateRoi(Name="PTVp_breast-tbed_R", Color="255,128,64", Type="PTV", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["PTVp_breast_R"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["PTVp_tumourbed_R"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ResultOperation = "Subtraction"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["PTVp_breast-tbed_R"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                       ExpressionB=ExpressionB,
                                                                                       ResultOperation=ResultOperation,
                                                                                       ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["PTVp_breast-tbed_R"].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                                    Algorithm="Auto")

if "CTVp_tumourbed_R" and "CTVp_tumourbed_L" in roi_list:
    if "RING PTV TOT - PTVp_tumourbed_TOT" not in roi_list:
        Case.PatientModel.CreateRoi(Name="RING PTV TOT - PTVp_tumourbed_TOT", Color="139,69,19", Type="Undefined",
                                    TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["RING PTV TOT"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["RING PTVp_tumourbed_L", "RING PTVp_tumourbed_R"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ResultOperation = "Subtraction"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["RING PTV TOT - PTVp_tumourbed_TOT"].SetAlgebraExpression(
            ExpressionA=ExpressionA, ExpressionB=ExpressionB, ResultOperation=ResultOperation,
            ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["RING PTV TOT - PTVp_tumourbed_TOT"].UpdateDerivedGeometry(
        Examination=Case.Examinations[exam], Algorithm="Auto")


elif "CTVp_tumourbed_R" in roi_list:
    if "RING PTV TOT - PTVp_tumourbed_R" not in roi_list:
        Case.PatientModel.CreateRoi(Name="RING PTV TOT - PTVp_tumourbed_R", Color="139,69,19", Type="Undefined",
                                    TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["RING PTV TOT"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["RING PTVp_tumourbed_R"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ResultOperation = "Subtraction"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["RING PTV TOT - PTVp_tumourbed_R"].SetAlgebraExpression(
            ExpressionA=ExpressionA, ExpressionB=ExpressionB, ResultOperation=ResultOperation,
            ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["RING PTV TOT - PTVp_tumourbed_R"].UpdateDerivedGeometry(
        Examination=Case.Examinations[exam], Algorithm="Auto")

elif "CTVp_tumourbed_L" in roi_list:
    if "RING PTV TOT - PTVp_tumourbed_L" not in roi_list:
        Case.PatientModel.CreateRoi(Name="RING PTV TOT - PTVp_tumourbed_L", Color="139,69,19", Type="Undefined",
                                    TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["RING PTV TOT"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': ["RING PTVp_tumourbed_L"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                          'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}}
        ResultOperation = "Subtraction"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["RING PTV TOT - PTVp_tumourbed_L"].SetAlgebraExpression(
            ExpressionA=ExpressionA, ExpressionB=ExpressionB, ResultOperation=ResultOperation,
            ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["RING PTV TOT - PTVp_tumourbed_L"].UpdateDerivedGeometry(
        Examination=Case.Examinations[exam], Algorithm="Auto")

if "Spinal_cord" in roi_list:
    if "Spinal_cord+1cm" not in roi_list:
        Case.PatientModel.CreateRoi(Name="Spinal_cord+1cm", Color="128,64,0", Type="Undefined", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["Spinal_cord"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 1.0,
                                          'Posterior': 1.0, 'Right': 1.0, 'Left': 1.0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': [],
                       'MarginSettings': {'Type': "Contract", 'Superior': 0, 'Inferior': 0, 'Anterior': 0,
                                          'Posterior': 0, 'Right': 0, 'Left': 0}}
        ResultOperation = "None"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["Spinal_cord+1cm"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                    ExpressionB=ExpressionB,
                                                                                    ResultOperation=ResultOperation,
                                                                                    ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["Spinal_cord+1cm"].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                                 Algorithm="Auto")

if "HumeralHead" in roi_list:
    if "HumHead_PRV" not in roi_list:
        Case.PatientModel.CreateRoi(Name="HumHead_PRV", Color="0,0,255", Type="Organ", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["HumeralHead"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 1.0, 'Inferior': 1.0, 'Anterior': 1.0,
                                          'Posterior': 1.0, 'Right': 1.0, 'Left': 1.0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': [],
                       'MarginSettings': {'Type': "Contract", 'Superior': 0, 'Inferior': 0, 'Anterior': 0,
                                          'Posterior': 0, 'Right': 0, 'Left': 0}}
        ResultOperation = "None"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["HumHead_PRV"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                ExpressionB=ExpressionB,
                                                                                ResultOperation=ResultOperation,
                                                                                ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["HumHead_PRV"].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                             Algorithm="Auto")

if "HumeralHead_L" in roi_list:
    if "HumHead_L_PRV" not in roi_list:
        Case.PatientModel.CreateRoi(Name="HumHead_L_PRV", Color="255,0,255", Type="Undefined", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["HumeralHead_L"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 1.0, 'Inferior': 1.0, 'Anterior': 1.0,
                                          'Posterior': 1.0, 'Right': 1.0, 'Left': 1.0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': [],
                       'MarginSettings': {'Type': "Contract", 'Superior': 0, 'Inferior': 0, 'Anterior': 0,
                                          'Posterior': 0, 'Right': 0, 'Left': 0}}
        ResultOperation = "None"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["HumHead_L_PRV"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                  ExpressionB=ExpressionB,
                                                                                  ResultOperation=ResultOperation,
                                                                                  ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["HumHead_L_PRV"].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                               Algorithm="Auto")

if "HumeralHead_R" in roi_list:
    if "HumHead_R_PRV" not in roi_list:
        Case.PatientModel.CreateRoi(Name="HumHead_R_PRV", Color="255,192,203", Type="Undefined", TissueName=None,
                                    RbeCellTypeName=None, RoiMaterial=None)
        ExpressionA = {'Operation': "Union", 'SourceRoiNames': ["HumeralHead_R"],
                       'MarginSettings': {'Type': "Expand", 'Superior': 1.0, 'Inferior': 1.0, 'Anterior': 1.0,
                                          'Posterior': 1.0, 'Right': 1.0, 'Left': 1.0}}
        ExpressionB = {'Operation': "Union", 'SourceRoiNames': [],
                       'MarginSettings': {'Type': "Contract", 'Superior': 0, 'Inferior': 0, 'Anterior': 0,
                                          'Posterior': 0, 'Right': 0, 'Left': 0}}
        ResultOperation = "None"
        ResultMarginSettings = {'Type': "Contract", 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                                'Right': 0.0, 'Left': 0.0}
        Case.PatientModel.RegionsOfInterest["HumHead_R_PRV"].SetAlgebraExpression(ExpressionA=ExpressionA,
                                                                                  ExpressionB=ExpressionB,
                                                                                  ResultOperation=ResultOperation,
                                                                                  ResultMarginSettings=ResultMarginSettings)
    Case.PatientModel.RegionsOfInterest["HumHead_R_PRV"].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                               Algorithm="Auto")

if "Heart" in roi_list:
    create_z_ROI(Case, exam, "Heart", "255,0,128")
if "Thyroid" in roi_list:
    create_z_ROI(Case, exam, "Thyroid", "170,0,255")
if "Lung_ipsilat" in roi_list:
    create_z_ROI(Case, exam, "Lung_ipsilat", "0,128,255")
# if "Lung_R" in roi_list:
#    create_z_ROI(Case,exam,"Lung_R","0,128,255")
# if "Lung_L" in roi_list:
#    create_z_ROI(Case,exam,"Lung_L","0,128,255")
if ("Lung_R" in roi_list) or ("Lung_L" in roi_list):
    create_z_ROI(Case, exam, "Lungs", "0,128,255")

center_roi_ptv_tot = Case.PatientModel.StructureSets[exam].RoiGeometries['PTV TOT'].GetCenterOfRoi()
print(center_roi_ptv_tot)
print(Case.Examinations[exam].Series[0].ImageStack.Corner)
print(Case.Examinations[exam].Series[0].ImageStack.SliceDirection)

coord_z = []
for pos in Case.Examinations[exam].Series[0].ImageStack.SlicePositions:
    # print("z : ",float(Case.Examinations[exam].Series[0].ImageStack.Corner['z']))
    # print("pos : ", float(pos))
    coord_z.append(float(Case.Examinations[exam].Series[0].ImageStack.Corner['z']) + float(pos))

coord_z_cor = []
for pos in coord_z:
    coord_z_cor.append(abs(pos - float(center_roi_ptv_tot['z'])))

print(coord_z_cor.index(min(coord_z_cor)) + 1)
print(float(Case.Examinations[exam].Series[0].ImageStack.SlicePositions[coord_z_cor.index(min(coord_z_cor))]) + float(
    Case.Examinations[exam].Series[0].ImageStack.Corner['z']))
slice_iso_z = float(
    Case.Examinations[exam].Series[0].ImageStack.SlicePositions[coord_z_cor.index(min(coord_z_cor))]) + float(
    Case.Examinations[exam].Series[0].ImageStack.Corner['z'])

slice_ext = []
Case.PatientModel.StructureSets[exam].RoiGeometries['External'].SetRepresentation(Representation='Contours')

print("slice_iso_z: ", round(float(slice_iso_z), 1))
for i, slice in enumerate(Case.PatientModel.StructureSets[exam].RoiGeometries['External'].PrimaryShape.Contours):
    # print(round((slice[0]['z']),1))
    if round(float(slice_iso_z), 1) == round(float(slice[0]['z']), 1):
        slice_ext.append(i)

if not slice_ext:
    print("erreur")
    sys.exit()
else:
    print("slice_ext : ", slice_ext)

max_len = 0
slice_travail = 0

for slice in slice_ext:
    if len(Case.PatientModel.StructureSets[exam].RoiGeometries['External'].PrimaryShape.Contours[slice]) > max_len:
        max_len = len(Case.PatientModel.StructureSets[exam].RoiGeometries['External'].PrimaryShape.Contours[slice])
        slice_travail = slice

print(slice_travail, max_len)
x = []
y = []
for coord in Case.PatientModel.StructureSets[exam].RoiGeometries['External'].PrimaryShape.Contours[slice_travail]:
    x.append(coord['x'])
    y.append(coord['y'])
moy_x = (min(x) + max(x)) / 2
moy_y = (min(y) + max(y)) / 2

print([point.Name for point in Case.PatientModel.PointsOfInterest])
if 'isocenter' in [point.Name for point in Case.PatientModel.PointsOfInterest]:
    Case.PatientModel.StructureSets[exam].PoiGeometries['isocenter'].Point = {'x': moy_x, 'y': moy_y, 'z': slice_iso_z}
else:
    Case.PatientModel.CreatePoi(Examination=Case.Examinations[exam], Point={'x': moy_x, 'y': moy_y, 'z': slice_iso_z},
                                Name=r"isocenter", Color="Yellow", VisualizationDiameter=1, Type="Isocenter")

# if 'Cylindre_L=26cmR=25cm' in [roi.Name for roi in Case.PatientModel.RegionsOfInterest]:
#    Case.PatientModel.RegionsOfInterest['Cylindre_L=26cmR=25cm'].DeleteRoi()
if "Cylindre_L=26cmR=25cm" not in roi_list:
    Case.PatientModel.CreateRoi(Name=r"Cylindre_L=26cmR=25cm", Color="Magenta", Type="Undefined", TissueName=None,
                                RbeCellTypeName=None, RoiMaterial=None)
Case.PatientModel.RegionsOfInterest['Cylindre_L=26cmR=25cm'].CreateCylinderGeometry(Radius=25,
                                                                                    Axis={'x': 0, 'y': 0, 'z': 1},
                                                                                    Length=26,
                                                                                    Examination=Case.Examinations[exam],
                                                                                    Center=
                                                                                    Case.PatientModel.StructureSets[
                                                                                        exam].PoiGeometries[
                                                                                        'isocenter'].Point,
                                                                                    Representation="Voxels",
                                                                                    VoxelSize=None)

print(min(x), max(x))
print(min(y), max(y))

Patient.Save()
